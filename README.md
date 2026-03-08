# Applio

BiAnCoXua

## OpenClaw BM25 Memory

This repository now includes an `openclaw_bm25/` package containing a Vietnamese-first BM25 memory workflow for OpenClaw.

Included files:

- `openclaw_bm25/bm25_memory.py` - BM25 memory engine with duplicate merge, phrase-aware ranking, token-budget context, and query intent hints
- `openclaw_bm25/SKILL.md` - OpenClaw skill instructions standardized on BM25
- `openclaw_bm25/AGENTS.memory.md` - AGENTS memory section updated to prefer BM25 over legacy memory systems

Goals:

- smarter memory storage
- faster retrieval
- better Vietnamese recall for accented and unaccented queries
- lower OpenClaw token usage by reducing irrelevant context
