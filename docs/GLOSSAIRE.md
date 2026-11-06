# Glossaire

Les mots du kit, puis ceux de git et de GitHub. Une fois l'espace IA généré,
`conception/kit/VOCABULAIRE.md` donne le détail.

## Les mots du kit

| Mot | Sens |
|---|---|
| **A** | La conversation de conception : elle discute avec toi, découpe le travail, écrit les briefs |
| **Agent de code** | Une IA qui lit et modifie directement les fichiers du dépôt : Claude Code, Codex, Copilot… |
| **Arbitrage** | La décision, prise par A avec toi, sur chaque constat d'une relecture |
| **B** | La relecture d'artefact : une conversation neuve relit un brief ou un plan, avant le code |
| **Brief** | Le document qui dit ce qu'un jalon doit faire et comment on le vérifie |
| **C** | La relecture de PR : une conversation neuve relit le code fini, sans connaître la conception |
| **Clôture** | Ce que fait une conversation A avant de s'arrêter : mettre à jour `CONTEXTE.md` |
| **Connecter** | Donner à une conversation l'accès à un dossier ([selon ton outil](WORKFLOW.md#la-frontière-fait-le-travail)) |
| **Constat** | Un défaut relevé par une relecture : où, quoi, comment ça casse |
| **Conversation neuve** | Une conversation qui n'a rien vu de ce qui précède |
| **Couche** | Ce que le kit génère : le dépôt, ou l'espace IA |
| **Espace IA** | Le dossier autour du dépôt, où vivent la conception et les relectures |
| **Fichier du kit** | Un fichier réécrit à chaque mise à jour : on ne le modifie pas dans un projet |
| **Fichier vivant** | Un fichier écrit une fois, qui appartient ensuite au projet |
| **Jalon** | Une étape du projet, livrée en une PR |
| **Miroir** | Une copie du dépôt en lecture seule, pour les conversations |
| **Module** | Une fonction à cocher : données privées, groupe, relectures… |
| **Mutation** | Introduire une erreur exprès, pour vérifier que les tests la détectent |
| **Paquet** | Le dossier de pièces remis à un relecteur |
| **Passation** | Ce qu'une conversation laisse à la suivante : un fichier, pas un souvenir |
| **Passe experte** | Une relecture spécialisée, sur un point difficile (maths, algorithme) |
| **Piste** | Un axe de travail parallèle, avec ses propres conversations |
| **Poste** | Le dossier jetable où une C relit une PR |
| **Préréglage** | Un choix de modules tout prêt : solo léger, groupe scolaire, standard, complet |
| **Relève** | Le remplacement d'une conversation A par une neuve |
| **Remontée** | Une amélioration notée dans un projet, pour le kit |
| **`v_for_cowork`** | Le dossier partagé entre A et ses relecteurs. Son nom est historique : il sert avec tout outil |

## Les mots de git et de GitHub

| Mot | Sens |
|---|---|
| **Branche** | Une ligne de travail à part, pour ne pas toucher à `main` |
| **CI** | Les vérifications que GitHub lance tout seul à chaque envoi |
| **Clone** | Une copie d'un dépôt sur ta machine |
| **Commit** | Une étape enregistrée de ton travail |
| **Dépôt** | Le projet et tout son historique |
| **Diff** | La liste des lignes changées |
| **Fusion** | Faire entrer une branche dans `main` |
| **Hook** | Un script lancé automatiquement avant une action, pour la contrôler |
| **`main`** | La branche de référence : ce qu'elle contient marche |
| **PR (pull request)** | Une demande de fusion, où l'on relit les changements avant de les accepter |
| **Tag** | Une étiquette posée sur un commit, pour marquer une version |
| **Tête** | Le dernier commit d'une branche |

## Les outils

| Outil | Rôle |
|---|---|
| **Copier** | Génère un projet depuis le kit, et le met à jour |
| **gh** | GitHub en ligne de commande |
| **just** | Lance les commandes du projet : `just check` vérifie tout |
| **mypy** | Vérifie les types |
| **pytest** | Lance les tests |
| **ruff** | Vérifie le style et le formatage |
| **uv** | Installe Python et les dépendances du projet |
