#!/usr/bin/env python3
import argparse, json, os
from datetime import datetime
from faster_whisper import WhisperModel
import os
# Silence HF download/progress noise and tokenizers warnings
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# CPU-friendly defaults; adjust size to "small.en" if you want better accuracy
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base.en")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav_path", help="Path to WAV/MP3/MP4/M4A/FLAC")
    ap.add_argument("--out", default="", help="Write transcript to this file (optional)")
    args = ap.parse_args()

    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    segments, info = model.transcribe(args.wav_path, vad_filter=True, vad_parameters={"min_silence_duration_ms": 500})
    text = "".join([seg.text for seg in segments]).strip()

    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": MODEL_SIZE,
        "language": info.language,
        "text": text
    }

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(json.dumps(payload, ensure_ascii=False))

if __name__ == "__main__":
    main()
