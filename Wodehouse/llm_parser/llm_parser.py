#!/usr/bin/env python3
import requests
import json
import uuid
import re
import time
from datetime import datetime

# --- Config ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3"

# --- Prompt Template ---
SYSTEM_PROMPT = """You are Wodehouse, a polite and helpful personal assistant.

Given a text transcript, identify if the user is:
- creating a task, reminder, or appointment
- logging a journal entry or personal note
- tracking a habit or daily activity

Extract this intent in JSON format.

Respond in the following JSON format:
{{
  "type": "reminder",
  "title": "short summary",
  "details": "full text of the user intent",
  "tags": ["optional", "contextual", "tags"],
  "timestamp": "YYYY-MM-DD HH:MM:SS"
}}

Today is {today}.
"""


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_prompt(user_input: str) -> str:
    prompt = SYSTEM_PROMPT.format(today=datetime.now().strftime("%A, %B %d, %Y"))
    prompt += f"\n\nTranscript: \"{user_input}\"\n"
    prompt += "Respond with only the JSON output."
    return prompt


def extract_json_block(text: str) -> dict:
    match = re.search(r'{.*}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    else:
        raise ValueError("No JSON block found in response")


def query_ollama(transcript: str, model=MODEL):
    prompt = build_prompt(transcript)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    start = time.time()
    try:
        print("Querying Wodehouse (phi-3)...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

        parsed = extract_json_block(raw)
        parsed["elapsed_sec"] = round(time.time() - start, 2)
        print(f"\u2705 Completed in {parsed['elapsed_sec']} sec")
        return parsed

    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        elapsed = round(time.time() - start, 2)
        print(f"\u274C Error after {elapsed} sec")
        return {
            "type": "error",
            "title": "LLM parsing error",
            "details": str(e),
            "tags": ["error", "llm", "wodehouse"],
            "timestamp": get_timestamp(),
            "elapsed_sec": elapsed
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: llm_parser \"transcript text here\"")
        exit(1)

    transcript = sys.argv[1]
    result = query_ollama(transcript)
    print(json.dumps(result, indent=2))