# /// script
# requires-python = ">=3.10"
# ///
"""Écrit le diff exact d'une PR, calculé par GitHub depuis la base de fusion,
dans v_for_cowork/pr-<n>.diff, là où A et B le lisent (A le joint au paquet de la C).

Usage (depuis la racine de l'espace) :
    uv run outils/diff_pr.py 42
    uv run outils/diff_pr.py 42 --piste analyse

Pourquoi un script : le diff doit être identique sur tous les systèmes. Sous Windows
PowerShell 5.1, `>` écrit en UTF-16, un tube vers Set-Content décode la sortie de gh
en CP850 (mojibake), et Set-Content -Encoding utf8 ajoute un BOM et des CRLF. Ici, les
octets de gh passent sans jamais être décodés.
"""

import argparse

import espace


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("numero", type=int, help="numéro de la PR")
    p.add_argument("--piste", default=None, help="nom de la piste (défaut : principale)")
    args = p.parse_args()

    miroir = espace.miroir_pret(args.piste)
    diff = espace.lancer(["gh", "pr", "diff", str(args.numero)], miroir, capturer=True)
    espace.ecrire_octets(espace.v_for_cowork(args.piste) / f"pr-{args.numero}.diff", diff)


if __name__ == "__main__":
    main()
