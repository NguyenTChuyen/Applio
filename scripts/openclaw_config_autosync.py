#!/usr/bin/env python3

import json
import subprocess
import time
from pathlib import Path

REPO_DIR = Path('/home/babyhack8x/dev/Applio')
SYNC_SCRIPT = REPO_DIR / 'scripts/sync_openclaw.sh'
STATE_FILE = Path.home() / '.baoan_memory/openclaw_config_sync_state.json'
WATCH_FILES = [
    Path.home() / '.openclaw/openclaw.json',
    Path.home() / '.openclaw/agents/main/agent/models.json',
]
POLL_SECONDS = 20


def file_state(path):
    if not path.exists():
        return None
    stat = path.stat()
    return {'mtime': stat.st_mtime_ns, 'size': stat.st_size}


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')


def main():
    state = load_state()
    while True:
        changed = False
        new_state = {}
        for path in WATCH_FILES:
            current = file_state(path)
            new_state[str(path)] = current
            if state.get(str(path)) != current:
                changed = True

        if changed:
            subprocess.run([str(SYNC_SCRIPT), 'Auto-sync OpenClaw config backup'], check=True)
            state = new_state
            save_state(state)

        time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    main()
