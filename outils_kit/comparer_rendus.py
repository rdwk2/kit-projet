# /// script
# requires-python = ">=3.10"
# dependencies = ["copier>=9.4"]
# ///
"""Compare le rendu du kit actuel à celui d'une version publiée, scénario par scénario.

Usage, depuis la racine du kit :
    uv run outils_kit/comparer_rendus.py                 # contre le dernier tag
    uv run outils_kit/comparer_rendus.py --ref v0.5.0    # contre un tag donné
    uv run outils_kit/comparer_rendus.py --seul espace-perso-complet --garder

Chaque scénario du banc (outils_kit/tester_kit.py) est généré deux fois : depuis le tag, et depuis
le kit tel qu'il est sur le disque (modifications non commitées comprises). Les deux arbres sont
comparés octet par octet, sans les fichiers de réponses `.copier-answers*` : une question nouvelle
y ajoute sa clé sans rien changer au reste.

Un scénario dont les réponses utilisent une question que le tag n'a pas est ignoré : il teste une
nouveauté, que la version publiée ne sait pas rendre.

Sert à prouver qu'un changement est additif : avec les réponses par défaut, le rendu ne bouge pas.
Code de sortie 1 si un fichier diffère, manque ou est en trop.
"""

from __future__ import annotations

import argparse
import difflib
import os
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import tester_kit as banc  # le dossier du script est dans le chemin d'import
import yaml
from copier import run_copy

KIT = banc.KIT
IGNORES = (".copier-answers",)
LIGNES_DIFF = 12


def dernier_tag() -> str:
    sortie = subprocess.run(["git", "describe", "--tags", "--abbrev=0", "HEAD"], cwd=KIT,
                            capture_output=True, text=True, check=False)
    if sortie.returncode != 0:
        sys.exit("Aucun tag trouvé : passer --ref.")
    return sortie.stdout.strip()


def questions_du_tag(ref: str) -> set[str]:
    sortie = subprocess.run(["git", "show", f"{ref}:copier.yml"], cwd=KIT, capture_output=True, check=False)
    if sortie.returncode != 0:
        sys.exit(f"Tag introuvable, ou sans copier.yml : {ref}")
    return {cle for cle in yaml.safe_load(sortie.stdout.decode("utf-8")) if not cle.startswith("_")}


def generations(sc: dict) -> list[dict]:
    """Les réponses d'un scénario : la piste principale, puis la piste supplémentaire s'il y en a une."""
    return [sc["data"]] + ([sc["piste"]["data"]] if "piste" in sc else [])


def generer(source: str, ref: str, dest: Path, data: dict) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_copy(source, dest, data={**banc.BASE, **data}, defaults=True, vcs_ref=ref,
                 quiet=True, unsafe=False, overwrite=True)


def fichiers(dossier: Path) -> dict[str, Path]:
    return {
        f.relative_to(dossier).as_posix(): f
        for f in dossier.rglob("*")
        if f.is_file() and not f.name.startswith(IGNORES)
    }


def apercu(avant: Path, apres: Path, rel: str) -> list[str]:
    try:
        a = avant.read_text(encoding="utf-8").splitlines()
        b = apres.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return ["        (fichier binaire)"]
    lignes = list(difflib.unified_diff(a, b, f"tag/{rel}", f"actuel/{rel}", n=1, lineterm=""))
    reste = len(lignes) - LIGNES_DIFF
    return [f"        {l}" for l in lignes[:LIGNES_DIFF]] + ([f"        … {reste} ligne(s) de plus"] if reste > 0 else [])


def comparer(avant: Path, apres: Path) -> list[str]:
    a, b = fichiers(avant), fichiers(apres)
    ecarts = [f"en moins : {rel}" for rel in sorted(a.keys() - b.keys())]
    ecarts += [f"en trop : {rel}" for rel in sorted(b.keys() - a.keys())]
    for rel in sorted(a.keys() & b.keys()):
        if a[rel].read_bytes() != b[rel].read_bytes():
            ecarts.append(f"différent : {rel}")
            ecarts += apercu(a[rel], b[rel], rel)
    return ecarts


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ref", help="tag de référence (défaut : le dernier tag)")
    p.add_argument("--seul", help="ne comparer que ce scénario")
    p.add_argument("--garder", action="store_true", help="garder les rendus (chemin affiché)")
    args = p.parse_args()

    ref = args.ref or dernier_tag()
    connues = questions_du_tag(ref)
    # Comme le banc : sous Windows, les essais se créent à côté du kit (antivirus, kit/MACHINE.md, AV-3).
    racine = Path(tempfile.mkdtemp(prefix="rendus_kit_", dir=KIT.parent if os.name == "nt" else None)).resolve()
    source_actuelle = str(banc.preparer_source(racine))
    # L'instantané reçoit le nom du tag : la version que les fichiers impriment en tête est la même des
    # deux côtés, et seul le contenu se compare.
    subprocess.run(["git", "tag", ref], cwd=source_actuelle, check=True, capture_output=True)

    total = 0
    for sc in banc.SCENARIOS:
        if args.seul and sc["nom"] != args.seul:
            continue
        nouvelles = sorted({cle for data in generations(sc) for cle in data} - connues)
        if nouvelles:
            print(f"[--] {sc['nom']} : ignoré, questions absentes de {ref} ({', '.join(nouvelles)})")
            continue
        avant, apres = racine / "tag" / sc["nom"], racine / "actuel" / sc["nom"]
        try:
            for data in generations(sc):
                generer(str(KIT), ref, avant, data)
                generer(source_actuelle, ref, apres, data)
            ecarts = comparer(avant, apres)
        except Exception as exc:  # noqa: BLE001 — un scénario qui plante est un échec, pas un arrêt
            ecarts = [f"{type(exc).__name__}: {exc}"]
        nombre = sum(1 for e in ecarts if not e.startswith(" "))
        print(f"[{'OK' if not ecarts else 'ÉCART'}] {sc['nom']}" + (f" ({nombre} fichier(s))" if ecarts else ""))
        for e in ecarts:
            print(f"    {e}")
        total += nombre

    if args.garder:
        print(f"\nRendus gardés dans {racine} (tag/ et actuel/)")
    elif not banc.retirer(racine):
        print(f"\n{racine} n'a pas pu être effacé en entier : le supprimer à la main.")
    print(f"\nRendu identique à {ref}." if total == 0 else f"\n{total} écart(s) avec {ref}.")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
