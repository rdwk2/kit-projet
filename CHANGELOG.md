# Changements de kit-projet

## 0.4.0 — 2026-11-06

Un débutant reçoit moins. Solo léger et Groupe scolaire s'allègent ; Standard et Complet ne changent pas :
leur rendu reste le même, à l'octet près. Aucun fichier vivant ne change de structure.

- **Dépôt pour débuter.** Une valeur calculée, `debutant`, porte les variantes de Solo léger et de Groupe
  scolaire. `CLAUDE.md` garde ses huit règles et leurs numéros, en une ou deux lignes chacune ; numpy, scipy
  et matplotlib sont acceptés d'office, et les tests de propriété sont bienvenus, pas exigés. `mypy` passe en
  mode souple (`strict = false`, `check_untyped_defs = true`) : les annotations ne sont demandées que sur les
  fonctions publiques. `hypothesis`, `TID251`, les blocs d'extras et `py.typed` sortent. `docs/ROADMAP.md`
  tient ses trois principes en trois lignes, sous le même titre.
- **Module `pistes`.** `kit/PISTES.md`, ses quatre gabarits et `outils/extraire_piste.py` ne sont plus
  générés en Solo léger ni en Groupe scolaire. Standard et Complet ont le module d'office ; en Personnalisé,
  il se coche. Créer une piste sans le module est refusé, avec un message qui dit quoi faire.
- **`JOURNAL` en groupe.** Une entrée par livraison, dans la PR de livraison d'un responsable, au lieu d'une
  entrée par PR : deux PR ouvertes n'entrent plus en conflit. En Solo léger, le `JOURNAL`, les fiches de
  décision et `docs/PIEGES.md` deviennent facultatifs.
- **Clôture courte.** Sans le module `relectures`, le § 7 de `CONTEXTE.md` se réduit à l'état, aux points
  ouverts et à la prochaine étape, la clôture à quatre étapes, et la lecture d'ouverture au § 0 de
  `kit/METHODE.md` et à `CONTEXTE.md`. Les sept titres de `CONTEXTE.md` restent, la copie d'avant aussi. Le
  § 8.3 d'un brief court devient facultatif.
- **Banc.** Nouveaux scénarios `depot-perso-standard` et `espace-pistes-seules`. Il vérifie les huit règles
  de `CLAUDE.md`, qu'aucun fichier absent n'est cité, qu'une piste sans le module est refusée, qu'une fonction
  sans annotations passe `just check` en préréglage débutant, et qu'un filet `---` suit une ligne vide.
- **Mettre à jour un projet.** En Personnalisé, coche `pistes` si le projet a plusieurs pistes : sans lui,
  `copier recopy` ne rafraîchit plus `kit/PISTES.md` ni ses gabarits. Il n'efface pas non plus les fichiers
  devenus inutiles : en Solo léger ou en Groupe scolaire, ils restent tels quels, jusqu'à ce que tu les retires.

## 0.3.0 — 2026-11-05

Première version partagée : le kit sert désormais à d'autres que son auteur. Les paragraphes changés
portent une barre `▌`, à retirer avant de publier (`uv run outils_kit/retirer_barres.py`). Aucun
fichier vivant ne change de structure.

- **Documentation.** `LISEZ_MOI.md` devient `README.md`, une page d'accueil avec un démarrage sans prise de tête et un démarrage en dix minutes. Nouveaux :
  `docs/GUIDE.md`, `docs/GLOSSAIRE.md`, `docs/WORKFLOW.md`, `CONTRIBUTING.md`, trois schémas Mermaid avec
  leur source `.mmd`, deux règles GitHub à importer (`docs/regles/`), la licence MIT.
- **Questions.** `humain`, `github` et `responsables` n'ont plus de valeur par défaut : ils sont demandés
  et validés. `racine` vaut `~/dev/<slug>`, et n'est posée que pour l'espace : elle ne part plus dans
  `.copier-answers.depot.yml`, qui est commité. Solo léger devient le préréglage par défaut, et le préfixe des jalons passe à `J`. Les
  libellés changent ; les valeurs `perso-standard` et `perso-complet` restent, car une valeur renommée
  ferait perdre ses modules à un projet existant, sans erreur.
- **Tout public.** Plus de nom, de chemin, de domaine d'origine, de citation ni de chiffre réel dans les
  fichiers générés. `kit/MACHINE.md` devient les pièges d'outillage, avec une partie macOS et Linux ; ses
  identifiants ne changent pas, et les entrées propres à une machine ou à Cowork en sortent.
  `kit/MODELES_ET_EFFORTS.md` raisonne par niveaux. `kit/VOCABULAIRE.md` définit les rôles et les mots de git.
- **Tout agent.** Les outils sont nommés avec une alternative. Le hook n'est promis que pour Claude Code :
  un autre agent n'a que la consigne.
- **Toute machine.** Chemins en `/`, `~` développé dans `outils/espace.py`, `.gitattributes` à la racine,
  CI du banc sur Windows, macOS et Linux. `http.sslBackend=schannel` n'est plus imposé : `KIT_SCHANNEL=1`
  le demande.
- **Code scientifique.** `just check` accepte l'écriture mathématique : ruff ignore `N803`, `N806` et
  `E741`, permet les lettres grecques usuelles ; mypy ne bloque plus sur un paquet sans types
  (`import-untyped`).
- **Débutants.** `README.md` et `CONTRIBUTING.md` disent les prérequis, l'authentification GitHub et
  `uv.lock` au premier commit. La CI ne tourne plus deux fois par PR. `data/` est ignoré pour tous. Un texte
  qui citait un module absent passe sous condition.
- **Scripts.** `espace.miroir_pret()` dit clairement qu'il manque le miroir ; `extraire_piste.py --empreinte`
  remplace une commande `python3 -c` ; le hook ignore la casse sous macOS ; `just fmt` va au bout.
- **Banc.** Il vérifie les renvois vers `kit/MACHINE.md`, les chemins en `~`, les schémas et leurs sources,
  `uv sync --locked`, et un module écrit comme un mathématicien. Il ne contient plus aucun terme privé :
  leur liste vit hors du dépôt (`KIT_TERMES_PRIVES`).
- **Version personnelle.** `kit/METHODE.md` lit `kit/perso/` s'il existe : un dépôt privé suit le kit public
  en n'ajoutant que des fichiers (`CONTRIBUTING.md`).
- **Remplacements mécaniques, sans barre.** Le pseudo de l'auteur devient `[[ humain ]]`, `[[ de_humain ]]` ou
  `[[ que_humain ]]` ; `\` devient `/` dans les chemins ; les blocs neutres passent de `powershell` à `bash` ;
  les lignes « Source » des leçons deviennent « Niveau » ; les dates d'observation quittent `kit/MACHINE.md`.
  Les barres `▌` de la version précédente sont retirées.

Les versions précédentes étaient privées.
