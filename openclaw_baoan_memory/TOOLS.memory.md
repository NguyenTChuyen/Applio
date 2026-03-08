# TOOLS.md

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Memory (BaoAn Memory - Primary)

**⚠️ BỘ NHỚ CHÍNH** - BaoAn Memory, nhanh hơn nhiều so với vector memory cũ

### Access

- **Script**: `python3 /home/babyhack8x/.openclaw/workspace/skills/baoan-memory.py`

### Commands

**Store memory:**
```bash
python3 /home/babyhack8x/.openclaw/workspace/skills/baoan-memory.py add "nội dung" category importance
```

**Search memory:**
```bash
python3 /home/babyhack8x/.openclaw/workspace/skills/baoan-memory.py search "từ khóa" [limit]
```

**Get history:**
```bash
python3 /home/babyhack8x/.openclaw/workspace/skills/baoan-memory.py history [limit] [offset]
```

**Get context:**
```bash
python3 /home/babyhack8x/.openclaw/workspace/skills/baoan-memory.py context [limit] [max_tokens] [mode]
```

**Lifecycle:**
```bash
python3 /home/babyhack8x/.openclaw/workspace/skills/baoan-memory.py precompact "nội dung cần giữ"
python3 /home/babyhack8x/.openclaw/workspace/skills/baoan-memory.py maintain 45
python3 /home/babyhack8x/.openclaw/workspace/skills/baoan-memory.py state
```

### Categories

- **product**: Thông tin sản phẩm
- **api**: API keys, tokens, secrets
- **preference**: Sở thích, yêu cầu của khách
- **conversation**: Thông tin cuộc trò chuyện
- **other**: Thông tin khác

### Importance

- 0.0 - 1.0 (1.0 = quan trọng nhất)

### When to Use

- **Store**: When user shares preferences, important info, or context you want to remember
- **Search**: When you need to find relevant past context

### Backup

- **Legacy vector memory**: da bo khoi workspace de tranh nham lan
