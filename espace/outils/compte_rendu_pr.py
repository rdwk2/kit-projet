# /// script
# requires-python = ">=3.10"
# ///
"""Copie la description d'une PR (le compte rendu de l'agent de code) dans
conception/passations/COMPTE_RENDU_CODE_PR-<n>.md — pour A seulement : ni B ni C
ne prennent leur énoncé des mains de l'auteur.

Usage : uv run outils/compte_rendu_pr.py 42 [--piste analyse]
"""

import argparse

import espace


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("numero", type=int)
    p.add_argument("--piste", default=None)
    args = p.parse_args()

    corps = espace.lancer(
        ["gh", "pr", "view", str(args.numero), "--json", "body", "-q", ".body"],
        espace.miroir_pret(args.piste),
        capturer=True,
    )
    cible = espace.passations(args.piste) / f"COMPTE_RENDU_CODE_PR-{args.numero}.md"
    espace.ecrire_octets(cible, corps)


if __name__ == "__main__":
    main()
