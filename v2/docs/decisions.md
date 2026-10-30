# Décisions de la première tranche

## Dépendances dirigées vers des contrats

`contracts.py` définit des interfaces petites. `Engine` orchestre leur composition ; `models.py`, `workspace.py`, `transport.py` et `store.py` les implémentent. Une API, un transport ou un stockage peut être remplacé sans modifier les autres.

Le catalogue des trois outils est encore statique et placé dans `workspace.py`. Lors de l'ajout d'un second domaine d'outils, extraire ce catalogue dans un registre avec permissions ; ne pas imposer aux futurs outils l'interface des fichiers.

Les contrats eux-mêmes peuvent évoluer avec une version et des tests de migration. La modularité diminue le coût de changement ; elle n'annule pas les différences entre fournisseurs ou runtimes.

## Premier moteur comme banc d'essai

La proposition cible s'appuie notamment sur OpenHands pour l'agent, OpenShell pour l'environnement et Temporal pour les missions durables. Cette tranche construit d'abord un petit parcours Python standard permettant d'exercer les frontières, le transport et le journal sans installer toute la pile.

Ce moteur n'a pas vocation à concurrencer ces bibliothèques. L'intégration OpenHands devra le remplacer ou devenir un second moteur après validation des mêmes scénarios. Le branchement dans la CLI est le point de composition ; aucune API publique du moteur n'est encore déclarée stable.

## Périmètre d'exécution explicite

Les actions actuelles se limitent à lister, lire et créer des fichiers dans un dossier dédié. Les clés du modèle sont dans le pilote ; le worker possède uniquement son jeton de service. Aucun `exec`, shell ou chargement de plugin provenant du modèle.

La première exécution de code arbitraire sera conditionnée par la validation d'un runtime isolé. Les outils, profils navigateur et secrets des services seront ajoutés derrière les mêmes frontières avec un contrôle de permissions externe au modèle.

## Comptabilité prudente, sans promesse de plafond absolu

Le moteur réserve avant l'appel et enregistre la réservation avant le réseau. Il rapproche ensuite la consommation rapportée par le fournisseur. L'estimation préalable utilise des octets et une marge, pas le tokenizer exact du fournisseur. Une facture plus élevée que prévu peut donc déjà avoir été engagée ; le moteur arrête alors les actions suivantes.

Pas de parallélisme ni de budget global partagé dans cette tranche. Ces fonctions demanderont un registre transactionnel côté service de confiance. Les coûts non tokenisés du fournisseur et l'infrastructure ne sont pas encore comptabilisés.

## Journaux avant reprise automatique

Les états et intentions sont sauvegardés avant les effets. Le redémarrage automatique et les écritures externes sont différés jusqu'à l'ajout d'une réconciliation et de clés d'idempotence. Une trace `pending` indique un résultat incertain, pas un échec certain.

## Auto-amélioration différée et testable

Le code peut être modifié aujourd'hui par un développeur ; il ne se modifie pas lui-même en production. La future évolution automatique utilisera une branche candidate, des tests possédés par un évaluateur séparé, des mesures de coût/réussite et un mécanisme de retour arrière. Le candidat ne contrôlera pas les secrets ni les seuils de sa propre promotion.
