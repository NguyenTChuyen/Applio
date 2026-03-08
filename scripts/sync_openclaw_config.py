#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "openclaw_config_backup"

SOURCES = {
    Path.home() / ".openclaw/openclaw.json": BACKUP_DIR / "openclaw.json",
    Path.home() / ".openclaw/agents/main/agent/models.json": BACKUP_DIR / "models.json",
}

REDACT_KEYS = {"apiKey", "botToken", "token", "accessToken", "secret"}


def sanitize(value):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in REDACT_KEYS:
                result[key] = "REDACTED"
            else:
                result[key] = sanitize(item)
        return result
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for src, dst in SOURCES.items():
        data = json.loads(src.read_text())
        dst.write_text(json.dumps(sanitize(data), ensure_ascii=False, indent=2) + "\n")
        print(f"synced {src} -> {dst}")


if __name__ == "__main__":
    main()
