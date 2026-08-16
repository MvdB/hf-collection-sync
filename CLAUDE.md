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
   - `get_remote_info()` → current commit SHA **and** the repo's file list (both come
     from the same `model_info` call)
   - `sync_model()` decides skip / download / update based on `(local dir exists)`,
     `state[model_id].sha`, and `remote_sha`. State is written after every successful
     model so the run is resumable.
   - `prune_removed()` cleans up files that no longer exist upstream —
     `snapshot_download` never deletes, so a shard set that was replaced upstream would
     otherwise sit on disk forever. Runs after `[OK]` too, since a file deleted in a
     commit that was already synced is only ever caught by a later sweep.

Layout convention: `owner/repo` on HF becomes the directory `owner--repo/` locally
(via `local_dir_for()`). `*--*/` is gitignored so model directories never get committed.

Persistent files at repo root, all gitignored:
- `.sync_state.json` — `{model_id: {sha, local_dir}}`, the source of truth for "is this up to date"
- `hf_sync.log` — full run log (appended each run)
- `.env` — `HF_TOKEN` (required), `HF_COLLECTION` (optional, default `LocalCache`) and
  `HF_PRUNE_MODE` (optional, default `move`). It is loaded
  *before* the config constants are evaluated — they are module-level, so a later load
  would be silently ignored. Loaded without `override`, so a one-off
  `HF_PRUNE_MODE=report ./hf_sync.sh` beats the `.env` value.

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
- Pruning is governed by `HF_PRUNE_MODE` (env or `.env`), default `move`:
  - `move` — file goes to `~/southbyte/_retired/hf_models-prune/<date>/<owner--repo>/<path>`.
    Same filesystem, so it's a rename, not a copy — but disk is only reclaimed once that
    directory is emptied by hand. This is the default because of the house rule that
    nothing in `$HOME` gets deleted.
  - `delete` — removed on the spot. Only reasonable if a mirror elsewhere holds a copy:
    once a file is gone upstream, the sync can never fetch it back.
  - `report` — logs `[PRUNE?]` lines and changes nothing. Also the fallback for a typo'd
    value, so a bad `HF_PRUNE_MODE` can never delete anything.

  Only files carrying a `.cache/huggingface/download/<path>.metadata` sidecar are ever
  touched — that's the hub's own record of what it downloaded. Locally maintained files
  such as `vllm_profile.conf` have no sidecar and are never candidates. An empty remote
  file list (API hiccup, gated repo) is treated as "no information", never as "everything
  was deleted".
- Python 3.11+, line length 100, ruff rules `E,F,W,I,UP` with `E501` ignored (see `pyproject.toml`).
