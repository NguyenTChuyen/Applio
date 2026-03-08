# OpenClaw Config Sync

Khi agent thay doi config OpenClaw local, phai dong bo ban backup sanitized len GitHub.

Local files can sync:

- `~/.openclaw/openclaw.json`
- `~/.openclaw/agents/main/agent/models.json`
- khi can, cap nhat them `openclaw_baoan_memory/AGENTS.memory.md` neu huong dan memory thay doi

Quy trinh bat buoc sau moi thay doi config:

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
