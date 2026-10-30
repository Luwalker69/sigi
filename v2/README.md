# SIGI v2 — des briques remplaçables

Premier parcours exécutable : modèle → outils fichiers → rapport → journal. Python 3.11 ou plus, sans dépendance à installer pour ce parcours.

**État : prototype alpha.** La démo est déterministe et n'utilise pas d'IA. L'adaptateur API existe mais aucun appel payant n'a été exécuté. Le worker HTTP a été testé sur loopback ; aucun serveur distant n'a été déployé.

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

Les neuf tests passent sous Ubuntu. Sous Windows : huit passent, un est ignoré lorsque les liens symboliques ne sont pas disponibles. Les tests n'appellent aucune API externe.

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
