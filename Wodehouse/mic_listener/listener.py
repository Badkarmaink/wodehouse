#!/usr/bin/env python3
"""
listener.py — Always-on microphone listener with VAD that saves speech clips as WAV.

- Uses WebRTC VAD if available; otherwise falls back to a simple RMS threshold.
- Works in WSL2 when PulseAudio devices are exposed (PULSE_SERVER=unix:/mnt/wslg/PulseServer).
- Writes clips into AUDIO_DIR (env) or /mnt/wodehouse_data/shared/audio by default.

Usage examples:
  # list devices and exit
  python listener.py --list-devices

  # run using auto-picked input device
  AUDIO_DIR=/mnt/wodehouse_data/shared/audio python listener.py

  # or specify device by index or name substring
  AUDIO_DIR=/mnt/wodehouse_data/shared/audio python listener.py --device 2
  AUDIO_DIR=/mnt/wodehouse_data/shared/audio python listener.py --device "Microphone"
"""
import os
import sys
import time
import wave
import queue
import argparse
import numpy as np
import sounddevice as sd

# Try to import WebRTC VAD (optional)
try:
    import webrtcvad
    HAVE_VAD = True
except Exception:
    HAVE_VAD = False

# --- Config / Defaults ---
AUDIO_DIR = os.getenv("AUDIO_DIR", "/mnt/wodehouse_data/shared/audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


def write_wav(path: str, audio: np.ndarray, samplerate: int = 16000) -> None:
    """Write mono 16-bit PCM WAV."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())


def pick_input_device(preferred: str | int | None) -> int:
    """Choose an input-capable device. Accepts index or substring name."""
    devs = sd.query_devices()
    # Specific selection
    if preferred is not None:
        # Numeric index?
        if isinstance(preferred, int) or (isinstance(preferred, str) and preferred.isdigit()):
            idx = int(preferred)
            sd.check_input_settings(device=idx, channels=1)
            return idx
        # Substring match by name
        name = str(preferred).lower()
        for i, d in enumerate(devs):
            if d["max_input_channels"] > 0 and name in d["name"].lower():
                return i
        raise RuntimeError(f"Requested device '{preferred}' not found or not input-capable.")
    # Auto-pick first input device
    for i, d in enumerate(devs):
        if d["max_input_channels"] > 0:
            return i
    raise RuntimeError("No input-capable audio device found.")


def build_vad_fn(samplerate: int, aggressiveness: int):
    """Return a callable is_speech(bytes) -> bool using WebRTC VAD or RMS fallback."""
    if HAVE_VAD:
        vad = webrtcvad.Vad(aggressiveness)
        def is_speech_chunk(b: bytes) -> bool:
            return vad.is_speech(b, samplerate)
        return is_speech_chunk
    else:
        # Simple RMS threshold as a fallback (tunable)
        THRESH = 300.0
        def is_speech_chunk(b: bytes) -> bool:
            arr = np.frombuffer(b, dtype=np.int16)
            if arr.size == 0:
                return False
            return float(np.abs(arr).mean()) > THRESH
        return is_speech_chunk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", help="Input device index or substring of name")
    ap.add_argument("--aggressiveness", type=int, default=2, choices=[0, 1, 2, 3],
                    help="WebRTC VAD sensitivity (0=least, 3=most). Ignored if VAD not installed.")
    ap.add_argument("--silence_ms", type=int, default=1500, help="Stop after this much trailing silence (ms)")
    ap.add_argument("--samplerate", type=int, default=16000, help="Sample rate (Hz)")
    ap.add_argument("--block_ms", type=int, default=30, help="Frame size (ms). VAD prefers 10/20/30ms.")
    ap.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    args = ap.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        print("Default device:", sd.default.device)
        return

    try:
        device = pick_input_device(args.device)
    except Exception as e:
        print(f"❌ Audio device error: {e}")
        print("Tip: run with --list-devices and choose a valid --device index or name.")
        sys.exit(1)

    dev_info = sd.query_devices(device)
    samplerate = int(args.samplerate or dev_info.get("default_samplerate", 16000)) or 16000
    block_ms = int(args.block_ms)
    block_size = int(samplerate * block_ms / 1000)

    is_speech_chunk = build_vad_fn(samplerate, args.aggressiveness)

    q: "queue.Queue[bytes]" = queue.Queue()

    # NOTE: Using RawInputStream; callback receives a CFFI buffer. Convert to bytes.
    def callback(indata, frames, time_info, status):
        if status:
            # Uncomment to debug:
            # print("PortAudio status:", status, file=sys.stderr)
            pass
        q.put(bytes(indata))  # <-- Option A: convert to raw bytes (no .copy())

    print(f"🎤 Using device [{device}]: {dev_info['name']} @ {samplerate} Hz")
    with sd.RawInputStream(samplerate=samplerate,
                           blocksize=block_size,
                           channels=1,
                           dtype="int16",
                           device=device,
                           callback=callback):
        print("🎧 Listening… Ctrl+C to stop.")
        buf = []
        last_voice_ts = None
        recording = False

        try:
            while True:
                b = q.get()  # bytes for one block
                if is_speech_chunk(b):
                    if not recording:
                        recording = True
                        buf = []
                        # print("🎙️  Speech detected… recording")
                    last_voice_ts = time.time()
                if recording:
                    buf.append(np.frombuffer(b, dtype=np.int16))
                    # finalize if enough trailing silence
                    if last_voice_ts and (time.time() - last_voice_ts) * 1000 > args.silence_ms:
                        clip = np.concatenate(buf) if buf else np.array([], dtype=np.int16)
                        ts = time.strftime("%Y%m%d_%H%M%S")
                        path = os.path.join(AUDIO_DIR, f"clip_{ts}.wav")
                        write_wav(path, clip, samplerate)
                        dur = len(clip) / float(samplerate) if samplerate else 0.0
                        print(f"💾 Saved {path} ({dur:.1f}s)")
                        recording = False
                        buf = []
        except KeyboardInterrupt:
            print("\n👋 Bye")


if __name__ == "__main__":
    main()
