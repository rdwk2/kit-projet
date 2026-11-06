# Charte d'analyse

*Version «n», validée le «AAAA-MM-JJ». Sans chiffre tiré des données.*

*Ce que la charte fixe : comment le projet produit un résultat d'analyse auquel on peut se
fier. Ce qu'elle ne fixe pas : la méthode de chaque question, qui vient dans son plan
d'analyse, relu, et qui doit respecter la charte. Modèle : la charte d'analyse d'un premier
projet ; chaque section dit ce qu'elle doit trancher pour ce projet.*

## 1. Les principes

<!-- Ex. : la mesure avant l'interprétation ; aucun chiffre tiré des données dans le dépôt. -->

## 2. Les données : du brut aux tables

<!-- Les couches (brut immuable → intermédiaire → tables), qui les écrit, comment elles se
régénèrent ; ce qu'on ne lit jamais directement. -->

## 3. Configuration, seuils et notes de l'utilisateur

<!-- Ce qui se déclare par personne (seuils, catégories, notes) plutôt que dans le code. -->

## 4. Les unités d'observation

<!-- Sur quoi on observe, et la dépendance entre observations (plusieurs mesures d'une même
journée ne sont pas indépendantes). -->

## 5. Les essais, et la règle « déjà vue »

<!-- Un essai : une hypothèse déclarée avant de la tester. Une question « déjà vue » : une
question dont une réponse a déjà été affichée sur ces mêmes données. Chaque déclaration compte
pour un essai ; une hypothèse ne se confirme que sur des données postérieures à sa déclaration ;
le registre des essais. -->

## 6. Le plan d'analyse de chaque question

<!-- Ce qu'il contient (unité, mesure, facteur, confusions et leur traitement, bases à battre,
c'est-à-dire les méthodes simples servant de référence, validation dans l'ordre du temps), et sa
relecture avant le code. -->

## 7. Prévoir : bases à battre, validation dans l'ordre du temps

## 8. L'incertitude

<!-- Comment on la rapporte ; ce qu'on ne rapporte pas sans elle. -->

## 9. Notebooks et interface

<!-- Règle 7 de CLAUDE.md : un notebook explore, mais tout chiffre rapporté vient d'une
fonction testée de src/. Les notebooks ne lisent que les tables, jamais le brut. -->

## 10. Où vivent les résultats

<!-- Hors du dépôt, sous le dossier des données ; nommés par date et empreinte (hachage du
contenu). -->

## 11. Les relectures

<!-- Quels textes passent par une relecture (plan d'analyse, charte), et par qui. -->
