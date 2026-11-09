# /// script
# requires-python = ">=3.10"
# ///
"""Affiche une section d'un fichier Markdown par le début de son titre, sans lire le reste.

    uv run outils/lire_section.py kit/METHODE.md --toc     (titres, niveaux et tailles)
    uv run outils/lire_section.py kit/LECONS.md "BRF"      (la section dont le titre commence ainsi)

Le chemin est relatif au dossier de conception de la piste, ou absolu.
"""

from __future__ import annotations

import argparse
import sys

import espace
from _commun import octets, sections, sortie_utf8


def main() -> None:
    sortie_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fichier", help="fichier Markdown, relatif au dossier de conception ou absolu")
    p.add_argument("titre", nargs="?", help="début du titre de la section")
    p.add_argument("--toc", action="store_true", help="afficher les titres et leur taille")
    p.add_argument("--piste", help="piste (défaut : principale)")
    args = p.parse_args()
    if not args.toc and not args.titre:
        p.error("donner un titre, ou --toc")

    chemin = espace.conception(args.piste) / args.fichier
    if not chemin.is_file():
        sys.exit(f"{chemin} introuvable.")
    lignes, secs = sections(chemin.read_text(encoding="utf-8"))
    if args.toc:
        for niveau, titre, debut, fin in secs:
            print(f"{'  ' * (niveau - 1)}{titre[:90]}  [{octets(lignes[debut:fin]) / 1024:.1f} Ko]")
        return

    cible = args.titre.lower()
    trouves = [s for s in secs if s[1].lower().startswith(cible)] or [s for s in secs if cible in s[1].lower()]
    if not trouves:
        sys.exit(f"Aucun titre ne commence par « {args.titre} » (voir --toc).")
    if len(trouves) > 1:
        autres = " | ".join(s[1] for s in trouves[:6])
        print(f"[{len(trouves)} titres correspondent ; le premier est affiché : {autres}]")
    _, _, debut, fin = trouves[0]
    print("\n".join(lignes[debut:fin]))


if __name__ == "__main__":
    main()
