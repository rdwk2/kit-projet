# /// script
# requires-python = ">=3.10"
# ///
"""Prouve qu'un découpage n'a perdu aucune ligne : chaque ligne non vide de la référence se
retrouve, avec sa multiplicité, dans l'union des fichiers donnés.

    uv run outils/verifier_deplacement.py passations/CONTEXTE_avant_A7.md CONTEXTE.md LECONS_PROJET.md

Les chemins sont relatifs au dossier de conception de la piste, ou absolus. Code de sortie 1 si
une ligne manque.
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import espace
from _commun import sortie_utf8


def lignes(chemin: Path) -> collections.Counter[str]:
    if not chemin.is_file():
        sys.exit(f"{chemin} introuvable.")
    return collections.Counter(ligne for ligne in chemin.read_text(encoding="utf-8").split("\n") if ligne.strip())


def main() -> None:
    sortie_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("reference", help="le fichier d'avant le découpage")
    p.add_argument("fichiers", nargs="+", help="les fichiers d'après le découpage")
    p.add_argument("--piste", help="piste (défaut : principale)")
    args = p.parse_args()

    dossier = espace.conception(args.piste)
    reference = lignes(dossier / args.reference)
    union: collections.Counter[str] = collections.Counter()
    for nom in args.fichiers:
        union.update(lignes(dossier / nom))
    manque = reference - union
    print(
        f"référence : {sum(reference.values())} lignes non vides ; "
        f"retrouvées : {sum((reference & union).values())} ; perdues : {sum(manque.values())}"
    )
    for ligne, nombre in manque.items():
        print(f"  PERDUE ×{nombre} : {ligne[:120]}")
    sys.exit(1 if manque else 0)


if __name__ == "__main__":
    main()
