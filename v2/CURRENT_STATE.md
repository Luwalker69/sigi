# Où en est SIGI ?

Mis à jour le 30 octobre 2026.

## Objectif du propriétaire

Assistant aussi polyvalent que possible : automatisations natives, recherche approfondie et capacité d'expérimenter ses propres architectures. API économiques, composants faciles à réarranger, exécution distante pour dissocier l'agent du PC. Privilégier des résultats visibles rapidement ; bilans courts pour l'utilisateur.

## Ce qui existe et a été vérifié

- Une démo gratuite lit vraiment un fichier et crée un rapport.
- Le modèle, les outils et le journal ont trois contrats Python indépendants.
- Le même moteur fonctionne avec un dossier dédié et avec un worker HTTP séparé.
- Un appel API compatible Chat Completions a été vérifié contre un serveur simulé, y compris la remontée du coût et l'absence de clé dans le journal.
- Les limites de budget, chemins hors workspace, liens symboliques et écrasements sont testés.
- Les redirections HTTP ne transmettent pas les identifiants.
- Vingt et un tests sur vingt et un passent sous Ubuntu, dont les diagnostics, le contexte de conversation, le budget cumulé et les frontières HTTP locales. Le correctif de diagnostic et l'interface n'ont pas encore été testés sous Windows natif.
- La CLI `python3 -B -m sigi demo` a été exécutée dans Ubuntu et a produit un rapport réel.
- `doctor --ask-key` vérifie l'authentification et la liste des modèles sans génération. Son transport est vérifié avec une API simulée.
- `run --ask-key` demande directement la clé, sans `read` ni `export`, et remplace une valeur de terminal obsolète pour cette seule commande.
- Le propriétaire a confirmé un premier appel Gemini réussi : présentation de SIGI, statut `completed`, coût déclaré 0,0001928 USD. Cette observation valide un échange simple ; elle ne mesure pas la qualité générale du modèle.
- `python3 -B -m sigi ui` lance une interface locale sur http://127.0.0.1:8765 : clé masquée en mémoire, conversation suivie, coût cumulé, nouvelle conversation et déconnexion.
- Le parcours de chat en mode démo a été exercé dans un navigateur, sur une vue étroite et une vue d'ordinateur ; la connexion et la déconnexion sont également testées via une API simulée.

## Incident résolu et limites connues

Le premier essai réel avait échoué avec un `RuntimeError` masqué. Après ajout de `doctor`, le propriétaire a confirmé l'authentification puis une génération réussie. La cause de l'ancien échec n'a pas été établie. Aucune clé du propriétaire n'a été utilisée pendant les tests automatiques et aucun changement de facturation n'a été effectué par l'assistant.

Le correctif préserve les codes HTTP et quelques raisons connues sans afficher le corps brut, la clé ou des extraits de requête. Le quota de génération n'est pas prouvé par une simple liste de modèles.

## Ce qui n'est pas encore fait

- Conversation multi-tour et actions fichiers de l'interface à confirmer avec le vrai modèle ; tests automatiques faits avec un modèle simulé.
- Hébergement distant, terminaison TLS, confinement OS et exécution de code généré.
- Navigation, moteur de recherche, documents et comptes connectés.
- Automatisations programmées, reprise automatique après crash et budgets multi-workers.
- Évaluation indépendante de la qualité et laboratoire d'auto-amélioration.
- Adaptateurs OpenHands, OpenShell et Temporal.
- Build Docker : non testé, Docker indisponible sur l'hôte d'analyse.

`completed` signifie que la boucle a reçu une réponse finale ; ce statut ne certifie pas encore la qualité du résultat. Les journaux permettent d'inspecter ce qui a été réellement exécuté.

Le journal est conservé, mais la mission ne redémarre pas automatiquement. En cas d'appel interrompu, la réservation demeure ; une action marquée `pending` doit être réconciliée avant un rejeu. Le worker n'exécute aucun code arbitraire. Les protections de chemin ne remplacent pas une sandbox OS, notamment si un autre processus peut changer les fichiers en parallèle.

Le chat conserve les réservations incertaines dans son budget pour ne pas les effacer au message suivant. Les clés ne sont pas persistées ; les transcriptions restent locales sous `.sigi/chats/`. Les conversations ne sont pas encore restaurées dans l'interface après redémarrage. Chaque nouvelle conversation reçoit une enveloppe propre ; aucun plafond global multi-session n'est encore appliqué.

## Prochaine étape unique

Utiliser l'interface sur deux ou trois échanges réels, puis demander de lire un brief et de créer une synthèse. Vérifier le fichier et rapprocher le coût cumulé de celui du fournisseur. Le paiement des crédits reste réalisé par le propriétaire dans Google AI Studio.

## Puis

1. Déployer le worker sur un hôte Linux distant avec HTTPS et isolation validée.
2. Ajouter recherche/navigation et mémoire sourcée, avec évaluation des citations.
3. Transformer une mission récurrente en procédure déterministe et reprendre après interruption.
4. Ajouter un laboratoire qui modifie une branche, exécute des tests indépendants et compare les versions avant promotion.

## Emplacement

Source locale : `/home/laland/ai/intro/sigi-v2`.

Distribution : dossier `v2/` de la branche GitHub `v2/modular-foundation` du dépôt `Luwalker69/sigi`. La v1 reste à la racine et la branche `main` n'est pas remplacée. La documentation cible se trouve dans `docs/architecture-target.md` ; elle distingue la proposition complète du premier parcours exécutable.
