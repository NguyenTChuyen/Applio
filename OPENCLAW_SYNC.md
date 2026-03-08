# OpenClaw Config Sync

Khi agent thay doi config OpenClaw local, phai dong bo ban backup sanitized len GitHub.

Local files can sync:

- `~/.openclaw/openclaw.json`
- `~/.openclaw/agents/main/agent/models.json`
- khi can, cap nhat them `openclaw_baoan_memory/AGENTS.memory.md` neu huong dan memory thay doi

Quy trinh thu cong sau moi thay doi config:

```bash
python3 /home/babyhack8x/dev/Applio/scripts/sync_openclaw_config.py
git -C /home/babyhack8x/dev/Applio add openclaw_config_backup README.md OPENCLAW_SYNC.md
git -C /home/babyhack8x/dev/Applio commit -m "Sync OpenClaw config backup"
git -C /home/babyhack8x/dev/Applio push origin main
```

Quy tac:

- khong commit secret thuan van; script da redact cac khoa nhu `apiKey`, `botToken`, `token`, `secret`
- neu thay doi them cac file huong dan trong workspace, copy sang repo truoc khi commit
- neu khong co thay doi sau khi sync, khong tao commit rong

## Tu dong dong bo

Da co watcher local qua systemd user service:

- service: `openclaw-config-autosync.service`
- script watcher: `scripts/openclaw_config_autosync.py`

Khi `~/.openclaw/openclaw.json` hoac `~/.openclaw/agents/main/agent/models.json` thay doi, watcher se tu dong:

1. chay sanitize backup
2. commit voi message `Auto-sync OpenClaw config backup`
3. push len `origin/main`

Watcher co debounce thong minh:

- poll moi `20s`
- cho config on dinh `90s` roi moi sync
- giup tranh tao nhieu commit neu OpenClaw ghi file lien tuc trong mot dot thay doi

Lenh kiem tra:

```bash
systemctl --user status openclaw-config-autosync.service
journalctl --user -u openclaw-config-autosync.service -n 50 --no-pager
```
