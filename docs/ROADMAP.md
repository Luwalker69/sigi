# Feuille de route SIGI

## Phase 1 — MVP économique : mesurer le coût réel par tâche

Objectif : **mesurer avant de sophistiquer**. La cascade ne se règle qu'avec des chiffres réels.

- [ ] Installer la stack locale : `ollama pull qwen3:8b`, `docker build -t sigi-sandbox:latest .`
- [ ] Brancher LiteLLM avec deux tiers (local + cheap) et valider une première complétion
- [ ] Exécuter 10 tâches tests en `--solo` et relever le coût par tâche via le gouverneur
- [ ] Ajouter le traçage Langfuse (self-hosted) sur chaque appel `complete()`
- [ ] Régler `SIGI_TASK_BUDGET` à partir de la mesure, pas au doigt mouillé
- [ ] Vérifier que le taux d'escalade reste sous 60 % sur l'échantillon
- [ ] Garder `pytest -q` vert

**Critère de réussite** : le rapport `[budget]` affiche un coût par tâche stable et mesuré —
c'est la baseline de toutes les décisions des phases 2-3.

## Phase 2 — Cerveau complet

- [ ] Vérificateurs : schémas Pydantic, tests, relecture croisée branchés dans la cascade
- [ ] Superviseur : décomposition, sous-agents en parallèle, agrégation distillée
- [ ] Compaction mémoire entre sessions (`memory.compact`)
- [ ] AGENTS.md du projet écrit à la main et stabilisé

## Phase 3 — Capitalisation

- [ ] Skills auto-écrites : proposition après chaque tâche réussie, revue humaine au merge
- [ ] Passerelle Telegram
- [ ] RouteLLM si le tri par règles plafonne
- [ ] mem0 si la mémoire fichier devient limite
- [ ] LangGraph si les workflows exigent des checkpoints
