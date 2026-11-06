# /// script
# requires-python = ">=3.10"
# ///
"""Extrait les règles propres au projet d'une piste (§§ 1, 2, 3 et 6 de son CONTEXTE.md)
pour une autre piste ; ne recopie jamais son état (§§ 4, 5 et 7).

    uv run outils/extraire_piste.py --vers analyse                    (depuis la piste principale)
    uv run outils/extraire_piste.py --vers principale --depuis analyse
    uv run outils/extraire_piste.py --empreinte «fichier»              (recalcule une empreinte)

Lit conception<suffixe de la référence>/CONTEXTE.md. Écrit dans
conception_<piste>/depuis_<référence>/ un fichier par section extraite
(REGLES_<RÉFÉRENCE>_<n>_<NOM>.md), puis LISEZ_MOI.md, **écrit en dernier** : s'il manque,
le dernier lancement n'a pas abouti. Quand le relancer, et ce que l'A en fait :
conception/kit/PISTES.md.

Garanties :
- tout est vérifié avant la première écriture : un titre du plan absent ou en double, un
  titre de niveau 1 ou 2 hors du plan, un bloc de code jamais fermé, une source illisible
  arrêtent tout, sans rien écrire ;
- les §§ 4, 5 et 7 ne sont jamais recopiés ni affichés : le script parcourt le fichier pour
  y repérer les titres, mais ne garde aucune ligne de ces sections (le fichier entier n'entre
  que dans l'empreinte de la source) ;
- un fichier du dossier de sortie que le script n'écrit pas est signalé, jamais supprimé ;
- UTF-8 sans BOM, fins de ligne LF, quels que soient le BOM et les fins de ligne de la source ;
- relancé sur une source inchangée, il redonne les mêmes empreintes du contenu.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import espace

PLAN = {
    1: "1. Où sont les choses",
    2: "2. Qui fait quoi — propre au projet",
    3: "3. Leçons propres au projet",
    4: "4. État d'avancement",
    5: "5. Points ouverts, avec leur déclencheur",
    6: "6. Particularités de la machine propres au projet",
    7: "7. Prochaine séance",
}
"""Les titres de niveau 2 de CONTEXTE.md, fixes et identiques dans toutes les pistes."""

EXTRAITES = {
    1: ("OU_SONT_LES_CHOSES", "à l'ouverture"),
    2: ("QUI_FAIT_QUOI", "à l'ouverture"),
    3: ("LECONS", "avant le premier brief de la piste ; ensuite, quand son empreinte change"),
    6: ("MACHINE", f"avant de donner une commande à {espace.HUMAIN}"),
}
"""Les sections recopiées (règles propres au projet). Jamais 4, 5 ni 7 : c'est l'état."""

LISEZ_MOI = "LISEZ_MOI.md"
TEMPORAIRE = ".extraire_tmp"
SEPARATEUR = "---"
GENERE_PAR = "<!-- Généré par outils/extraire_piste.py (kit-projet). Ne pas modifier : relancer le script. -->"
NOM_PISTE = re.compile(r"^[a-z][a-z0-9-]*$")
TITRE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
CLOTURE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
FILET = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
RECALCUL = "uv run outils/extraire_piste.py --empreinte «fichier»"
"""La commande à lancer pour recalculer l'empreinte du contenu d'un fichier."""


def cle(titre: str) -> str:
    """Clé de comparaison d'un titre : à la typographie près (apostrophes, tirets, espaces)."""
    t = unicodedata.normalize("NFC", titre)
    t = re.sub("[‘’ʼ]", "'", t)
    t = re.sub("[‐-―−-]", "—", t)
    return re.sub(r"\s+", " ", t).strip()


def analyser(texte: str) -> tuple[dict[int, list[str]], dict[int, list[str]], list[str], list[str]]:
    """Découpe le CONTEXTE (fins de ligne déjà ramenées à LF).

    Renvoie les lignes de chaque section extraite, les titres de ses sous-sections, les
    erreurs (vide si tout va bien) et les avertissements.
    """
    attendus = {cle(titre): n for n, titre in PLAN.items()}
    vus: dict[int, list[int]] = {n: [] for n in PLAN}
    lignes = {n: [] for n in EXTRAITES}
    sous_sections: dict[int, list[str]] = {n: [] for n in EXTRAITES}
    hors_plan: list[tuple[int, str]] = []
    autres_titres: list[str] = []
    courante: int | None = None
    plan_commence = False
    cloture: tuple[str, int, int] | None = None

    for numero, ligne in enumerate(texte.split("\n"), start=1):
        niveau, titre = 0, ""
        if cloture is not None:
            car, longueur, _ = cloture
            if re.match(rf"^ {{0,3}}{re.escape(car)}{{{longueur},}}[ \t]*$", ligne):
                cloture = None
        else:
            m = CLOTURE.match(ligne)
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                cloture = (m.group(1)[0], len(m.group(1)), numero)
            else:
                t = TITRE.match(ligne)
                if t:
                    niveau, titre = len(t.group(1)), (t.group(2) or "").strip()

        if niveau in (1, 2):
            n = attendus.get(cle(titre)) if niveau == 2 else None
            if n is not None:
                vus[n].append(numero)
                courante, plan_commence = n, True
            elif plan_commence:
                hors_plan.append((numero, ("#" * niveau) + " " + titre))
                courante = None
            else:
                autres_titres.append(titre)
        elif niveau == 3 and courante in EXTRAITES:
            sous_sections[courante].append(titre)
        if courante in EXTRAITES:
            lignes[courante].append(ligne)

    erreurs = []
    candidats = [t for _, t in hors_plan] + autres_titres
    for n, titre in PLAN.items():
        if not vus[n]:
            proche = difflib.get_close_matches(titre, [c.lstrip("# ") for c in candidats], n=1, cutoff=0.5)
            indice = f" ; le titre voisin le plus proche : « {proche[0]} »" if proche else ""
            erreurs.append(f"titre du plan absent : « ## {titre} »{indice}")
        elif len(vus[n]) > 1:
            erreurs.append(f"titre en double : « ## {titre} » (lignes {', '.join(map(str, vus[n]))})")
    for numero, titre in hors_plan:
        erreurs.append(
            f"titre hors du plan fixe, ligne {numero} : « {titre} » (un passage de plus se range "
            "sous un titre ### de la section qui le porte)"
        )
    if cloture is not None:
        erreurs.append(f"bloc de code ouvert ligne {cloture[2]}, jamais fermé : les titres qui suivent sont invisibles")

    avertissements = []
    debuts = [vus[n][0] for n in PLAN if len(vus[n]) == 1]
    if not erreurs and debuts != sorted(debuts):
        avertissements.append("les titres du plan ne sont pas dans l'ordre 1 à 7 (sans effet sur l'extraction)")
    return lignes, sous_sections, erreurs, avertissements


def corps_de_section(lignes: list[str]) -> str:
    """Les lignes de la section, sans les lignes vides ni le filet (---) qui la terminent."""
    fin = len(lignes)
    while fin and not lignes[fin - 1].strip():
        fin -= 1
    if fin and FILET.match(lignes[fin - 1]):
        fin -= 1
        while fin and not lignes[fin - 1].strip():
            fin -= 1
    return "\n".join(lignes[:fin]) + "\n"


def empreinte(texte: str) -> str:
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


def empreinte_contenu(texte: str) -> str | None:
    """SHA-256 du texte sous la ligne `---` de l'en-tête, sans lignes vides de bord."""
    lignes = texte.split("\n")
    if SEPARATEUR not in lignes:
        return None
    k = lignes.index(SEPARATEUR)
    return empreinte("\n".join(lignes[k + 1 :]).strip("\n") + "\n")


def afficher_empreinte(fichier: Path) -> None:
    """Affiche l'empreinte du contenu d'un fichier déjà extrait : ses 16 premiers caractères."""
    if not fichier.is_file():
        sys.exit(f"{fichier} introuvable.")
    h = empreinte_contenu(fichier.read_text(encoding="utf-8"))
    if h is None:
        sys.exit(f"{fichier} n'a pas de ligne `{SEPARATEUR}` : ce n'est pas un fichier extrait.")
    print(h[:16])


def chemin_relatif(chemin: Path) -> str:
    """Chemin relatif à la racine de l'espace, écrit avec des `/` sur tous les systèmes."""
    return chemin.relative_to(espace.RACINE).as_posix()


def taille(octets: int) -> str:
    return f"{octets} o" if octets < 1024 else f"{octets / 1024:.1f} Ko".replace(".", ",")


def ecrire(chemin: Path, texte: str) -> None:
    """Écrit en UTF-8 sans BOM, fins de ligne LF, par un fichier temporaire puis un remplacement."""
    temporaire = chemin.with_name(chemin.name + TEMPORAIRE)
    temporaire.write_bytes(texte.encode("utf-8"))
    os.replace(temporaire, chemin)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--vers", help="piste qui reçoit les règles (ex. analyse)")
    p.add_argument("--depuis", default="principale", help="piste de référence (défaut : principale)")
    p.add_argument(
        "--empreinte", type=Path, metavar="FICHIER", help="afficher l'empreinte du contenu de ce fichier, sans rien écrire"
    )
    args = p.parse_args()
    if args.empreinte:
        afficher_empreinte(args.empreinte)
        return
    if not args.vers:
        p.error("--vers est obligatoire (ou --empreinte)")
    vers, depuis = args.vers, args.depuis

    for nom in (vers, depuis):
        if not NOM_PISTE.match(nom):
            sys.exit(f"Nom de piste invalide : « {nom} » (minuscules, chiffres et tirets).")
    if vers == depuis:
        sys.exit("--vers et --depuis désignent la même piste : rien à extraire.")
    source = espace.conception(depuis) / "CONTEXTE.md"
    dossier_piste = espace.conception(vers)
    sortie = dossier_piste / f"depuis_{depuis}"
    if not dossier_piste.is_dir():
        sys.exit(f"{dossier_piste} introuvable : la piste « {vers} » n'existe pas encore (kit/PISTES.md).")
    if not source.is_file():
        sys.exit(f"{source} introuvable : la piste « {depuis} » n'a pas de CONTEXTE.md.")
    if sortie.exists() and not sortie.is_dir():
        sys.exit(f"{sortie} existe et n'est pas un dossier : rien n'a été écrit.")

    octets = source.read_bytes()
    try:
        texte = octets.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        sys.exit(f"{source} n'est pas en UTF-8 (octet {e.start}) : rien n'a été écrit.")
    texte = texte.replace("\r\n", "\n").replace("\r", "\n")
    lignes, sous_sections, erreurs, avertissements = analyser(texte)
    if erreurs:
        print(f"Rien n'a été écrit. {source} ne suit pas le plan fixe de CONTEXTE.md :", file=sys.stderr)
        for e in erreurs:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    maintenant = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    modifiee = datetime.fromtimestamp(source.stat().st_mtime).astimezone().strftime("%Y-%m-%d %H:%M")
    h_source = hashlib.sha256(octets).hexdigest()
    rel_source = chemin_relatif(source)
    fichiers: dict[str, str] = {}
    lignes_table = []
    for n, (nom_court, quand) in EXTRAITES.items():
        nom = f"REGLES_{depuis.upper()}_{n}_{nom_court}.md"
        corps = corps_de_section(lignes[n])
        h = empreinte(corps)
        ss = sous_sections[n]
        entete = (
            f"{GENERE_PAR}\n"
            f"> **Règles propres au projet de la piste « {depuis} »**, § {n}, recopiées pour la piste « {vers} ».\n"
            f"> Source : `{rel_source}`, modifiée le {modifiee} ; SHA-256 de la source `{h_source[:16]}`.\n"
            f"> Généré le {maintenant}. Empreinte du contenu (le texte sous la ligne `---`) : `{h[:16]}`.\n"
            f"> Les chemins cités sont ceux de la piste « {depuis} » : les transposer avant de les appliquer.\n"
            f"> Le texte est recopié tel quel : ses renvois (« § 2 », « ce fichier », « ci-dessous ») visent le "
            f"CONTEXTE de la piste « {depuis} », et sa règle « à lire en entier » vaut pour les A de cette piste, "
            f"pas pour celles de la piste « {vers} ».\n"
        )
        if ss:
            entete += "> Sous-sections :\n" + "".join(f"> - {titre}\n" for titre in ss)
        contenu = f"{entete}\n{SEPARATEUR}\n\n{corps}"
        fichiers[nom] = contenu
        detail = (
            f"{len(ss)} sous-section{'s' if len(ss) > 1 else ''}, la dernière « {ss[-1].replace('|', '/')} »"
            if ss
            else "sans sous-section"
        )
        lignes_table.append(
            f"| `{nom}` | le § {n} entier ({detail}) | {quand} | {taille(len(contenu.encode('utf-8')))} "
            f"| `{h[:16]}` | `{h_source[:16]}` | {modifiee} |"
        )

    attendus = set(fichiers) | {LISEZ_MOI}
    for nom in sorted(attendus):
        if (sortie / nom).exists() and not (sortie / nom).is_file():
            sys.exit(f"{sortie / nom} existe et n'est pas un fichier : rien n'a été écrit.")
    en_trop = []
    if sortie.is_dir():
        for element in sorted(sortie.iterdir(), key=lambda e: e.name):
            nom = element.name
            if nom in attendus or (nom.endswith(TEMPORAIRE) and nom[: -len(TEMPORAIRE)] in attendus):
                continue
            en_trop.append(nom + ("/" if element.is_dir() else ""))
    anciennes = {}
    for nom in fichiers:
        if (sortie / nom).is_file():
            anciennes[nom] = empreinte_contenu((sortie / nom).read_text(encoding="utf-8", errors="replace"))

    suf_depuis, suf_vers = espace.suffixe(depuis), espace.suffixe(vers)
    trop = ", ".join(f"`{e}`" for e in en_trop) if en_trop else "aucun"
    lisez_moi = "\n".join(
        [
            GENERE_PAR,
            f"# Ce que la piste « {vers} » reçoit de la piste « {depuis} »",
            "",
            f"*Généré le {maintenant} par `uv run outils/extraire_piste.py --vers {vers} --depuis {depuis}`, "
            f"qui ne fait que lire `{rel_source}` et n'écrit que dans ce dossier. Ne rien écrire ici : le script "
            "le réécrit à chaque lancement. **Ce fichier est écrit en dernier : s'il manque, le dernier lancement "
            f"n'a pas abouti** ; l'A s'arrête et le dit à {espace.HUMAIN}.*",
            "",
            f"**Quand {espace.HUMAIN} relance le script** : avant d'ouvrir une A de la piste « {vers} », et après chaque "
            f"clôture d'une A de la piste « {depuis} ». L'A, prévenue, ne relit que les fichiers dont "
            "l'empreinte du contenu a changé depuis sa dernière lecture (elle les note au § 1 de son CONTEXTE).",
            "",
            "| Fichier | Contenu | Quand le lire | Taille | Empreinte du contenu | Empreinte de la source | Source modifiée le |",
            "|---|---|---|---|---|---|---|",
            *lignes_table,
            "",
            "**Les empreintes** (SHA-256, 16 premiers caractères). Celle du contenu porte sur le texte sous la "
            "ligne `---` de l'en-tête, sans les lignes vides de bord, avec une fin de ligne finale : elle ne "
            f"change que si la section change. Celle de la source porte sur `{rel_source}` entier : elle change "
            "à chaque modification de ce fichier, état compris. Pour recalculer celle d'un fichier :",
            "",
            f"    {RECALCUL}",
            "",
            f"**Transposition.** Ces règles nomment les dossiers de la piste « {depuis} » (`conception{suf_depuis}/`, "
            f"`v_for_cowork{suf_depuis}/`…) : pour la piste « {vers} », lire `conception{suf_vers}/`, "
            f"`v_for_cowork{suf_vers}/`. Ce qui suppose un accès aux dossiers de la piste « {depuis} » ne "
            f"s'applique pas tel quel : le signaler à {espace.HUMAIN}.",
            "",
            f"**Ce qui n'est jamais ici** : les §§ 4, 5 et 7 du CONTEXTE de la piste « {depuis} » (son état, ses "
            f"points ouverts, sa prochaine séance), ses briefs, ses passations, ses archives : l'A de la piste "
            f"« {vers} » n'a jamais accès à ses dossiers. Pour une section ou un fichier précis de l'autre piste, elle le "
            f"demande à {espace.HUMAIN}, en disant pourquoi ; {espace.HUMAIN} le colle dans la conversation, ou le copie "
            f"dans `conception{suf_vers}/relais/`, jamais dans ce dossier.",
            "",
            f"**Fichiers en trop** (présents ici, non écrits par le script : signalés, jamais supprimés) : {trop}.",
            "",
        ]
    )

    try:
        sortie.mkdir(exist_ok=True)
        (sortie / LISEZ_MOI).unlink(missing_ok=True)
        for nom, contenu in fichiers.items():
            ecrire(sortie / nom, contenu)
        for nom, contenu in fichiers.items():
            if (sortie / nom).read_bytes() != contenu.encode("utf-8"):
                sys.exit(f"{sortie / nom} relu différent de ce qui a été écrit : LISEZ_MOI.md n'est pas écrit.")
        ecrire(sortie / LISEZ_MOI, lisez_moi)
    except OSError as e:
        sys.exit(
            f"Écriture interrompue ({e}) : LISEZ_MOI.md est absent, l'A s'arrêtera. Fermer ce qui tient "
            f"un fichier de {sortie} ouvert, puis relancer."
        )

    print(f"Source : {source} (SHA-256 {h_source[:16]}, modifiée le {modifiee})")
    for nom, contenu in fichiers.items():
        nouvelle = empreinte_contenu(contenu)
        etat = "nouveau" if nom not in anciennes else ("inchangé" if anciennes[nom] == nouvelle else "CHANGÉ")
        print(f"-> {sortie / nom}  {nouvelle[:16]}  {etat}")
    print(f"-> {sortie / LISEZ_MOI}  (écrit en dernier)")
    for a in avertissements:
        print(f"Avertissement : {a}")
    if en_trop:
        print(f"En trop dans {sortie} (signalés, non supprimés) : {', '.join(en_trop)}")
    print(f"Dire à l'A de la piste « {vers} » : script relancé ; elle relit ce qui a changé.")


if __name__ == "__main__":
    main()
