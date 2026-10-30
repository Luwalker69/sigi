# AGENTS.md — SIGI

Instructions pour tout agent de code travaillant dans ce dépôt. Tenir ce fichier maigre (< 150 lignes).

## Commandes

- Installer : `pip install -e ".[dev]"`
- Tests : `pytest -q` — tout doit rester vert avant tout commit
- Sandbox : `docker build -t sigi-sandbox:latest .`
- Lancer : `python -m sigi "ta tâche" --solo`

## Carte du projet

- `sigi/agent.py` — boucle CodeAct du harnais (le cœur, ne pas alourdir)
- `sigi/cascade.py` — tri et escalade des modèles (principe : petit d'abord)
- `sigi/supervisor.py` — délégation à sous-agents à contexte isolé
- `sigi/budget.py` — gouverneur de tokens, dégradation douce
- `sigi/verifier.py` — barrière d'escalade (schémas, tests, relecture)
- `sigi/memory.py` — mémoire hors contexte + compaction
- `sigi/skills.py` — skills avec registre coût/qualité
- `sigi/tools/` — fichiers (prison de répertoire), bash (sandbox), web

## Conventions

- Français dans les docstrings et les messages ; identifiants en anglais, style snake_case.
- Un composant = un fichier ; pas de fichier au-delà de ~200 lignes.
- Toute nouvelle dépendance se justifie dans le message de commit.

## Contraintes

- Jamais de secret dans le code : tout passe par variables d'environnement (`.env` est ignoré).
- `bash.run()` doit rester confiné Docker en production (`SIGI_SANDBOX=docker`).
- Un taux d'escalade > 60 % est un bug de réglage, pas une fatalité.

## Anti-patterns

- Ne pas ajouter de framework d'orchestration en phases 1-2 (le harnais est le produit).
- Ne pas survérifier : chaque vérification coûte des tokens, deux types croisés suffisent.
- Ne pas agrandir ce fichier au-delà de ~150 lignes.
