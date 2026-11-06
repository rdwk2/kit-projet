# passations/

Ce qui passe d'une conversation ou d'une session à l'autre, et ce qui en revient :

- les copies d'état (`CONTEXTE_avant_A«n».md`, une par clôture) ;
- les rapports de relecture rangés (avec le module `relectures` : `RELECTURE_BRIEF-«jalon».md`,
  `RELECTURE_PLAN-«jalon».md`, `RELECTURE_PR-«n».md`), déplacés ici dès que leur auteur a fini ;
- les documents d'A remplis depuis `kit/gabarits/` (consignes, arbitrages, revues, paquets
  avec leur `DEMARRAGE.md`) ;
- les comptes rendus de l'agent de code (`COMPTE_RENDU_CODE_PR-«n».md`, pour A seulement) ;
- les listes d'archivage (`A_ARCHIVER_«étape».txt`), avec le module `archives`.

Ce dossier n'est vu que par A : il est sous `conception`. Ce qui doit parvenir à une autre
conversation ou session passe, filtré par A, par `v_for_cowork` ou par un paquet. Avec le module
`relectures`, B y lit le brief et son annexe, et C reçoit le paquet `«jalon»-C/` ou
`passations/C_PR-«n»/`, copié dans son poste par `outils/clone_c.py`.
