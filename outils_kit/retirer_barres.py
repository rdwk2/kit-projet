# /// script
# requires-python = ">=3.10"
# ///
"""Retire les barres `▌` de relecture, dans tous les fichiers suivis par git.

Usage, depuis la racine du kit :
    uv run outils_kit/retirer_barres.py

Une barre citée entre accents graves est la règle elle-même : elle reste.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def main() -> int:
    sortie = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
    total = 0
    for nom in filter(None, sortie.decode("utf-8").split("\0")):
        chemin = Path(nom)
        if chemin.name == "retirer_barres.py" or not chemin.is_file():
            continue
        octets = chemin.read_bytes()
        if "▌".encode() not in octets:
            continue
        texte, compte = re.subn(r"(?<!`)▌(?!`) ?", "", octets.decode("utf-8"))
        chemin.write_bytes(texte.encode("utf-8"))
        total += compte
    print(f"{total} barre(s) retirée(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
