# Contribuer au kit

Deux cas : tu veux ta propre version du kit, ou tu veux l'améliorer pour tout le monde.

- **Ta propre version** : fais un fork (ci-dessous). Tu en fais ce que tu veux.
- **Une amélioration pour tout le monde** : fais un fork, change ce qu'il faut sur une branche, lance le
  banc, puis ouvre une pull request vers ce dépôt.

## Ta propre version : un fork

Sur GitHub, clique sur **Fork**, puis récupère ta copie. Le dépôt d'origine devient `upstream` :

```bash
# À remplacer : «ton-compte»
git clone https://github.com/«ton-compte»/kit-projet
cd kit-projet
git remote add upstream https://github.com/rdwk2/kit-projet
```

Pour recevoir les nouveautés :

```bash
git pull upstream main
```

Pour qu'elles arrivent sans conflit :

- **Ajoute des fichiers, ne modifie pas ceux du kit.** Tes notes pour les conversations vont dans
  `espace/conception[[ suffixe ]]/kit/perso/` : ce dossier n'existe pas dans le kit, et `kit/METHODE.md`
  demande de le lire s'il existe.
- **Tes valeurs par défaut** n'ont rien à faire dans le kit : mets-les dans `settings.yml`
  ([guide](docs/GUIDE.md#7-tes-réglages)).
- **Tague tes versions** `v«X.Y.Z»+perso` : Copier prend le dernier tag, et le suffixe passe après le
  tag de la même version.

Pour vérifier qu'aucun terme privé ne part dans une PR, écris-les dans un fichier hors du dépôt, un par
ligne, et donne son chemin au banc : variable d'environnement `KIT_TERMES_PRIVES`. Les dossiers `perso/`
ne sont pas contrôlés.

## Comment le kit est fait

| Élément | Rôle |
|---|---|
| `copier.yml` | Les questions, les préréglages, les modules, la présence de chaque fichier (`_exclude`), les fichiers vivants (`_skip_if_exists`) |
| `depot/` | La couche dépôt : ce qui finit dans le dépôt git d'un projet |
| `espace/` | La couche espace IA : ce qui finit autour du dépôt, une fois par piste |
| `docs/` | La documentation du kit, ses schémas (`docs/schemas/*.mmd`) et ses règles GitHub (`docs/regles/`) |
| `outils_kit/tester_kit.py` | Le banc d'essai : génère chaque préréglage et vérifie le résultat |
| `CHANGELOG.md` | Les versions : une version = un tag git `v«X.Y.Z»` |

Copier ne copie que le sous-dossier de la couche demandée (`_subdirectory`) : le reste n'arrive jamais
dans un projet.

## Conventions

- **Seuls les fichiers en `.jinja` sont interprétés** ; les autres sont copiés tels quels.
- Délimiteurs changés : `[[ variable ]]`, `[% if … %] … [% endif %]`, `[# commentaire #]`. Les `{{ … }}`
  de GitHub Actions et de just restent du texte.
- `[[ humain ]]` donne le nom ; `[[ de_humain ]]` et `[[ que_humain ]]` gèrent l'élision (« d'Alice »).
  Une anecdote au passé n'emploie pas ces variables : elle n'est pas arrivée au lecteur.
- `«…»` : un champ que la conversation remplit à l'usage, jamais touché par Copier.
- **Fichier du kit** (en-tête « Fichier du kit ») : réécrit à chaque mise à jour, jamais modifié dans
  un projet. **Fichier vivant** (en-tête « Fichier vivant ») : écrit une fois, listé dans
  `_skip_if_exists`, jamais écrasé.
- Chemins en `/`, valables partout, PowerShell compris. Un bloc `bash` doit aussi marcher sous
  PowerShell ; sinon, c'est un bloc `powershell`, avec sa variante.
- Dans la documentation, chaque bloc de commandes rappelle ce qu'il faut remplacer sur sa première ligne.
- Noms de fichiers naturels : la présence se règle dans `_exclude`, pas dans les noms. Pas de
  `| : * ? " < >` dans un nom (Windows).
- **`debutant`** vaut vrai en Solo léger et en Groupe scolaire : une variante pour débuter se met dans un
  `[% if debutant %]`, sans toucher au texte de Standard et Complet.
- **Barre `▌`** en marge : marque un paragraphe changé, le temps d'une relecture.
  `uv run outils_kit/retirer_barres.py` les retire.
- **Schémas** : peu de boîtes, texte court, police de 22 px ; un lecteur ne peut pas zoomer. La source
  `.mmd` et le bloc Mermaid de la page doivent être identiques : le banc le vérifie.

## Ne pas renommer les valeurs des préréglages

Une valeur inconnue dans `.copier-answers.*.yml` ne produit pas d'erreur : `copier update --defaults`
retombe sur le préréglage par défaut, et retire des modules au projet. C'est pourquoi « Standard »
garde la valeur `perso-standard`, et « Complet », `perso-complet`.

## Modifier le kit

1. Modifie les fichiers. Un fichier vivant ne sera reçu que par les nouveaux projets.
2. **Ajouter un module** : une entrée dans `modules_choisis`, le module dans les préréglages concernés
   (`modules`), ses lignes dans `_exclude`, ses fichiers, ses attentes dans `outils_kit/tester_kit.py`.
3. Lance le banc :
   ```bash
   uv run outils_kit/tester_kit.py            # structure, délimiteurs, scripts, recopy, renvois
   uv run outils_kit/tester_kit.py --complet  # + uv sync et just check dans les dépôts générés
   ```
4. Une entrée dans `CHANGELOG.md`, un commit, un tag :
   ```bash
   # À remplacer : le message et le numéro de version
   git add -A
   git commit -m "feat: «ce qui change»"
   git tag v«X.Y.Z»
   ```
   Version **majeure** si un fichier vivant change de structure, **mineure** si des règles, gabarits ou
   modules s'ajoutent, **correctif** sinon.

Pour essayer une modification pas encore taguée, ajoute `--vcs-ref HEAD` à `copier copy`.

Les changements de fond viennent des remontées des projets (`REMONTEES_KIT.md`). Le prompt de la
session qui les consolide est dans `espace/conception[[ suffixe ]]/kit/prompts/CONSOLIDATION_KIT.md.jinja`.
