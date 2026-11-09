# /// script
# requires-python = ">=3.10"
# ///
"""Fonctions communes aux outils de lecture du contexte (bibliothèque standard seule)."""

from __future__ import annotations

import re
import sys

JETONS_PAR_KO = 285
"""Estimation : 3,5 caractères par jeton, en français accentué."""


def sortie_utf8() -> None:
    """Sous Windows, une sortie redirigée n'est pas en UTF-8 : un accent y ferait planter l'affichage."""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]


def sections(texte: str) -> tuple[list[str], list[tuple[int, str, int, int]]]:
    """Les lignes du texte et ses sections (niveau, titre, début, fin exclue) ; un titre dans un bloc ``` ne compte pas."""
    lignes = texte.split("\n")
    titres: list[tuple[int, str, int]] = []
    dans_code = False
    for i, ligne in enumerate(lignes):
        if ligne.startswith("```"):
            dans_code = not dans_code
        m = None if dans_code else re.match(r"^(#{1,4}) (.*)", ligne)
        if m:
            titres.append((len(m.group(1)), m.group(2).strip(), i))
    resultat = []
    for k, (niveau, titre, debut) in enumerate(titres):
        fin = len(lignes)
        for autre_niveau, _, j in titres[k + 1 :]:
            if autre_niveau <= niveau:
                fin = j
                break
        resultat.append((niveau, titre, debut, fin))
    return lignes, resultat


def octets(lignes: list[str]) -> int:
    """La taille de ces lignes dans le fichier, fins de ligne comprises."""
    return sum(len(ligne.encode("utf-8")) + 1 for ligne in lignes)
