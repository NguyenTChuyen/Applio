# Applio

BiAnCoXua

## OpenClaw BaoAn Memory

This repository now includes an `openclaw_baoan_memory/` package containing a Vietnamese-first BaoAn Memory workflow for OpenClaw.

Included files:

- `openclaw_baoan_memory/baoan-memory.py` - BaoAn Memory engine with lifecycle controls, duplicate merge, phrase-aware ranking, token-budget context, flush/precompact, pinned/archive, and query intent hints
- `openclaw_baoan_memory/SKILL.md` - OpenClaw skill instructions standardized on `baoan-memory`
- `openclaw_baoan_memory/AGENTS.memory.md` - AGENTS memory section updated to prefer BaoAn Memory over legacy systems
- `openclaw_baoan_memory/TOOLS.memory.md` - workspace tool notes aligned to BaoAn Memory

Goals:

- smarter memory storage
- faster retrieval
- better Vietnamese recall for accented and unaccented queries
- lower OpenClaw token usage by reducing irrelevant context
- cleaner lifecycle management for recent, curated, pinned, and archived memory
