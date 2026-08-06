#!/usr/bin/env python3
"""
Schreibt die Verzeichnisnamen aller Modelle der HF-Collection in eine Datei.
-------------------------------------------------------------------------
Wird von sync_all.sh für den Retention-Schritt benutzt: alles was NICHT in
dieser Liste steht, ist ein Altmodell und wandert nach /nfs/ai/old_models.

Nutzt bewusst die Funktionen aus hf_sync.py (eine Quelle der Wahrheit) statt
die Collection-Auflösung zu duplizieren.

Aufruf:
    collection_dirs.py <ausgabedatei>

Exit 0 nur wenn die Liste vollständig geschrieben wurde. Bei jedem Fehler
Exit != 0 und die Ausgabedatei bleibt unangetastet -- sync_all.sh bricht dann
die Retention ab, damit ein API-Fehler nicht alle Modelle als "alt" erscheinen
lässt.
"""

import sys
from pathlib import Path

from huggingface_hub import HfApi

from hf_sync import find_collection, load_token


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: collection_dirs.py <outfile>", file=sys.stderr)
        sys.exit(2)

    out = Path(sys.argv[1])

    token = load_token()
    api = HfApi()

    username = api.whoami(token=token)["name"]
    collection = find_collection(api, username, token)

    dirs = sorted(
        item.item_id.replace("/", "--") for item in collection.items if item.item_type == "model"
    )

    if not dirs:
        print("Collection lieferte 0 Modelle – Abbruch.", file=sys.stderr)
        sys.exit(1)

    # Erst in eine temporäre Datei, dann atomar umbenennen: eine halb
    # geschriebene Liste darf nie als gültig gelesen werden.
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text("\n".join(dirs) + "\n", encoding="utf-8")
    tmp.replace(out)


if __name__ == "__main__":
    main()
