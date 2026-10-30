# SIGI v2 — des briques remplaçables

Premier parcours exécutable : modèle → outils fichiers → rapport → journal. Python 3.11 ou plus, sans dépendance à installer pour ce parcours.

## Le chat est l'interface de l'agent

SIGI reçoit désormais une identité technique fournie par le programme : sa version, le modèle utilisé, le dossier de ses propres sources et la liste des capacités réellement enregistrées. Il peut inspecter les fichiers de la v2 où il est installé, y compris ses modules, tests, interface et documentation. Le même catalogue d'outils est utilisé par la CLI et le chat ; ajouter un outil au registre ne demande pas de modifier le moteur.

| Outil | Capacité active |
|---|---|
| `agent_info` | Décrire l'agent et ses limites réelles |
| `project_tree` | Explorer ses sources et documents |
| `project_read` | Lire le code, avec lignes et empreinte du fichier |
| `project_search` | Rechercher un texte dans le projet |
| `project_check_syntax` | Analyser la syntaxe Python sans exécution |
| `project_propose_change` | Préparer une modification avec diff et contenu candidat |
| `list_files`, `read_file`, `write_file` | Travailler dans le dossier `essai` |

Les outils exécutés apparaissent sous la réponse dans le chat. Une modification proposée est enregistrée dans `essai/proposals/` avec l'empreinte de la version lue. Elle n'est pas appliquée au code actif et n'exécute pas de code généré. Les scripts, le Web, l'auto-déploiement et l'application automatique de ces propositions ne sont pas encore implémentés.

Les dossiers de sessions, clés, fichiers cachés et dossiers de travail sont exclus de l'exploration des sources. Les sources sont détectées à partir de l'installation, pas du dossier `essai`. Si la distribution ne contient pas les sources, `--project /chemin/vers/sigi/v2` permet de préciser le dossier ; l'inventaire signale sinon leur absence.

Exemples à demander à SIGI :

- « Lis ton état actuel et ton code, puis explique tes capacités en citant les fichiers. »
- « Cherche où sont gérés tes outils et explique le fonctionnement. »
- « Propose une amélioration simple de ta documentation, sans l'appliquer. »

**État : prototype alpha.** Le propriétaire a confirmé un premier échange réel avec Gemini, terminé avec un coût déclaré de 0,0001928 USD. La démo reste déterministe, sans IA, et les tests automatiques utilisent exclusivement des API simulées. Le worker HTTP a été testé sur loopback ; aucun serveur distant n'a été déployé.

## Discuter dans une interface simple

Dans Ubuntu :

```bash
cd ~/ai/sigi/v2
git pull --ff-only
python3 -B -m sigi ui
```

Ouvrir **http://127.0.0.1:8765** dans le navigateur Windows. Garder le terminal ouvert. Coller la clé Gemini dans le champ masqué, cliquer **Connecter**, puis écrire ses messages. La clé n'est demandée qu'une fois pendant la session et n'est pas sauvegardée sur disque. **Déconnecter** ou arrêter le serveur l'oublie ; une heure d'inactivité expire également la session.

Après une mise à jour, arrêter l'ancien serveur avec **Ctrl+C**, récupérer les changements, relancer `python3 -B -m sigi ui`, puis actualiser la page et reconnecter la clé. Un serveur Python déjà lancé ne charge pas automatiquement les nouveaux outils.

- Le modèle reçoit les messages précédents, pour une vraie conversation suivie.
- Le budget SIGI configuré (0,05 USD par défaut) porte sur l'ensemble de cette conversation. Le coût affiché vient des tarifs configurés et de l'usage déclaré par l'API ; ce n'est pas le solde de crédits Google.
- **Nouvelle conversation** démarre un nouveau contexte et une nouvelle enveloppe. Il n'y a pas encore de plafond global partagé entre toutes les conversations : régler aussi les limites du projet chez le fournisseur.
- Une actualisation conserve le chat tant que le serveur et sa session tournent. Les transcriptions sont enregistrées dans `.sigi/chats/`, mais leur restauration dans l'interface après arrêt du serveur reste à ajouter.
- Les clés restent dans le pilote local ; cette interface est volontairement limitée à loopback. Elle n'est pas un serveur à exposer sur Internet.

Pour essayer l'interface sans clé : `python3 -B -m sigi ui --demo`. Un bandeau indique clairement que les réponses de cette démonstration ne viennent pas d'une IA.

## Charger quelques crédits Gemini

La facturation se configure sur le projet Google de la clé, dans [Google AI Studio Billing](https://aistudio.google.com/billing). Google annonce un prépaiement minimum de 5 USD ou l'équivalent local ; le montant exact est affiché pendant le paiement. L'auto-recharge est optionnelle. Les délais de comptabilisation peuvent entraîner un dépassement du crédit ou du plafond choisi ; la limite n'est pas une coupure instantanée garantie. Le quota actuel peut suffire pour commencer.

[Documentation officielle de facturation](https://ai.google.dev/gemini-api/docs/billing).

## Essayer dans Ubuntu

Depuis ta copie du dépôt `sigi`, récupérer la branche :

```bash
git fetch origin
git switch v2/modular-foundation
cd v2
```

Depuis le dossier contenant ce README :

```bash
python3 -B -m sigi demo
```

SIGI crée un brief, le lit, écrit `resultat.md` et sauvegarde un journal. Chaque lancement utilise un nouveau dossier sous `.sigi/demo/` ; les chemins sont affichés dans le terminal.

```bash
python3 -B -m unittest discover -s tests -v
```

Les vingt-huit tests passent sous Ubuntu. Ils couvrent le contexte, le budget, les sessions et leurs clés, mais aussi le parcours complet d'inspection du projet et de préparation d'une modification depuis le chat. Les tests n'appellent aucune API externe.

## Diagnostiquer une erreur de connexion

Depuis ce dossier, lancer :

```bash
python3 -B -m sigi doctor --ask-key
```

Coller uniquement la clé quand Python la demande, puis appuyer sur Entrée. La saisie est masquée ; la clé n'est ni affichée ni enregistrée. Cette option remplace, pour cette seule commande, une éventuelle ancienne valeur dans le terminal. Il n'est pas nécessaire de taper `read` ou `export`.

`doctor` consulte seulement la liste des modèles : aucune génération n'est lancée. Une connexion acceptée ne garantit pas un quota de génération disponible. Si le modèle n'apparaît pas, aucun modèle ni tarif n'est changé automatiquement.

Les erreurs affichent désormais le statut HTTP et une explication construite sans corps de réponse brut : clé invalide, accès refusé, crédits requis, quota, modèle introuvable, certificats TLS, DNS ou connexion. Une réponse inconnue reste masquée. Ne pas désactiver la validation TLS pour contourner une erreur de certificat.

Après un diagnostic réussi, lancer une mission avec une saisie directe de la clé :

```bash
mkdir -p essai
python3 -B -m sigi run 'Bonjour, présente-toi brièvement.' --workspace essai --ask-key
```

Le dossier s'appelle `essai`. Une erreur de dossier est signalée avant de demander la clé. Les commandes suivantes qui utilisent `--ask-key` redemandent la clé ; cette version ne la sauvegarde pas sur le disque.

## Première mission avec une API

L'exemple configure Gemini via son endpoint compatible Chat Completions. La disponibilité du modèle et les tarifs doivent être revérifiés avant l'essai. La réponse réelle et la qualité des actions restent à valider avec une clé.

[Documentation Google](https://ai.google.dev/gemini-api/docs/openai) · [Tarifs](https://ai.google.dev/gemini-api/docs/pricing)

```bash
mkdir -p essai
printf '%s\n' 'Je veux un assistant modulaire et économique.' > essai/brief.txt
read -r -s -p 'Clé Gemini : ' GEMINI_API_KEY
export GEMINI_API_KEY
python3 -B -m sigi run 'Lis brief.txt et crée une synthèse dans synthese.md.' --workspace essai
```

La clé reste dans l'environnement du pilote ; ne pas la coller dans le chat ou un fichier du projet. Les journaux contiennent la mission et les observations de fichiers : ils restent privés, sous `.sigi/`, exclu de Git.

Le plafond est de 0,05 USD par mission dans `config.example.toml`. Il repose sur une réservation prudente avant l'appel et le coût déclaré par l'API. Ce n'est pas une garantie universelle de facturation : le compteur préalable estime les tokens, les tarifs sont configurables et certains fournisseurs facturent des éléments supplémentaires. Un dépassement déclaré arrête la mission avant toute autre action. Les limites du compte fournisseur complètent ce mécanisme.

## Utiliser les outils dans un autre processus

Terminal Ubuntu A, dans ce dossier :

```bash
mkdir -p atelier
read -r -s -p 'Jeton worker, au moins 24 caractères : ' SIGI_WORKER_TOKEN
export SIGI_WORKER_TOKEN
python3 -B -m sigi.worker --workspace atelier
```

Terminal B : définir le même `SIGI_WORKER_TOKEN` et la clé du modèle, puis :

```bash
python3 -B -m sigi run 'Liste les fichiers disponibles.' --worker-url http://127.0.0.1:8080
```

Le worker ne reçoit pas la clé du modèle. Son jeton autorise uniquement les trois outils fichiers de son espace de travail. Le code du modèle ne peut pas exécuter de shell ou de Python dans cette version.

Pour un hôte distant, HTTPS et un déploiement authentifié avec pare-feu sont nécessaires. Le client refuse HTTP hors loopback. Le serveur Python brut est destiné au banc d'essai derrière un proxy ; il n'est pas un service Internet de production.

`Dockerfile.worker` fournit une image non privilégiée avec un workspace dédié ; son build n'a pas été testé dans cet environnement, où Docker n'est pas disponible. L'isolation OpenShell/MicroVM reste une étape distincte. Ne pas monter un dossier personnel ou un socket Docker dans le worker.

## Réarranger les briques

| Brique | Contrat | Adaptateurs actuels |
|---|---|---|
| Modèle | `Model` | Démo et API compatible Chat Completions |
| Outils | `Workspace` | Dossier dédié ou worker HTTP |
| État des missions | `RunStore` | Fichiers JSON écrits atomiquement |
| Pilotage | `Engine` | Boucle bornée, coût, observations et journal |

Le branchement est dans `sigi/__main__.py`. Les adaptateurs n'appellent pas le moteur. On peut ajouter un fournisseur natif, un espace OpenShell ou un stockage PostgreSQL sans réécrire les autres adaptateurs. Les différences entre fournisseurs peuvent demander une adaptation du protocole : la même URL ne suffit pas toujours.

Le moteur actuel est un banc d'essai volontairement petit. OpenHands, Temporal et OpenShell ne sont pas installés ni intégrés. La prochaine intégration devra passer les mêmes scénarios avant de remplacer une brique existante.

## Pour reprendre après une pause

Lire [CURRENT_STATE.md](CURRENT_STATE.md), puis [les décisions](docs/decisions.md). Ils décrivent ce qui fonctionne, les limites et la prochaine étape.
