#!/usr/bin/env python3
import os, time, json, subprocess, shlex
from datetime import datetime

BASE = "/mnt/wodehouse_data"
AUDIO_DIR = f"{BASE}/shared/audio"
TRANSCRIBER = f"{BASE}/whisper_transcriber/transcribe.py"
LLM_PARSER = "/usr/local/bin/llm_parser"  # your symlinked parser
LOG_MOD = f"{BASE}/task_logger/logger.py"

os.makedirs(AUDIO_DIR, exist_ok=True)

def transcribe(path):
    cmd = f"{shlex.quote(TRANSCRIBER)} {shlex.quote(path)}"
    out = subprocess.check_output(cmd, shell=True, text=True)
    j = json.loads(out)
    return j["text"]

def parse_with_llm(text):
    cmd = f'{shlex.quote(LLM_PARSER)} {shlex.quote(text)}'
    out = subprocess.check_output(cmd, shell=True, text=True)
    return json.loads(out)

def log_entry(entry):
    import importlib.util
    spec = importlib.util.spec_from_file_location("logger", LOG_MOD)
    logger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(logger)
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.log(entry)

def main():
    seen = set()
    print("🔁 Watching for new audio clips…")
    while True:
        for fname in sorted(os.listdir(AUDIO_DIR)):
            if not fname.endswith(".wav"): continue
            full = os.path.join(AUDIO_DIR, fname)
            if full in seen: continue
            seen.add(full)
            print(f"🧩 Processing {fname}…")
            try:
                text = transcribe(full)
                if not text.strip():
                    print("…empty transcript, skipping")
                    continue
                parsed = parse_with_llm(text)
                log_entry(parsed)
                print(f"✅ Logged: {parsed.get('type')} — {parsed.get('title')}")
            except subprocess.CalledProcessError as e:
                print("STT/LLM error:", e)
            except json.JSONDecodeError as e:
                print("Bad JSON:", e)
        time.sleep(2)

if __name__ == "__main__":
    main()

