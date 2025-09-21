#!/usr/bin/env python3
import csv, os
from datetime import datetime

BASE = "/mnt/wodehouse_data/shared"
LOG_DIR = os.path.join(BASE, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def append_markdown(entry: dict):
    day = datetime.now().strftime("%Y-%m-%d")
    md = os.path.join(LOG_DIR, f"{day}_daily_log.md")
    line = f"- **{entry.get('type','note').upper()}** — {entry.get('title','(untitled)')}  \n  {entry.get('details','')}\n"
    with open(md, "a", encoding="utf-8") as f:
        f.write(line)

def append_csv(entry: dict):
    csvp = os.path.join(LOG_DIR, "task_log.csv")
    exists = os.path.exists(csvp)
    with open(csvp, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["timestamp","type","title","details","tags","elapsed_sec"])
        w.writerow([
            entry.get("timestamp",""),
            entry.get("type",""),
            entry.get("title",""),
            entry.get("details",""),
            "|".join(entry.get("tags",[])),
            entry.get("elapsed_sec","")
        ])

def log(entry: dict):
    append_markdown(entry)
    append_csv(entry)
