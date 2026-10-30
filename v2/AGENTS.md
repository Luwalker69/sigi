# SIGI v2

- Lire et actualiser `CURRENT_STATE.md` après chaque étape vérifiée.
- Le domaine dépend des contrats ; les adaptateurs dépendent du domaine.
- Aucun secret dans les fichiers, journaux et tests.
- Ne pas exécuter de code généré dans le pilote.
- Aucun appel payant dans les tests ; utiliser un serveur HTTP simulé.
- Tests : `python -B -m unittest discover -s tests -v`.
- Démo : `python -B -m sigi demo`.
- Distinguer capacité implémentée, interface prévue et intégration validée.
