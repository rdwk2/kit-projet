# relecture/

Une C relit une PR sans avoir vu la conception ; son poste est un dossier jetable. Voir
`conception/kit/VOCABULAIRE.md`.

Un poste par relecture C, préparé par `uv run outils/clone_c.py «n» --paquet «nom»` : `c-pr«n»/`
pour la C d'une PR, `c-pr«n»-«variante»/` pour une C bornée ou une seconde C
(`--variante «variante»`), suivis de `_«piste»` dans une piste parallèle. Il contient le clone du
dépôt sur la tête de la PR, avec son environnement (`uv sync --locked`, lancé une fois le poste à
sa place : un `.venv` déplacé ne marche plus), et `paquet/` (le démarrage écrit par A). Le script
lance aussi `just check` et dit s'il est rouge.

- Lancer l'agent **dans** le poste (pas de `.git` à sa racine, aucun dossier ajouté), en
  **mode normal** (sans mode plan, si ton agent en a un) : il doit pouvoir écrire son rapport.
- À la fin : `uv run outils/clone_c.py «n» --recuperer [--variante «variante»]` copie ses rapports
  vers A ; celui d'une C bornée ou seconde y prend le nom `RELECTURE_PR-«n»_«variante».md`.
- Une préparation qui échoue laisse un `….preparation` qu'aucune session n'a ouvert : relancer
  la même commande le retire.
- Un poste neuf par relecture, jamais réutilisé : sous Windows, un dossier encore tenu ouvert par une
  session refuse de s'effacer, et la C suivante jouerait sur l'ancien clone. Le ménage se fait
  à la main, toutes les sessions fermées.
- Ce dossier n'est jamais connecté à une conversation.
