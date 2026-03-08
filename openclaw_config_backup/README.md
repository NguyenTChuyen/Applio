# OpenClaw Config Backup

Sanitized backup of local OpenClaw config files.

Included files:

- `openclaw.json` - sanitized main config snapshot
- `models.json` - sanitized model registry snapshot

Secrets are redacted before committing.

Local source files:

- `~/.openclaw/openclaw.json`
- `~/.openclaw/agents/main/agent/models.json`

Use `scripts/sync_openclaw_config.py` to refresh these backups safely.
