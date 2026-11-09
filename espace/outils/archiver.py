# /// script
# requires-python = ">=3.10"
# ///
"""Archive des éléments de conception/ vers archives_conception/ : ne fait que déplacer.

A écrit la liste (un chemin par ligne, relatif à conception/, « # » pour commenter)
dans conception/passations/A_ARCHIVER_<étape>.txt, et une ligne par élément dans
INVENTAIRE_ARCHIVES.md ; l'humain relit, puis lance :

    uv run outils/archiver.py conception/passations/A_ARCHIVER_A12.txt            (essai à blanc)
    uv run outils/archiver.py conception/passations/A_ARCHIVER_A12.txt --executer

Garanties : rien n'est supprimé ; tout est vérifié avant le premier déplacement
(tout ou rien) ; chaque élément garde son chemin relatif, si bien que les liens
entre fichiers archivés restent valides ; un élément sans ligne d'inventaire,
un fichier vivant (CONTEXTE, index, inventaire, kit/, passations/ d'un bloc) ou une
destination déjà occupée arrêtent tout. La ligne d'inventaire doit être dans la section
« ## Archivages » (pas seulement dans « Restés en conception »). La liste se range elle-même dans les archives à la fin.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path, PurePosixPath

import espace

VIVANTS = {"CONTEXTE.md", "LECONS_PROJET.md", "MACHINE_PROJET.md", "00_LISEZ_MOI.md", "INVENTAIRE_ARCHIVES.md",
           "REMONTEES_KIT.md", "passations"}
"""Ce qui ne part jamais en entier (et le dossier kit/, rafraîchi par copier recopy).
`passations` part pièce par pièce, jamais d'un bloc."""


def section_archivages(inventaire: str) -> str:
    """Le texte de la section « ## Archivages » de l'inventaire, seule à faire foi : un chemin
    encore listé dans « Restés en conception » ne doit pas satisfaire le contrôle."""
    dedans, lignes = False, []
    for ligne in inventaire.splitlines():
        if ligne.startswith("## "):
            dedans = ligne.strip().lower().startswith("## archivages")
            continue
        if dedans:
            lignes.append(ligne)
    return "\n".join(lignes)


def lire_liste(fichier: Path) -> list[PurePosixPath]:
    elements = []
    for brute in fichier.read_text(encoding="utf-8-sig").splitlines():
        ligne = brute.split("#", 1)[0].strip().replace("\\", "/").rstrip("/")
        if ligne:
            elements.append(PurePosixPath(ligne))
    return elements


def problemes(elements: list[PurePosixPath], source: Path, cible: Path, inventaire: str) -> list[str]:
    erreurs = []
    vus: set[PurePosixPath] = set()
    for rel in elements:
        if rel.is_absolute() or ".." in rel.parts:
            erreurs.append(f"{rel} : chemin relatif à conception/ attendu, sans « .. »")
            continue
        if rel in vus:
            erreurs.append(f"{rel} : listé deux fois")
        vus.add(rel)
        if rel.parts[0] == "kit" or (len(rel.parts) == 1 and rel.name in VIVANTS):
            erreurs.append(f"{rel} : fichier vivant ou fichier du kit, il ne s'archive pas")
        if not (source / rel).exists():
            erreurs.append(f"{rel} : introuvable dans {source}")
        if (cible / rel).exists():
            erreurs.append(f"{rel} : existe déjà dans {cible} (rien n'est écrasé)")
        if f"`{rel}`" not in inventaire:
            erreurs.append(
                f"{rel} : absent de la section « Archivages » d'INVENTAIRE_ARCHIVES.md "
                f"(chemin attendu tel quel, entre accents graves : `{rel}`)"
            )
    return erreurs


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("liste", type=Path, help="fichier de la liste écrite par A")
    p.add_argument("--piste", default=None)
    p.add_argument("--executer", action="store_true", help="déplacer pour de vrai")
    args = p.parse_args()

    source, cible = espace.conception(args.piste), espace.archives(args.piste)
    liste = args.liste if args.liste.is_absolute() else Path.cwd() / args.liste
    inventaire_md = source / "INVENTAIRE_ARCHIVES.md"
    inventaire = section_archivages(inventaire_md.read_text(encoding="utf-8")) if inventaire_md.exists() else ""
    elements = lire_liste(liste)
    if not elements:
        raise SystemExit(f"Liste vide : {liste}")

    erreurs = problemes(elements, source, cible, inventaire)
    for rel in elements:
        print(f"  {source / rel}  ->  {cible / rel}")
    if erreurs:
        print("\nRien n'a été déplacé :")
        for e in erreurs:
            print(f"  - {e}")
        raise SystemExit(1)
    if not args.executer:
        print(f"\nEssai à blanc : {len(elements)} élément(s) prêt(s). Relancer avec --executer.")
        return

    for rel in elements:
        (cible / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source / rel), str(cible / rel))
    try:
        rel_liste = PurePosixPath(liste.resolve().relative_to(source.resolve()).as_posix())
    except ValueError:
        rel_liste = None
    if rel_liste is not None and not (cible / rel_liste).exists():
        (cible / rel_liste).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(liste), str(cible / rel_liste))
    print(f"\n{len(elements)} élément(s) déplacé(s) vers {cible}. Rien n'a été supprimé.")


if __name__ == "__main__":
    main()
