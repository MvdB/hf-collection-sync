# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file Python tool (`hf_sync.py`) that mirrors a named HuggingFace collection to local
directories. Driven by SHA comparison: each model's remote commit SHA is checked against
`.sync_state.json`, and only changed/missing models are downloaded via `snapshot_download`.

## Commands

```bash
# Run the sync (reads .env from the repo root)
python hf_sync.py

# Windows entrypoint — note: hardcoded to A:\.venv\Scripts\python.exe in hf_sync.bat
hf_sync.bat

# Lint / format / type-check — these three are what CI runs
ruff check hf_sync.py
ruff format --check hf_sync.py
mypy hf_sync.py
```

There are no tests. CI (`.github/workflows/ci.yml`) only runs the three checks above.

## Architecture

Everything lives in `hf_sync.py`. The control flow in `main()`:

1. `load_token()` — reads `HF_TOKEN` from `.env` (loaded eagerly at module import so
   `HF_COLLECTION` is available before `main()` runs).
2. `api.whoami()` → username, then `find_collection()` resolves `HF_COLLECTION` (default
   `LocalCache`) against the user's collections. Falls back from exact-match to
   case-insensitive substring match. `api.get_collection(slug)` is required because
   `list_collections` returns truncated item lists.
3. For each `item_type == "model"` in the collection:
   - `get_remote_sha()` → current commit SHA
   - `sync_model()` decides skip / download / update based on `(local dir exists)`,
     `state[model_id].sha`, and `remote_sha`. State is written after every successful
     model so the run is resumable.

Layout convention: `owner/repo` on HF becomes the directory `owner--repo/` locally
(via `local_dir_for()`). `*--*/` is gitignored so model directories never get committed.

Persistent files at repo root, all gitignored:
- `.sync_state.json` — `{model_id: {sha, local_dir}}`, the source of truth for "is this up to date"
- `hf_sync.log` — full run log (appended each run)
- `.env` — `HF_TOKEN` (required) and `HF_COLLECTION` (optional, default `LocalCache`)

## Conventions

- Log/comment strings in `hf_sync.py` are in German — match that style when editing.
- Two knobs at the top of `hf_sync.py` control which files get downloaded:
  - `IGNORE_PATTERNS` — global blocklist applied to every repo (e.g. skip TF/Flax weights).
    `None` by default = download everything.
  - `ALLOW_PATTERNS` — `{model_id: [glob, ...]}`, an allowlist for individual repos. Not listed
    = whole repo. For repos shipping many quantization variants of the same weights, where the
    whole repo is hundreds of GB and you want three files. The patterns are stored in
    `.sync_state.json` under `allow`, so editing them re-downloads that model on the next run
    instead of waiting for the remote SHA to change.
- Python 3.11+, line length 100, ruff rules `E,F,W,I,UP` with `E501` ignored (see `pyproject.toml`).
