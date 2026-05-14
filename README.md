# hf-collection-sync

Syncs all models from a named HuggingFace collection to a local directory.
Updates are detected via commit SHA — already-current models are skipped without re-downloading.

## How it works

1. Authenticates with the HuggingFace API using your token
2. Fetches the full collection (by name) from your account
3. For each model, compares the remote commit SHA against the locally stored one
4. Downloads or updates only what has changed

Local directory layout mirrors the collection:

```
./mistralai--Mistral-7B-v0.1/
./meta-llama--Llama-3-8B/
...
```

State is persisted in `.sync_state.json` so interrupted runs resume cleanly.

## Setup

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# → edit .env and insert your HF_TOKEN
```

Linux / macOS (use a separate venv path if the repo lives on a share that's
also accessed from Windows — the two venvs are not compatible):

```bash
python3 -m venv .venv-linux
.venv-linux/bin/pip install -r requirements.txt

cp .env.example .env
# → edit .env and insert your HF_TOKEN
```

Get your token at <https://huggingface.co/settings/tokens> (read access is sufficient).

## Configuration

Set these variables in your `.env` file:

| Variable | Default | Description |
|---|---|---|
| `HF_TOKEN` | — | HuggingFace API token (required) |
| `HF_COLLECTION` | `LocalCache` | Exact or partial name of the HF collection |

To skip certain file types, edit `IGNORE_PATTERNS` at the top of `hf_sync.py`:

Example — skip non-PyTorch weights:

```python
IGNORE_PATTERNS = ["*.msgpack", "flax_model*", "tf_model*", "rust_model*"]
```

## Usage

```bash
# Linux / macOS (uses .venv-linux automatically)
./hf_sync.sh

# Windows (uses the local .venv automatically)
hf_sync.bat
```

Output:

```
============================================================
HF LocalCache Sync  —  Collection: 'LocalCache'
============================================================
Angemeldet als: your-username
Collection 'LocalCache': 6 Modelle
[OK]       Qwen/Qwen3.5-0.8B  (sha 2fc06364…)
[DOWNLOAD] Qwen/Qwen3.5-14B
[UPDATE]   mistralai/Mistral-7B-v0.1  (abc12345… → def67890…)
...
============================================================
Zusammenfassung:
  Aktuell (übersprungen): 4
  Neu heruntergeladen:    1
  Aktualisiert:           1
  Fehlgeschlagen:         0
============================================================
```

A full log is written to `hf_sync.log` alongside the script.

## Automating with Task Scheduler (Windows)

Create a basic task that runs `hf_sync.bat` on a schedule — daily or on login.

## Requirements

- Python 3.11+
- `huggingface_hub >= 0.24.0`
- `python-dotenv >= 1.0.0`

## License

MIT — see [LICENSE](LICENSE)
