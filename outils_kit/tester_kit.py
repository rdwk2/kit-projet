# /// script
# requires-python = ">=3.10"
# dependencies = ["copier>=9.4"]
# ///
"""Banc d'essai du kit : génère chaque préréglage et vérifie le résultat.

Usage, depuis la racine du kit :
    uv run outils_kit/tester_kit.py              # générations et vérifications de structure
    uv run outils_kit/tester_kit.py --complet    # + uv sync et just check dans les dépôts Python générés
    uv run outils_kit/tester_kit.py --garder     # garde les projets générés (chemin affiché)

Ce que vérifie le banc, une fois pour tout le kit :
- chaque schéma des pages a sa source `.mmd`, identique, et inversement ;
- si la variable KIT_TERMES_PRIVES donne un fichier de termes, aucun n'est dans le kit.
Ce que vérifie chaque scénario :
- les fichiers attendus sont là, les fichiers exclus n'y sont pas ;
- aucun délimiteur de gabarit ne reste ([[ … ]], [% … %], [# … #]) et aucun fichier .jinja ;
- un filet `---` a une ligne vide avant lui : sinon, Markdown fait un titre du paragraphe ;
- les scripts d'outils/ se compilent et répondent à --help ;
- les passages qui dépendent des réponses (dépôt public ou privé) sont les bons ;
- recopy : un fichier vivant modifié est gardé, un fichier du kit effacé revient ;
- update (dépôt) : une nouveauté du kit arrive, une modification locale reste ;
- extraction entre pistes : le CONTEXTE généré suit le plan fixe d'extraire_piste.py ;
- chaque renvoi à une entrée de kit/MACHINE.md existe ;
- `CLAUDE.md` a ses huit règles, avec leurs numéros, dans tous les préréglages ;
- la lecture d'ouverture d'une A tient dans son budget, et un CONTEXTE gonflé fait échouer la mesure ;
- un préréglage ne cite aucun fichier qu'il n'a pas, et refuse une piste sans le module pistes ;
- un `racine` en `~/…` donne un chemin absolu aux scripts ;
- avec --complet : uv sync, uv sync --locked et just check dans chaque dépôt Python généré,
  avec un module qui écrit comme un mathématicien (`A`, `X`, `l`, lettres grecques) et, pour
  débuter, une fonction sans annotations.
Code de sortie 0 si tout passe.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import traceback
import warnings
from pathlib import Path

from copier import run_copy, run_recopy, run_update

KIT = Path(__file__).resolve().parent.parent


def retirer(dossier: Path) -> bool:
    """Efface un dossier, fichiers en lecture seule compris (objets git sous Windows)."""

    def forcer(fonction, chemin, _erreur):
        os.chmod(chemin, stat.S_IWRITE)
        fonction(chemin)

    try:
        if sys.version_info >= (3, 12):
            shutil.rmtree(dossier, onexc=forcer)
        else:
            shutil.rmtree(dossier, onerror=forcer)
    except OSError:
        return False
    return True
DELIMITEURS = re.compile(r"\[\[ |\[% |\[# | \]\]| %\]| #\]")
# Les entrées de kit/MACHINE.md citées ailleurs ; GIT-n manque ici : il sert aussi aux leçons.
RENVOIS = re.compile(r"\b(?:SYS|VER|AV|PS|CMD|PY|UV|JU|GH|AFF|WSL|CL|ML)-\d+\b")
SCHEMA = re.compile(r"```mermaid\n(.*?)```", re.S)
MODULE_MATHS = '''"""Moindres carrés : on résout A x = b, avec une variance σ² et un seuil α."""


def resoudre(A: list[float], b: list[float]) -> list[float]:
    """Résout A x = b, terme à terme."""
    X = [y / a for a, y in zip(A, b, strict=True)]
    return X


def total(l: list[float]) -> float:
    """Somme les valeurs."""
    return sum(l)
'''

MODULE_SOUPLE = '''"""Une fonction sans annotations : mypy en mode souple l'accepte."""


def carre(x):
    """Renvoie le carré de x."""
    return x * x
'''

BASE = {
    "projet": "Projet d'essai",
    "slug": "projet-essai",
    "description": "Une phrase d'essai.",
    "racine": "~/dev/projet-essai",
    "humain": "Alice",
    "github": "alice/projet-essai",
    "responsables": "@alice @bob",
}

DEPOT_SOCLE = [
    "CLAUDE.md", "AGENTS.md", "README.md", "BACKLOG.md", ".gitignore", ".gitattributes",
    "docs/ROADMAP.md", "docs/JOURNAL.md", "docs/PIEGES.md", "docs/decisions/0000-template.md",
    ".copier-answers.depot.yml",
]
DEPOT_PYTHON = [
    "pyproject.toml", "justfile", ".python-version", "src/projet_essai/__init__.py",
    "tests/test_socle.py", ".github/workflows/ci.yml",
]
PY_TYPED = "src/projet_essai/py.typed"
# Ce qu'un préréglage pour débuter n'a pas, et ce qu'il a à la place.
SANS_DEBUTANT = {"pyproject.toml": ["hypothesis", "TID251", "pyarrow", "\nstrict = true"],
                 ".github/workflows/ci.yml": ["extras"], "justfile": ["strict"],
                 "CLAUDE.md": ["Un objet invalide", "mode strict", "(`hypothesis`)",
                               "à la fin de chaque session de travail"]}
AVEC_DEBUTANT = {"pyproject.toml": ["TID252", "check_untyped_defs = true"],
                 "CLAUDE.md": ["accepté d'office", "pas exigé"],
                 "docs/ROADMAP.md": ["Les trois principes qui gouvernent l'ordre", "**Tranches verticales** :"]}
AVEC_COMPLET = {"pyproject.toml": ["hypothesis", "TID251", "strict = true"],
                ".github/workflows/ci.yml": ["extras"], "CLAUDE.md": ["Un objet invalide", "mode strict"]}
SANS_COMPLET = {"pyproject.toml": ["check_untyped_defs"], "CLAUDE.md": ["accepté d'office"]}
DEPOT_DONNEES = [
    ".env.example", ".claude/settings.json", "scripts/hooks/proteger_donnees.py",
]
DEPOT_GROUPE = [
    "CONTRIBUTING.md", ".github/pull_request_template.md", ".github/CODEOWNERS",
    "docs/LIVRAISONS.md", "docs/RELIRE_UNE_PR.md",
]
DEPOT_ANALYSE = ["docs/analyse/CHARTE.md", "docs/analyse/QUESTIONS.md"]


def espace_socle(s: str = "") -> list[str]:
    c = f"conception{s}"
    return [
        f"{c}/CONTEXTE.md", f"{c}/LECONS_PROJET.md", f"{c}/MACHINE_PROJET.md", f"{c}/00_LISEZ_MOI.md",
        f"{c}/REMONTEES_KIT.md", f"{c}/passations/LISEZ_MOI.md",
        f"{c}/kit/METHODE.md", f"{c}/kit/MODELES_ET_EFFORTS.md", f"{c}/kit/LECONS.md",
        f"{c}/kit/MACHINE.md", f"{c}/kit/COMMANDES.md", f"{c}/kit/VOCABULAIRE.md", f"{c}/kit/IDIOMES_DEV.md",
        f"{c}/kit/gabarits/LISEZ_MOI.md", f"{c}/kit/gabarits/BRIEF_JALON.md",
        f"{c}/kit/gabarits/CLOTURE_CONTEXTE.md",
        f"{c}/kit/gabarits/OUVERTURES_A.md", f"{c}/kit/gabarits/CONSIGNE_CODE.md",
        f"{c}/kit/gabarits/FEU_VERT_PLAN.md", f"{c}/kit/gabarits/CORRECTIFS.md",
        f"{c}/kit/gabarits/ARBITRAGE.md", f"{c}/kit/gabarits/REVUE_PR.md",
        f"{c}/kit/prompts/PREMIERE_A.md", f"{c}/kit/prompts/CONSOLIDATION_KIT.md",
        f"{c}/kit/prompts/SESSION_EXPLICATION.md",
        f"v_for_cowork{s}/LISEZ_MOI.md",
    ]


ESPACE_RACINE = [
    "00_LISEZ_MOI_ESPACE.md", "outils/espace.py", "outils/diff_pr.py", "outils/miroir.py",
    "outils/compte_rendu_pr.py", "outils/revue_pr.py", "outils/tete_pr.py",
    "outils/_commun.py", "outils/lire_section.py", "outils/mesurer_noyau.py", "outils/verifier_deplacement.py",
]
OUTIL_PISTES = "outils/extraire_piste.py"
# Ce qu'un projet sans le module pistes ne cite nulle part : il n'a pas ces fichiers.
CITES_PISTES = ["PISTES.md", "NOTE_PISTE", "RELAIS.md", "MESSAGE_FUSION_PISTE", "extraire_piste"]


def espace_relectures(s: str = "") -> list[str]:
    c = f"conception{s}"
    return [
        f"v_for_cowork{s}/06_BRIEF_RELECTURE_PR.md", f"v_for_cowork{s}/07_BRIEF_RELECTURE_ARTEFACT.md",
        f"{c}/kit/gabarits/ANNEXE_B.md", f"{c}/kit/gabarits/ANNEXE_C.md",
        f"{c}/kit/gabarits/DEPART_B.md", f"{c}/kit/gabarits/DEMARRAGE_C.md",
    ]


def espace_pistes(s: str = "") -> list[str]:
    g = f"conception{s}/kit/gabarits"
    return [f"conception{s}/kit/PISTES.md", f"{g}/RELAIS.md", f"{g}/REPONSE_RELAIS.md",
            f"{g}/MESSAGE_FUSION_PISTE.md", f"{g}/NOTE_PISTE.md"]


def espace_archives(s: str = "") -> list[str]:
    return [f"archives_conception{s}/LISEZ_MOI.md", f"conception{s}/INVENTAIRE_ARCHIVES.md",
            f"conception{s}/kit/ARCHIVES.md"]


def espace_expert(s: str = "") -> list[str]:
    return [f"conception{s}/kit/EXPERT.md", f"conception{s}/kit/gabarits/PASSE_EXPERTE.md",
            f"conception{s}/kit/gabarits/SESSION_A_PART.md"]


SCENARIOS: list[dict] = [
    {"nom": "depot-solo-leger", "data": {"couche": "depot", "preset": "solo-leger"},
     "presents": DEPOT_SOCLE + DEPOT_PYTHON,
     "absents": DEPOT_DONNEES + DEPOT_GROUPE + DEPOT_ANALYSE + [PY_TYPED], "python": True, "souple": True,
     "update": True, "contient": AVEC_DEBUTANT, "sans": SANS_DEBUTANT},
    {"nom": "depot-groupe", "data": {"couche": "depot", "preset": "groupe-scolaire"},
     "presents": DEPOT_SOCLE + DEPOT_PYTHON + DEPOT_GROUPE,
     "absents": DEPOT_DONNEES + DEPOT_ANALYSE + [PY_TYPED], "python": True, "souple": True,
     # une entrée de JOURNAL par PR ferait un conflit à chaque fusion
     "contient": {**AVEC_DEBUTANT, "docs/JOURNAL.md": ["**Une entrée par livraison**"],
                  "docs/LIVRAISONS.md": ["docs/JOURNAL.md"], "CONTRIBUTING.md": ["docs/JOURNAL.md"]},
     "sans": {**SANS_DEBUTANT, "docs/JOURNAL.md": ["par session"]}},
    {"nom": "depot-perso-standard", "data": {"couche": "depot", "preset": "perso-standard"},
     "presents": DEPOT_SOCLE + DEPOT_PYTHON + [PY_TYPED],
     "absents": DEPOT_DONNEES + DEPOT_GROUPE + DEPOT_ANALYSE, "python": True,
     "contient": AVEC_COMPLET, "sans": SANS_COMPLET},
    {"nom": "depot-perso-complet", "data": {"couche": "depot", "preset": "perso-complet",
     # une description longue : le dépôt généré doit quand même passer `just check` (E501)
     "description": "Une description volontairement longue, comme celle d'un vrai projet pour un client, "
                    "qui dépasse largement la longueur de ligne de ruff une fois dans la docstring."},
     "presents": DEPOT_SOCLE + DEPOT_PYTHON + DEPOT_DONNEES + [PY_TYPED, "tests/test_proteger_donnees.py"],
     "absents": DEPOT_GROUPE + DEPOT_ANALYSE, "python": True,
     "contient": AVEC_COMPLET, "sans": SANS_COMPLET},
    {"nom": "depot-autre-analyse", "data": {"couche": "depot", "preset": "personnalise",
                                             "modules_choisis": ["analyse-donnees"], "langage": "autre"},
     "presents": DEPOT_SOCLE + DEPOT_ANALYSE,
     "absents": DEPOT_PYTHON + [PY_TYPED] + DEPOT_DONNEES + DEPOT_GROUPE},
    {"nom": "espace-solo-leger", "data": {"couche": "espace", "preset": "solo-leger"},
     "presents": espace_socle() + ESPACE_RACINE,
     "absents": espace_relectures() + espace_archives() + espace_expert() + espace_pistes()
     + ["relecture/LISEZ_MOI.md", "conception/kit/MUTATION.md", "outils/clone_c.py", "outils/archiver.py",
        OUTIL_PISTES],
     "jamais_cite": CITES_PISTES,
     # sans relectures : une clôture courte, et les 7 titres que lit extraire_piste.py
     "contient": {"conception/CONTEXTE.md": ["## 7. Prochaine séance"],
                  "conception/kit/gabarits/CLOTURE_CONTEXTE.md": ["**Prochaine étape**"],
                  "conception/kit/gabarits/BRIEF_JALON.md": ["(facultatif)"],
                  "conception/kit/IDIOMES_DEV.md": ["le niveau *socle* seul"]},
     "sans": {"conception/CONTEXTE.md": ["METHODE.md` en entier"],
              "conception/kit/gabarits/CLOTURE_CONTEXTE.md": ["Ce qu'a fait", "États d'avant"],
              "conception/kit/gabarits/OUVERTURES_A.md": ["METHODE.md` en entier"],
              # hypothesis n'est pas installé : pytest s'arrêterait sur cette option
              "conception/kit/gabarits/BRIEF_JALON.md": ["--hypothesis-seed"],
              "conception/kit/prompts/PREMIERE_A.md": ["METHODE.md` ; le § 0"]},
     "refus": {"piste": "analyse"}},
    {"nom": "espace-perso-standard", "data": {"couche": "espace", "preset": "perso-standard", "public": True},
     "presents": espace_socle() + ESPACE_RACINE + espace_relectures() + espace_pistes()
     + ["relecture/LISEZ_MOI.md", "outils/clone_c.py", OUTIL_PISTES],
     "absents": espace_archives() + espace_expert() + ["conception/kit/MUTATION.md", "outils/archiver.py"],
     # dépôt public : les parades anonymes sont données ; avec relectures, la clôture complète
     "contient": {"conception/kit/MACHINE.md": ["ETAT_DISTANT.txt", "API publique répond sans jeton"],
                  "conception/kit/gabarits/CLOTURE_CONTEXTE.md": ["Ce qu'a fait la", "États d'avant"]},
     "sans": {"conception/kit/MACHINE.md": ["Le dépôt est privé"]}},
    {"nom": "espace-perso-complet", "data": {"couche": "espace", "preset": "perso-complet"},
     "presents": espace_socle() + ESPACE_RACINE + espace_relectures() + espace_archives()
     + espace_expert() + espace_pistes() + ["relecture/LISEZ_MOI.md", "conception/kit/MUTATION.md",
                                            "outils/clone_c.py", "outils/archiver.py", OUTIL_PISTES],
     "absents": [], "recopy": True, "budget_mord": True,
     # dépôt privé (défaut) : pas de parade anonyme
     "contient": {"conception/kit/MACHINE.md": ["ETAT_DISTANT.txt", "Le dépôt est privé"]},
     "sans": {"conception/kit/MACHINE.md": ["API publique répond sans jeton"]},
     # puis une piste « analyse » dans la même racine
     "piste": {"data": {"couche": "espace", "preset": "perso-complet", "piste": "analyse"},
               "presents": espace_socle("_analyse") + espace_relectures("_analyse")
               + espace_archives("_analyse") + espace_expert("_analyse") + espace_pistes("_analyse")
               + [".copier-answers.espace_analyse.yml"],
               "absents": []}},
    # Le module pistes sans relectures : extraire_piste.py doit lire le CONTEXTE de ce préréglage.
    {"nom": "espace-pistes-seules", "data": {"couche": "espace", "preset": "personnalise",
                                              "modules_choisis": ["pistes"]},
     "presents": espace_socle() + ESPACE_RACINE + espace_pistes() + [OUTIL_PISTES],
     "absents": espace_relectures() + espace_archives() + espace_expert()
     + ["relecture/LISEZ_MOI.md", "outils/clone_c.py"],
     "piste": {"data": {"couche": "espace", "preset": "personnalise", "modules_choisis": ["pistes"],
                        "piste": "analyse"},
               "presents": espace_socle("_analyse") + espace_pistes("_analyse")
               + [".copier-answers.espace_analyse.yml"],
               "absents": espace_relectures("_analyse")}},
]


class Echec(Exception):
    pass


SOURCE: Path | None = None


def preparer_source(racine: Path) -> Path:
    """Instantané du kit tel qu'il est sur le disque (modifications non commitées comprises),
    dans un dépôt git temporaire : on teste ce qu'on a sous les yeux, pas le dernier tag."""
    src = racine / "_kit"
    shutil.copytree(KIT, src, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.name=essai", "-c", "user.email=essai@example.invalid",
                 "commit", "-qm", "instantané"]):
        subprocess.run(cmd, cwd=src, check=True, capture_output=True)
    return src


def generer(dest: Path, data: dict) -> None:
    assert SOURCE is not None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_copy(str(SOURCE), dest, data={**BASE, **data}, defaults=True, vcs_ref="HEAD",
                 quiet=True, unsafe=False, overwrite=True)


def verifier_structure(dest: Path, presents: list[str], absents: list[str]) -> list[str]:
    erreurs = [f"manque : {p}" for p in presents if not (dest / p).is_file()]
    erreurs += [f"en trop : {a}" for a in absents if (dest / a).exists()]
    return erreurs


def verifier_filets(rel: str, texte: str) -> list[str]:
    """Une condition mal fermée peut manger la ligne vide d'avant un filet, sans rien casser d'autre."""
    erreurs, dans_code, avant = [], False, ""
    for n, ligne in enumerate(texte.splitlines(), 1):
        if ligne.lstrip().startswith("```"):
            dans_code = not dans_code
        elif not dans_code and ligne == "---" and avant.strip():
            erreurs.append(f"filet collé au texte : {rel}:{n}")
        avant = ligne
    return erreurs


def verifier_contenu(dest: Path) -> list[str]:
    erreurs = []
    for d in sorted(dest.rglob("*")):
        if d.is_dir() and ".git" not in d.parts and not any(d.iterdir()):
            erreurs.append(f"dossier vide : {d.relative_to(dest).as_posix()}")
    for f in sorted(dest.rglob("*")):
        if not f.is_file() or ".git" in f.parts:
            continue
        rel = f.relative_to(dest).as_posix()
        if f.suffix == ".jinja":
            erreurs.append(f"fichier .jinja non rendu : {rel}")
        try:
            texte = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if f.name.endswith(".yml") and "copier-answers" in f.name:
            continue
        if f.suffix == ".md":
            erreurs += verifier_filets(rel, texte)
        for n, ligne in enumerate(texte.splitlines(), 1):
            if DELIMITEURS.search(ligne):
                erreurs.append(f"délimiteur restant : {rel}:{n}: {ligne.strip()[:90]}")
    return erreurs


def verifier_renvois(dest: Path) -> list[str]:
    """Chaque renvoi à une entrée de kit/MACHINE.md existe : une entrée retirée ne laisse pas de trou."""
    machine = dest / "conception" / "kit" / "MACHINE.md"
    if not machine.is_file():
        return []
    connues = set(re.findall(r"^- \*\*([A-Z]+-\d+) —", machine.read_text(encoding="utf-8"), re.M))
    erreurs = []
    for f in sorted(dest.rglob("*")):
        if not f.is_file() or f.suffix not in {".md", ".py"} or {"perso", ".git"} & set(f.parts):
            continue
        for n, ligne in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for renvoi in RENVOIS.findall(ligne):
                if renvoi not in connues:
                    erreurs.append(f"renvoi sans entrée : {f.relative_to(dest).as_posix()}:{n}: {renvoi}")
    return erreurs


def verifier_regles(dest: Path) -> list[str]:
    """`CLAUDE.md` promet des numéros stables : les règles 1 à 8 sont là, dans tous les préréglages."""
    claude = dest / "CLAUDE.md"
    if not claude.is_file():
        return []
    partie = claude.read_text(encoding="utf-8").split("## Règles dures")[1].split("\n---")[0]
    numeros = re.findall(r"^(\d+)\. ", partie, re.M)
    return [] if numeros == list("12345678") else [f"règles de CLAUDE.md : {numeros}"]


def verifier_budget_ouverture(dest: Path, piste: str | None = None) -> list[str]:
    """La lecture d'ouverture d'une A tient dans son budget : `outils/mesurer_noyau.py` le dit."""
    if not (dest / "outils" / "mesurer_noyau.py").is_file():
        return []
    r = lancer_script(dest, "outils/mesurer_noyau.py", *(["--piste", piste] if piste else []))
    if r.returncode:
        return [f"budget d'ouverture{f' (piste {piste})' if piste else ''} : {(r.stdout + r.stderr).strip()[-500:]}"]
    return []


def verifier_budget_mord(dest: Path) -> list[str]:
    """Le garde-fou mord : un CONTEXTE gonflé au-delà du budget fait échouer la mesure."""
    contexte = dest / "conception" / "CONTEXTE.md"
    avant = contexte.read_bytes()
    contexte.write_bytes(avant + b"LIGNE DE TROP\n" * 4000)
    try:
        r = lancer_script(dest, "outils/mesurer_noyau.py")
    finally:
        contexte.write_bytes(avant)
    if r.returncode == 1 and "budget noyau dépassé" in r.stdout:
        return []
    return [f"un CONTEXTE gonflé ne fait pas échouer la mesure : code {r.returncode}, {r.stdout.strip()[-300:]}"]


def verifier_jamais_cite(dest: Path, noms: list[str]) -> list[str]:
    """Un fichier qu'un préréglage n'a pas n'y est cité nulle part : un renvoi ne mène pas dans le vide."""
    erreurs = []
    for f in sorted(dest.rglob("*")):
        if not f.is_file() or f.suffix not in {".md", ".py"} or ".git" in f.parts:
            continue
        for n, ligne in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            erreurs += [f"cite un fichier absent : {f.relative_to(dest).as_posix()}:{n}: {nom}"
                        for nom in noms if nom in ligne]
    return erreurs


def verifier_refus(racine: Path, data: dict) -> list[str]:
    """Une piste sans le module pistes est refusée, avec un message qui dit quoi faire."""
    try:
        generer(racine / "refus", data)
    except Exception as exc:  # noqa: BLE001 — Copier lève selon la version ; seul le message compte
        return [] if "module pistes" in str(exc) else [f"refus sans explication : {exc}"]
    return ["une piste est acceptée sans le module pistes"]


def verifier_chemins(dest: Path) -> list[str]:
    """`racine` vaut `~/…` par défaut : les scripts doivent recevoir un chemin absolu."""
    if not (dest / "outils" / "espace.py").is_file():
        return []
    code = "import sys; sys.path.insert(0, 'outils'); import espace; print(espace.depot_travail())"
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    r = subprocess.run(["uv", "run", "--quiet", "python", "-c", code], capture_output=True, text=True,
                       cwd=dest, env=env)
    chemin = r.stdout.strip()
    if r.returncode or "~" in chemin or not Path(chemin).is_absolute():
        return [f"espace.depot_travail() ne donne pas un chemin absolu : {chemin or r.stderr[-300:]}"]
    return []


def verifier_schemas() -> list[str]:
    """Les schémas des pages sont ceux de docs/schemas : une source qui dérive ne sert à rien."""
    pages = [KIT / "README.md", *sorted((KIT / "docs").glob("*.md"))]
    blocs = {b.strip() for page in pages for b in SCHEMA.findall(page.read_text(encoding="utf-8"))}
    sources = {f.name: f.read_text(encoding="utf-8").strip() for f in (KIT / "docs" / "schemas").glob("*.mmd")}
    erreurs = [f"schéma sans page : docs/schemas/{nom}" for nom, s in sources.items() if s not in blocs]
    erreurs += [f"schéma sans source .mmd : {b.splitlines()[1].strip()}" for b in blocs if b not in sources.values()]
    return erreurs


def verifier_termes() -> list[str]:
    """Aucun terme privé dans le kit. La liste vit hors du dépôt : elle ne peut pas être publique."""
    liste = os.environ.get("KIT_TERMES_PRIVES")
    if not liste:
        return []
    termes = [ligne.strip() for ligne in Path(liste).read_text(encoding="utf-8").splitlines()
              if ligne.strip() and not ligne.startswith("#")]
    motif = re.compile(r"\b(?:" + "|".join(re.escape(terme) for terme in termes) + r")\b", re.I)
    sortie = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=KIT, capture_output=True,
                            text=True, encoding="utf-8", check=True).stdout
    erreurs = []
    for rel in sortie.splitlines():
        f = KIT / rel
        if "perso" in Path(rel).parts or not f.is_file():
            continue
        try:
            texte = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, ligne in enumerate(texte.splitlines(), 1):
            if motif.search(ligne):
                erreurs.append(f"terme privé : {rel}:{n}: {ligne.strip()[:90]}")
    return erreurs


def verifier_textes(dest: Path, contient: dict, sans: dict) -> list[str]:
    """Des passages qui dépendent des réponses (ex. dépôt public ou privé)."""
    erreurs = []
    for rel, morceaux in contient.items():
        texte = (dest / rel).read_text(encoding="utf-8")
        erreurs += [f"{rel} : « {m} » manque" for m in morceaux if m not in texte]
    for rel, morceaux in sans.items():
        texte = (dest / rel).read_text(encoding="utf-8")
        erreurs += [f"{rel} : « {m} » ne devrait pas y être" for m in morceaux if m in texte]
    return erreurs


def verifier_outils(dest: Path) -> list[str]:
    erreurs = []
    outils = dest / "outils"
    if not outils.is_dir():
        return erreurs
    for script in sorted(outils.glob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as erreur:
            erreurs.append(f"ne compile pas : {script.name} : {erreur}")
            continue
        if script.name == "espace.py":
            continue
        r = lancer_script(dest, f"outils/{script.name}", "--help")
        if r.returncode:
            erreurs.append(f"--help échoue : {script.name} : {(r.stdout + r.stderr).strip()[-300:]}")
    return erreurs


def lancer_script(dest: Path, script: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Lance un script d'outils/ comme un utilisateur : `uv run outils/x.py …`, depuis la racine de l'espace.

    Jamais par `sys.executable` : c'est l'interpréteur jetable que uv a créé pour ce banc, et un
    antivirus peut refuser qu'on le relance (kit/MACHINE.md, AV-3).
    """
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    return subprocess.run(["uv", "run", "--quiet", script, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=dest, env=env)


def verifier_extraction(dest: Path, piste: str) -> list[str]:
    """Le CONTEXTE généré suit le plan fixe qu'attend outils/extraire_piste.py, et les leçons du projet suivent."""
    lecons = dest / "conception" / "LECONS_PROJET.md"
    avant = lecons.read_bytes()
    lecons.write_bytes(avant + "\nLEÇON DE LA RÉFÉRENCE\n".encode())
    try:
        r = lancer_script(dest, "outils/extraire_piste.py", "--vers", piste)
    finally:
        lecons.write_bytes(avant)
    if r.returncode:
        return [f"extraire_piste.py échoue sur le CONTEXTE généré : {(r.stdout + r.stderr).strip()[-400:]}"]
    sortie = dest / f"conception_{piste}" / "depuis_principale"
    if not (sortie / "LISEZ_MOI.md").is_file():
        return ["extraire_piste.py n'a pas écrit son LISEZ_MOI.md"]
    if "LEÇON DE LA RÉFÉRENCE" not in (sortie / "REGLES_PRINCIPALE_3_LECONS.md").read_text(encoding="utf-8"):
        return ["extraire_piste.py n'a pas repris LECONS_PROJET.md"]
    return []


GIT_ID = ["-c", "user.name=essai", "-c", "user.email=essai@example.invalid"]


def verifier_update(racine: Path, data: dict) -> list[str]:
    """`copier update` d'un dépôt : une nouveauté du kit arrive, une modification locale reste.
    Sur une copie privée de l'instantané, pour ne pas toucher aux autres scénarios."""
    assert SOURCE is not None
    src = racine / "_kit_update"
    shutil.copytree(SOURCE, src)
    dest = racine / "depot-update"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_copy(str(src), dest, data={**BASE, **data}, defaults=True, vcs_ref="HEAD", quiet=True)
    def git(cwd: Path, *args: str) -> None:
        subprocess.run(["git", *GIT_ID, *args], cwd=cwd, check=True, capture_output=True)
    git(dest, "init", "-q")
    git(dest, "add", "-A")
    git(dest, "commit", "-qm", "squelette")
    claude = dest / "CLAUDE.md"
    claude.write_text(claude.read_text(encoding="utf-8") + "\nRÈGLE LOCALE DU PROJET\n", encoding="utf-8")
    git(dest, "commit", "-qam", "local")
    agents = src / "depot" / "AGENTS.md.jinja"
    agents.write_text(agents.read_text(encoding="utf-8") + "\nNOUVEAUTÉ DU KIT\n", encoding="utf-8")
    git(src, "commit", "-qam", "kit v+1")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_update(dest, answers_file=".copier-answers.depot.yml", defaults=True, overwrite=True,
                   quiet=True, vcs_ref="HEAD", unsafe=False)
    erreurs = []
    if "NOUVEAUTÉ DU KIT" not in (dest / "AGENTS.md").read_text(encoding="utf-8"):
        erreurs.append("copier update n'a pas apporté la nouveauté du kit (AGENTS.md)")
    if "RÈGLE LOCALE DU PROJET" not in claude.read_text(encoding="utf-8"):
        erreurs.append("copier update a perdu une modification locale (CLAUDE.md)")
    return erreurs


def verifier_recopy(dest: Path) -> list[str]:
    erreurs = []
    vivant = dest / "conception" / "CONTEXTE.md"
    kit = dest / "conception" / "kit" / "METHODE.md"
    vivant.write_text(vivant.read_text(encoding="utf-8") + "\nLIGNE AJOUTÉE PAR UNE A\n", encoding="utf-8")
    kit.unlink()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_recopy(dest, answers_file=".copier-answers.espace.yml", defaults=True, overwrite=True,
                   quiet=True, vcs_ref="HEAD")
    if "LIGNE AJOUTÉE PAR UNE A" not in vivant.read_text(encoding="utf-8"):
        erreurs.append("recopy a écrasé un fichier vivant (CONTEXTE.md)")
    if not kit.is_file():
        erreurs.append("recopy n'a pas rétabli un fichier du kit (kit/METHODE.md)")
    return erreurs


def verifier_python(dest: Path, souple: bool) -> list[str]:
    if not shutil.which("uv") or not shutil.which("just"):
        return ["--complet demande uv et just dans le PATH"]
    # Du code de maths doit passer : majuscules, `l`, lettres grecques.
    (dest / "src" / "projet_essai" / "exemple_maths.py").write_text(MODULE_MATHS, encoding="utf-8", newline="\n")
    if souple:
        (dest / "src" / "projet_essai" / "exemple_souple.py").write_text(MODULE_SOUPLE, encoding="utf-8", newline="\n")
    # --locked : ce que lance la CI au premier envoi.
    for cmd in (["git", "init", "-q"], ["uv", "sync", "-q"], ["uv", "sync", "-q", "--locked"], ["just", "check"]):
        r = subprocess.run(cmd, cwd=dest, capture_output=True, text=True)
        if r.returncode:
            return [f"{' '.join(cmd)} échoue :\n{(r.stdout + r.stderr)[-1500:]}"]
    return []


def lieu_erreur(exc: BaseException) -> str:
    """La dernière ligne du banc traversée par l'exception, et la commande lancée s'il y en a une."""
    ici = Path(__file__).resolve()
    lignes = [f for f in traceback.extract_tb(exc.__traceback__) if Path(f.filename).resolve() == ici]
    lieu = f" — tester_kit.py:{lignes[-1].lineno} : {lignes[-1].line}" if lignes else ""
    cmd = getattr(exc, "cmd", None) or getattr(exc, "filename", None)
    return lieu + (f" — {cmd}" if cmd else "")


def main() -> int:
    # Sous Windows, une sortie redirigée n'est pas en UTF-8 : un « ✗ » y ferait planter le bilan.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--complet", action="store_true", help="uv sync et just check dans les dépôts Python")
    p.add_argument("--garder", action="store_true", help="garder les projets générés")
    p.add_argument("--seul", help="ne jouer que ce scénario")
    args = p.parse_args()

    global SOURCE
    # Sous Windows, un antivirus peut bloquer un python.exe neuf dans %TEMP% (kit/MACHINE.md, AV-3) :
    # les projets d'essai se créent à côté du kit.
    # Sous macOS, le dossier temporaire passe par un lien (/var → /private/var) : sans resolve(),
    # `copier update` compare ce chemin à celui, résolu, que donne git, et plante.
    racine = Path(tempfile.mkdtemp(prefix="essai_kit_", dir=KIT.parent if os.name == "nt" else None)).resolve()
    SOURCE = preparer_source(racine)
    bilan: list[tuple[str, list[str]]] = [("kit", verifier_schemas() + verifier_termes())]
    for sc in SCENARIOS:
        if args.seul and sc["nom"] != args.seul:
            continue
        dest = racine / sc["nom"]
        erreurs: list[str] = []
        try:
            generer(dest, sc["data"])
            erreurs += verifier_structure(dest, sc["presents"], sc["absents"])
            if "piste" in sc:
                generer(dest, sc["piste"]["data"])
                erreurs += verifier_structure(dest, sc["piste"]["presents"], sc["piste"]["absents"])
                erreurs += verifier_extraction(dest, sc["piste"]["data"]["piste"])
            erreurs += verifier_textes(dest, sc.get("contient", {}), sc.get("sans", {}))
            erreurs += verifier_contenu(dest)
            erreurs += verifier_renvois(dest)
            erreurs += verifier_regles(dest)
            erreurs += verifier_budget_ouverture(dest)
            if "piste" in sc:
                erreurs += verifier_budget_ouverture(dest, sc["piste"]["data"]["piste"])
            if sc.get("budget_mord"):
                erreurs += verifier_budget_mord(dest)
            erreurs += verifier_jamais_cite(dest, sc.get("jamais_cite", []))
            if "refus" in sc:
                erreurs += verifier_refus(racine, {**sc["data"], **sc["refus"]})
            erreurs += verifier_outils(dest)
            erreurs += verifier_chemins(dest)
            if sc.get("recopy"):
                erreurs += verifier_recopy(dest)
            if sc.get("update"):
                erreurs += verifier_update(racine, sc["data"])
            if args.complet and sc.get("python"):
                erreurs += verifier_python(dest, sc.get("souple", False))
        except Exception as exc:  # noqa: BLE001 — un scénario qui plante est un échec, pas un arrêt
            erreurs.append(f"{type(exc).__name__}: {exc}{lieu_erreur(exc)}")
        bilan.append((sc["nom"], erreurs))

    print(f"\nProjets générés dans {racine}\n")
    total = 0
    for nom, erreurs in bilan:
        statut = "OK " if not erreurs else "ÉCHEC"
        print(f"[{statut}] {nom} ({len(erreurs)} erreur(s))")
        for e in erreurs[:30]:
            print(f"        ✗ {e}")
        if len(erreurs) > 30:
            print(f"        ✗ … et {len(erreurs) - 30} autre(s)")
        total += len(erreurs)
    if not args.garder:
        if not retirer(racine):
            print(f"\n{racine} n'a pas pu être effacé en entier (fichier encore tenu ?) : le supprimer à la main.")
    print("\nTout passe." if total == 0 else f"\n{total} erreur(s).")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
