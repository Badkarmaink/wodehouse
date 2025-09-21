📘 Wodehouse Assistant — Project Overview

An offline-first, voice-driven AI assistant designed for personal productivity, built using containers and a local LLM (Phi-3). 
📌 Project Goals

Voice-to-command interaction via push-to-talk or wake word

Use local models (LLM + Whisper) for privacy

Container-based architecture for modularity and portability

Markdown-friendly web UI with dark mode for desktop/mobile

Log all voice actions and suggest responses (PoC mode)

No home automation — automation is server-side only

Capable of triggering scripts via Alfred or CLI

Support task nudges, journaling, habit tracking

⚙️ System Architecture

Primary Host: 8-core laptop, 64GB RAM, 2TB disk

Secondary Node: 4-core box, 64GB RAM (remote accessible)

GPU: Starting CPU-only; Upgrades: RTX 3050 → 3060 (12GB)

🧱 Components

| Component | Description |
| --- | --- |
| Wodehouse | Local LLM logic & speech assistant |
| Whisper | OpenAI STT (local) for audio input |
| Web UI | Dark mode UI with chat, logs, markdown output |
| Queue | JSONL-based queue system for task communication |
| Config | JSON config defines assistant name, wake words, etc |
| Alfred | Script runner triggered by assistant intent (via JSONL) |

🎙️ Voice Interaction

Mode: Push-to-Talk (Space) or Wake Word ("Wodehouse")

Flow: Mic input → Whisper STT → Intent detection → Action suggestion

PoC Mode: Logs what it would do (“Add meeting to calendar. Should I invite Joanna?”)

Supports toggling mic, stopping recording, testing debug mode

📦 Container Strategy

All components run in containers (WSL2-compatible)

LLM (Phi-3), Whisper, web UI, queue monitor are all decoupled

Secondary machine can offload: Whisper, LLM, or task runners

🧠 Model

LLM: phi-3 selected for offline inference

Model inference kept local — no outbound “thinking” unless manually approved (e.g., code research)

Lightweight but capable of generating Alfred scripts or responses

🧾 Config Example
{
  "assistant_name": "wodehouse",
  "pronunciation": "woodhouse",
  "wake_words": ["wodehouse", "buddy", "taskbot"],
  "ptt_key": "space",
  "web_ui": true,
  "dark_mode": true,
  "queue_file": "/var/log/wodehouse/queue.jsonl",
  "test_mode": true
}

🔄 Repo Integration

GitHub integration active

All repo interactions go through JSONL queue and are configurable

Future: Enable auto-update of modules via Git pull or internal trigger

✅ Recent Changes

✅ Converted from “always listening” to push-to-talk and wake word

✅ Default name “Wodehouse” made configurable in JSON (assistant_name)

✅ Added remote second box support with install instructions

✅ Web UI designed in Markdown, mobile-friendly

✅ Secondary box validated for Whisper/LLM delegation

📅 Coming Soon

Journaling & daily summary logs

Habit tracker integration (via voice)

Alfred task queue integration (bi-directional)

Webhooks + custom script flow (JSON-defined recipes)

Codex-style code analysis via web interface
