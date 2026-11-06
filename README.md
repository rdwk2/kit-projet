# kit-projet

Un gabarit pour démarrer un projet de code propre, et le mener avec une IA sans en perdre le contrôle.

## À quoi ça sert

En une commande, le kit crée le dépôt git d'un projet déjà prêt : tests, vérifications automatiques,
règles pour l'agent de code, modèles de documents. Quand le kit évolue, tes projets se mettent à jour
sans perdre tes modifications.

Pour un projet plus ambitieux, il ajoute un espace IA : un dossier où des conversations d'IA séparées
conçoivent le travail, puis relisent celui de l'agent de code.

**Pour qui ?** Tu sais programmer en Python, et tu débutes sur git ou sur les agents de code. Le kit
marche sous Windows, macOS et Linux, avec Claude ou un autre agent.

## Le principe

```mermaid
%%{init: {"theme": "neutral", "themeVariables": {"fontSize": "22px"}}}%%
flowchart LR
    K["Le kit"] --> D["Le dépôt<br/>ton code"]
    K -.-> E["L'espace IA<br/>facultatif"]
```

Le **dépôt** contient ton code et tout ce qui le vérifie. L'**espace IA** est facultatif : il entoure le
dépôt et accueille les conversations de conception. Pour débuter, le dépôt suffit.

## Démarrer sans prise de tête

Tu as Claude Code, ou un autre agent de code ? Ouvre une session neuve dans le dossier où tu ranges tes
projets, et colle ce message. L'agent lit le kit, te pose ses questions, t'explique les mots et te dit
si le kit t'aidera vraiment. Avec ton accord, il lance les commandes à ta place.

```text
Je veux peut-être démarrer un projet avec kit-projet : https://github.com/rdwk2/kit-projet

Clone ce dépôt dans un dossier temporaire, puis lis README.md, docs/GUIDE.md, docs/WORKFLOW.md et
docs/GLOSSAIRE.md.

Ensuite, avant de lancer quoi que ce soit :
1. Demande-moi ce que je veux faire, si je travaille seul ou à plusieurs, et ce que je connais déjà de
   git et des agents. Une question à la fois.
2. Dis-moi franchement si le kit m'aidera pour ce projet. Propose un préréglage et explique-le avec des
   mots simples.
3. Vérifie ce qui est installé sur ma machine (git, uv, just, gh), et dis-moi ce qui manque.

Puis, avec mon accord, lance toi-même les commandes du guide et vérifie leur résultat. Termine en me
disant ce que je fais ensuite, avec la première demande à faire à mon agent.
```

## Démarrer à la main, en dix minutes

Ces étapes créent un **petit projet** : le dépôt seul, avec le préréglage solo léger. Pour un autre
préréglage, voir [plus bas](#quel-préréglage-choisir).

**1. Installe les outils**, une seule fois. Il te faut [git](https://git-scm.com/downloads), un
compte [GitHub](https://github.com), puis uv et just :

```bash
# macOS et Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows, dans PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Rouvre ton terminal, puis :

```bash
uv tool install rust-just
```

**2. Crée ton projet.** Place-toi dans le dossier où tu ranges tes projets. `mon-projet` est un
exemple : **remplace-le par le nom de ton projet**, en minuscules, sans espace ni accent. Copier, l'outil
qui génère le projet, pose ensuite quelques questions ; garde les réponses proposées si tu hésites.

```bash
# À remplacer : mon-projet
uvx copier copy --data couche=depot --data preset=solo-leger gh:rdwk2/kit-projet mon-projet
```

**3. Vérifie que tout est vert.**

```bash
# À remplacer : mon-projet
cd mon-projet
git init -b main
uv sync
just check
```

**4. Enregistre ce premier état.** `uv.lock` part dans ce commit : sans lui, la vérification de GitHub
échouerait.

```bash
git add -A
git commit -m "chore: squelette depuis kit-projet"
```

**5. Mets-toi au travail.** Ouvre ton agent de code dans le dossier de ton projet. Il lit `CLAUDE.md`
(ou `AGENTS.md`), qui lui donne les règles du projet. Tu peux commencer par ce message :

```text
Lis CLAUDE.md. Pose-moi des questions sur ce que je veux faire, une à la fois, puis complète README.md
et docs/ROADMAP.md. Propose ensuite un plan pour le premier jalon, et attends mon accord avant d'écrire
du code.
```

Pour envoyer le projet sur GitHub et protéger `main` : [guide](docs/GUIDE.md#4-après-la-génération).

## Quel préréglage choisir

Le préréglage se choisit dans la commande de l'étape 2, avec `preset=`.

| Préréglage | Pour | Ce que tu génères | `preset=` |
|---|---|---|---|
| **Solo léger** | Un TP, un script, un petit outil | Le dépôt | `solo-leger` |
| **Groupe scolaire** | Un projet à plusieurs, débutants sur GitHub | Le dépôt, avec un guide pour les camarades | `groupe-scolaire` |
| **Standard** | Un projet personnel qui dure | Le dépôt et l'espace IA, avec conception et relectures | `perso-standard` |
| **Complet** | Un gros projet, avec des données privées | Le standard, plus archives, mutation et passes expertes | `perso-complet` |

Standard et Complet demandent deux commandes, car ils génèrent aussi l'espace IA : voir le
[guide, § 3.2](docs/GUIDE.md#32-le-dépôt-et-lespace-ia).

## Pour aller plus loin

- [Le guide](docs/GUIDE.md) : créer, mettre en route, mettre à jour un projet, cas particuliers.
- [Le workflow A/B/C expliqué](docs/WORKFLOW.md) : à quoi servent les conversations séparées.
- [Le glossaire](docs/GLOSSAIRE.md) : les mots du kit et de git.
- [Contribuer](CONTRIBUTING.md) : ta propre version du kit, ou une amélioration à proposer.

## Licence

[MIT](LICENSE). Les fichiers que le kit génère t'appartiennent : tu n'as aucune mention à y garder.
