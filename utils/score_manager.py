import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path("data/history.json")

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(record):
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    history = load_history()
    record["timestamp"] = datetime.now().isoformat()
    history.append(record)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)