# /// script
# requires-python = ">=3.10"
# ///
"""Publie le commentaire de revue d'une PR (option « Comment » : GitHub interdit
d'approuver sa propre PR, ce qui est le cas d'un projet à une personne) depuis
conception/passations/REVUE_PR-<n>.md, écrit par A.

Le commentaire dit ce qui a été vérifié : il porte sur l'état final de la branche,
donc juste avant la fusion. Le fichier est lu tel quel, accents compris.

Usage : uv run outils/revue_pr.py 42 [--piste analyse]
"""

import argparse

import espace


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("numero", type=int)
    p.add_argument("--piste", default=None)
    args = p.parse_args()

    fichier = espace.passations(args.piste) / f"REVUE_PR-{args.numero}.md"
    if not fichier.is_file():
        raise SystemExit(f"Commentaire introuvable : {fichier} (A l'écrit d'abord)")
    espace.lancer(
        ["gh", "pr", "review", str(args.numero), "--comment", "--body-file", str(fichier)],
        espace.miroir_pret(args.piste),
    )
    print("Commentaire publié. Ensuite, sur GitHub : « Squash and merge », puis uv run outils/miroir.py")


if __name__ == "__main__":
    main()
