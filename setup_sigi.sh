#!/usr/bin/env bash
# ============================================================================
# setup_sigi.sh — Script d'amorçage du projet SIGI v0.1
# Généré le 29/10/2026 — Super Intelligence Générale Informatique
#
# Usage :
#   git clone https://github.com/Luwalker69/sigi.git
#   cd sigi
#   bash setup_sigi.sh
#
# Crée le squelette complet (24 fichiers), committe et pousse sur main.
# Les blocs de code des documents sont régénérés à la fin du script
# (placeholder @@@FENCE@@@ remplacé par trois backticks).
# ============================================================================
set -euo pipefail

echo "🧠 SIGI — amorçage du squelette v0.1..."

mkdir -p docs sigi/tools skills tests

# ─────────────────────────── README.md ───────────────────────────
cat > README.md <<'SIGI_EOF'
# SIGI 🧠⚡

**S**uper **I**ntelligence **G**énérale **I**nformatique

> Un agent maison **ultra performant à bas coût**. La philosophie en une phrase :
> *la qualité vient du contrôle, pas du prix du modèle.*

SIGI inverse le pattern dominant de 2026 : au lieu d'un grand modèle qui délègue vers le bas,
un **petit modèle monte vers le haut, et un vérificateur tient la barrière**.

## Les 5 principes

1. **Le petit modèle d'abord, le vérificateur décide** — 50 à 80 % des appels à un modèle de frontière
   pourraient passer par une gamme inférieure sans perte de qualité. On escalade uniquement si la
   vérification échoue (tests, schémas, relecture).
2. **Le contexte est le budget le plus cher** — sous-agents à contexte isolé, mémoire *hors* fenêtre
   de contexte, compaction systématique, AGENTS.md maigre (< 150 lignes, écrit à la main).
3. **Agir en code, pas en JSON** — les actions CodeAct sont plus compactes que les appels d'outils
   verbeux : moins de tokens, moins d'aller-retours, exécution vérifiable.
4. **Ce qui est appris une fois ne doit plus jamais coûter cher** — l'agent écrit ses propres skills,
   chacune avec un registre de coûts ; l'expérience accumulée rapporte au lieu de coûter.
5. **Toute action doit être vérifiable à peu de frais** — un petit modèle + un vérificateur fort
   bat souvent un grand modèle seul.

## Architecture

@@@FENCE@@@mermaid
flowchart TD
  U["Utilisateur<br/>CLI, Telegram ou Slack"] --> G["Gouverneur de budget<br/>plafond de tokens par tâche"]
  G --> O["Orchestrateur (superviseur)<br/>boucle CodeAct maison"]
  O --> T["Tri de tâche<br/>règles gratuites puis classifier léger"]
  T -->|"80% des cas"| C1["Modèle local ou bon marché<br/>Ollama : Qwen, GLM, DeepSeek<br/>ou API : Haiku, Flash"]
  T -->|"cas ambigus"| C2["Modèle intermédiaire"]
  T -->|"cas critiques déclarés"| C3["Modèle de frontière"]
  C1 --> V["Vérificateurs<br/>tests, schémas Pydantic, relecture"]
  C2 --> V
  V -->|"échec (max 2 essais)"| C3
  V -->|"succès"| S["Skills auto-écrites<br/>registre coût / qualité"]
  O --> SUB["Sous-agents spécialisés<br/>contexte isolé, résultats distillés"]
  O --> M["Mémoire hors contexte<br/>fichiers + SQLite + compaction"]
  O --> TOOLS["Outils MCP<br/>dans une sandbox Docker"]
@@@FENCE@@@

Le détail complet est dans [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Démarrage rapide

@@@FENCE@@@bash
git clone https://github.com/Luwalker69/sigi.git
cd sigi
pip install -e ".[dev]"

# Modèle local (coût marginal nul)
ollama pull qwen3:8b

# Sandbox d'exécution
docker build -t sigi-sandbox:latest .

# Clé API pour les étages bon marché / frontière
export ANTHROPIC_API_KEY=votre-cle

# Tests
pytest -q

# Premier vol
python -m sigi "résume le README du projet et propose 3 améliorations" --solo
@@@FENCE@@@

## Feuille de route

- **Phase 1 — MVP économique** : boucle + 2 modèles + 3 outils + Langfuse. *Objectif : mesurer le
  coût réel par tâche avant toute sophistication.*
- **Phase 2 — Cerveau complet** : superviseur, vérificateurs, gouverneur de budget, mémoire, compaction.
- **Phase 3 — Capitalisation** : skills auto-écrites, passerelle Telegram, RouteLLM, mem0, LangGraph.

## La pile (briques open source les plus adoptées de leur catégorie)

| Dépôt | Rôle dans SIGI |
|---|---|
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | Inspiration de la boucle CodeAct |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | Passerelle LLM : 100+ modèles, suivi des coûts |
| [ollama/ollama](https://github.com/ollama/ollama) | Modèles locaux gratuits (Qwen, GLM, DeepSeek, gpt-oss) |
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | Observabilité et évals auto-hébergées |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | Mémoire persistante (option, phase 3) |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | Navigation web en skill MCP (phase 3) |
| [agent0ai/agent-zero](https://github.com/agent0ai/agent-zero) | Patron de la sandbox Linux complète |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | Évolution si workflows complexes (phase 3+) |

## Budget visé (usage personnel, ~300 tâches/mois)

| Configuration | Coût mensuel estimé |
|---|---|
| Agent mono-modèle de frontière, sans harnais | 40-150 € |
| SIGI phase 1 (cascade + cache + compaction) | **3-15 €** |
| SIGI phase 3 (+ skills amorties + local nocturne) | **1-8 €** |

## Licence

MIT — voir [LICENSE](LICENSE).
SIGI_EOF

# ─────────────────────────── AGENTS.md ───────────────────────────
cat > AGENTS.md <<'SIGI_EOF'
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
SIGI_EOF

# ─────────────────────────── LICENSE ───────────────────────────
cat > LICENSE <<'SIGI_EOF'
MIT License

Copyright (c) 2026 Maël LALANDE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
SIGI_EOF

# ─────────────────────────── .gitignore ───────────────────────────
cat > .gitignore <<'SIGI_EOF'
__pycache__/
*.py[cod]
.venv/
venv/
.env
data/
*.db
.pytest_cache/
dist/
build/
*.egg-info/
SIGI_EOF

# ─────────────────────────── .env.example ───────────────────────────
cat > .env.example <<'SIGI_EOF'
# Copier vers .env (ignoré par git) et remplir.

# Modèles (identifiants LiteLLM)
SIGI_LOCAL_MODEL=ollama/qwen3:8b
SIGI_CHEAP_MODEL=anthropic/claude-haiku-4-5
SIGI_FRONTIER_MODEL=anthropic/claude-sonnet-4-6

# Gouverneur de budget : plafond de tokens par tâche
SIGI_TASK_BUDGET=60000

# Sandbox : "docker" (recommandé) ou "local" (développement uniquement)
SIGI_SANDBOX=docker

# Clés de providers (litellm lit l'environnement)
ANTHROPIC_API_KEY=
SIGI_EOF

# ─────────────────────────── Dockerfile ───────────────────────────
cat > Dockerfile <<'SIGI_EOF'
# Image sandbox de SIGI : le rayon d'explosion est le conteneur.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

CMD ["bash"]
SIGI_EOF

# ─────────────────────────── pyproject.toml ───────────────────────────
cat > pyproject.toml <<'SIGI_EOF'
[project]
name = "sigi"
version = "0.1.0"
description = "SIGI — Super Intelligence Générale Informatique : agent maison haute performance à bas coût."
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
dependencies = [
  "litellm>=1.100",
  "pydantic>=2.7",
  "PyYAML>=6.0",
  "httpx>=0.27",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
sigi = "sigi.__main__:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["sigi*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
SIGI_EOF

# ─────────────────────────── docs/ARCHITECTURE.md ───────────────────────────
cat > docs/ARCHITECTURE.md <<'SIGI_EOF'
# Architecture de SIGI

## Objectif

Un agent **ultra performant** sur des tâches réelles (code, recherche, automatisation),
**peu coûteux** à l'usage, assemblé uniquement à partir de briques open source éprouvées,
maintenable par une personne seule.

## L'inversion fondatrice

Le pattern dominant de 2026 : un modèle de frontière délègue vers le bas.
L'inversion de SIGI : **un petit modèle monte vers le haut, et un vérificateur tient la barrière**.
Les petits modèles coûtent jusqu'à 40 fois moins cher que la frontière ; 50 à 80 % des appels
n'ont pas besoin d'un grand modèle si la sortie est vérifiée autrement que par la confiance.

## Vue d'ensemble

@@@FENCE@@@mermaid
flowchart TD
  U["Utilisateur"] --> G["Gouverneur de budget"]
  G --> O["Orchestrateur superviseur"]
  O --> T["Tri de tâche (règles puis classifier)"]
  T --> C1["Tier local (Ollama)"]
  T --> C2["Tier bon marché (API)"]
  T --> C3["Tier frontière (API)"]
  C1 --> V["Vérificateurs"]
  C2 --> V
  V -->|"échec"| C3
  V -->|"succès"| OUT["Résultat + skill éventuelle"]
  O --> SUB["Sous-agents isolés"]
  O --> M["Mémoire hors contexte"]
  O --> TOOLS["Outils MCP sandboxés"]
@@@FENCE@@@

## La cascade de modèles

@@@FENCE@@@mermaid
sequenceDiagram
  participant Task as Tâche
  participant Rules as Règles (gratuit)
  participant Small as Petit modèle
  participant Verif as Vérificateur
  participant Big as Modèle frontière
  Task->>Rules: template connu ?
  Rules->>Small: sinon, tenter en petit
  Small-->>Verif: réponse + artefacts
  alt vérification passe
    Verif-->>Task: livré au coût minimal
  else vérification échoue (max 2 essais)
    Verif->>Big: escalade avec contexte distillé
    Big-->>Task: livré
  end
@@@FENCE@@@

Garde-fou critique : **le taux d'escalade est un SLO**. Une cascade qui escalade en silence
90 % du trafic coûte plus cher que pas de cascade du tout. Le gouverneur de budget
(`sigi/budget.py`) l'affiche en continu et dégrade doucement (frontière → intermédiaire → local)
en cas de dépassement du plafond de tokens, au lieu d'un échec brutal.

## Composants

| Fichier | Rôle | Principe |
|---|---|---|
| `agent.py` | Boucle CodeAct (~150 lignes, pas de framework) | Agir en code, pas en JSON |
| `cascade.py` | Tri par règles gratuites, puis escalade vérifiée | Petit modèle d'abord |
| `supervisor.py` | Décomposition, sous-agents en parallèle, agrégation distillée | Contexte isolé par sous-agent |
| `verifier.py` | Schémas Pydantic, tests, relecture croisée | La barrière d'escalade |
| `budget.py` | Plafond par tâche, dégradation douce, taux d'escalade | Compteur de vitesse du portefeuille |
| `memory.py` | Fichiers + SQLite, compaction des sessions | Mémoire hors contexte |
| `skills.py` | Chargement des skills, registre coût/qualité | L'expérience amortit son coût |
| `tools/` | Fichiers en prison de répertoire, bash sandboxé Docker, web tronqué | Rayon d'explosion : le conteneur |

## Skills auto-écrites

Chaque skill est un fichier Markdown avec un en-tête YAML contenant un **registre de coûts**
(`calls`, `tokens`, `failures`). L'orchestrateur préfère la skill au meilleur ratio coût/qualité ;
une skill trop coûteuse est candidate à réécriture. La phase 3 ajoute la proposition
automatique de skills après chaque tâche réussie.

## Pile externe

- **LiteLLM** : passerelle unique vers 100+ modèles, avec suivi des coûts intégré.
- **Ollama** : tier local gratuit (Qwen, GLM, DeepSeek, gpt-oss).
- **Langfuse** : traçage et évals auto-hébergées — indispensable pour régler la cascade.
- **Docker** : sandbox d'exécution.
- Chemins d'évolution : RouteLLM (routage économétrique), mem0 (mémoire production),
  LangGraph (workflows à checkpoints), passerelle multi-canaux façon OpenClaw.

## Budget visé

| Configuration | Coût mensuel estimé (usage personnel) |
|---|---|
| Mono-modèle de frontière sans harnais | 40-150 € |
| SIGI phase 1 | 3-15 € |
| SIGI phase 3 | 1-8 € |

Estimations d'ordre de grandeur fondées sur les retours de cascade 2025-2026
(50-85 % d'économies pour un système bien réglé ; le premier mois ne capture
que la moitié des économies finales).

## Risques et garde-fous

- **Cascade perverse** (escalade silencieuse) : surveillée par le gouverneur ; seuil d'alerte 60 %.
- **Vérificateur trop mou** : croiser deux types de vérification sur les tâches à enjeu.
- **Dérive des skills** : revue humaine au merge, façon pull request.
- **Sécurité** : aucun identifiant réel tant que la sandbox n'est pas activée.

## Pour aller plus loin

- [The best open source frameworks for building AI agents in 2026](https://www.firecrawl.dev/blog/best-open-source-agent-frameworks)
- [Multi-Agent Orchestration: 5 Patterns That Work](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work)
- [LLM Model Routing: Cost-Quality Optimization](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [Model Routing and Cascades](https://www.antm.ai/articles/model-routing-and-cascades-cheapest-model-good-enough)
- [Context Engineering for AI Agents](https://www.metacto.com/blogs/context-rich-environments-ai-agents)
- [The State of Agentic AI Standards in 2026](https://dev.to/alexmercedcoder/the-state-of-agentic-ai-standards-in-2026-mcp-a2a-webmcp-osi-and-the-protocol-stack-taking-3o2l)
- [Best Open Source AI Agents in 2026](https://rerun.build/blog/open-source-ai-agents)
SIGI_EOF

# ─────────────────────────── docs/ROADMAP.md ───────────────────────────
cat > docs/ROADMAP.md <<'SIGI_EOF'
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
SIGI_EOF

# ─────────────────────────── sigi/__init__.py ───────────────────────────
cat > sigi/__init__.py <<'SIGI_EOF'
"""SIGI — Super Intelligence Générale Informatique.

Agent maison haute performance à bas coût : cascade de modèles dirigée
par des vérificateurs, délégation à sous-agents à contexte isolé,
skills amorties et gouverneur de budget.
"""

__version__ = "0.1.0"
SIGI_EOF

# ─────────────────────────── sigi/config.py ───────────────────────────
cat > sigi/config.py <<'SIGI_EOF'
"""Configuration des modèles et des seuils, tout par variables d'environnement."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelTier:
    """Un étage de la cascade."""

    name: str
    model: str  # identifiant LiteLLM, ex. "ollama/qwen3:8b"


TIERS = {
    "local": ModelTier("local", os.getenv("SIGI_LOCAL_MODEL", "ollama/qwen3:8b")),
    "cheap": ModelTier("cheap", os.getenv("SIGI_CHEAP_MODEL", "anthropic/claude-haiku-4-5")),
    "frontier": ModelTier("frontier", os.getenv("SIGI_FRONTIER_MODEL", "anthropic/claude-sonnet-4-6")),
}

# Ordre d'escalade : petit modèle d'abord, toujours.
CASCADE = ["local", "cheap", "frontier"]

# Essais par étage avant de monter d'un cran.
ESCALATION_RETRIES = 2

# Plafond de tokens par tâche (gouverneur de budget).
AGENT_TOKEN_CEILING = int(os.getenv("SIGI_TASK_BUDGET", "60000"))

# "docker" confine bash.run() dans un conteneur ; "local" pour le développement.
SANDBOX = os.getenv("SIGI_SANDBOX", "docker")
SIGI_EOF

# ─────────────────────────── sigi/llm.py ───────────────────────────
cat > sigi/llm.py <<'SIGI_EOF'
"""Passerelle LLM unique : tout passe par LiteLLM, jamais d'appel direct."""

from dataclasses import dataclass

import litellm

from .config import TIERS

litellm.suppress_debug_info = True


@dataclass
class LLMResult:
    """Une complétion, avec sa facture."""

    text: str
    tokens_in: int
    tokens_out: int
    model: str


def complete(tier: str, messages: list[dict], **kwargs) -> LLMResult:
    """Appelle l'étage demandé via LiteLLM et renvoie le texte + les tokens."""
    cfg = TIERS[tier]
    response = litellm.completion(model=cfg.model, messages=messages, **kwargs)
    usage = getattr(response, "usage", None)
    tokens_in = getattr(usage, "prompt_tokens", 0) or 0
    tokens_out = getattr(usage, "completion_tokens", 0) or 0
    text = response.choices[0].message.content or ""
    return LLMResult(text=text, tokens_in=tokens_in, tokens_out=tokens_out, model=cfg.model)
SIGI_EOF

# ─────────────────────────── sigi/budget.py ───────────────────────────
cat > sigi/budget.py <<'SIGI_EOF'
"""Gouverneur de budget : le compteur de vitesse du portefeuille."""


class Budget:
    """Plafond de tokens par tâche, dégradation douce, taux d'escalade en SLO."""

    DEGRADATION_ORDER = ["frontier", "cheap", "local"]

    def __init__(self, ceiling: int):
        self.ceiling = ceiling
        self.spent = 0
        self.calls: list[dict] = []

    def charge(self, tier: str, tokens_in: int, tokens_out: int) -> None:
        """Facture un appel et l'enregistre pour le rapport."""
        self.spent += tokens_in + tokens_out
        self.calls.append({"tier": tier, "in": tokens_in, "out": tokens_out})

    def degrade(self, tier: str) -> str:
        """Baisse d'un cran le niveau demandé si le plafond est dépassé."""
        if self.spent >= self.ceiling:
            index = self.DEGRADATION_ORDER.index(tier)
            return self.DEGRADATION_ORDER[min(index + 1, len(self.DEGRADATION_ORDER) - 1)]
        return tier

    @property
    def escalation_rate(self) -> float:
        """Part des appels servie par autre chose que le tier local."""
        if not self.calls:
            return 0.0
        escalated = sum(1 for call in self.calls if call["tier"] != "local")
        return escalated / len(self.calls)

    def report(self) -> str:
        """Une ligne, affichée après chaque tâche."""
        return (
            f"budget: {self.spent}/{self.ceiling} tokens, "
            f"escalade: {self.escalation_rate:.0%}"
        )
SIGI_EOF

# ─────────────────────────── sigi/cascade.py ───────────────────────────
cat > sigi/cascade.py <<'SIGI_EOF'
"""Cascade petit-modèle-d'abord : la qualité vient du contrôle, pas du prix."""

import re

from .config import CASCADE, ESCALATION_RETRIES
from .llm import LLMResult, complete

# Règles gratuites : un template connu part directement au bon étage.
RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(diff|renomme|reformat|lint)\b", re.I), "local"),
    (re.compile(r"\b(résume|résumé|summar|traduis)\b", re.I), "local"),
    (re.compile(r"\b(typo|correction de bug simple)\b", re.I), "cheap"),
]

# Marqueurs déclaratifs : la tâche annonce elle-même ses enjeux.
CRITICAL_MARKERS = ("critique", "production", "paiement", "sécurité", "migration")


def classify(task: str) -> str:
    """Retourne l'étage de départ : 'local', 'cheap' ou 'frontier'."""
    for pattern, tier in RULES:
        if pattern.search(task):
            return tier
    if any(marker in task.lower() for marker in CRITICAL_MARKERS):
        return "frontier"
    return "cheap"


def default_prompt(task: str, last_verdict: str | None) -> list[dict]:
    """Construit le prompt d'étage, avec le verdict précédent si escalade."""
    messages = [{"role": "user", "content": task}]
    if last_verdict:
        messages.append(
            {
                "role": "user",
                "content": f"Tentative précédente jugée insuffisante: {last_verdict}. Corrige.",
            }
        )
    return messages


async def run_cascade(task, verifier, budget, start_tier=None) -> tuple[LLMResult, str]:
    """Essaie chaque étage ; n'escalade que si le vérificateur échoue.

    Args:
        task: la tâche à accomplir.
        verifier: coroutine (task, résultat) -> (bool, verdict).
        budget: gouverneur de tokens.
        start_tier: étage de départ forcé, sinon tri automatique.
    """
    tier = start_tier or classify(task)
    index = CASCADE.index(tier)
    verdict = None

    while index < len(CASCADE):
        tier = budget.degrade(CASCADE[index])
        for _ in range(ESCALATION_RETRIES):
            result = complete(tier, default_prompt(task, verdict))
            budget.charge(tier, result.tokens_in, result.tokens_out)
            ok, verdict = await verifier(task, result.text)
            if ok:
                return result, tier
        index += 1  # escalade : on monte d'un cran, verdict distillé dans le prompt

    return result, tier
SIGI_EOF

# ─────────────────────────── sigi/verifier.py ───────────────────────────
cat > sigi/verifier.py <<'SIGI_EOF'
"""Vérificateurs : la barrière d'escalade de la cascade."""

import json
import subprocess

from pydantic import BaseModel, ValidationError

from .llm import complete


def schema_check(schema: type[BaseModel], result: str) -> tuple[bool, str]:
    """Valide une sortie contre un modèle Pydantic."""
    try:
        schema.model_validate_json(result)
        return True, "schéma valide"
    except ValidationError as error:
        return False, f"schéma invalide: {error.errors()[:3]}"
    except json.JSONDecodeError:
        return False, "sortie non JSON"


def tests_check(command: str = "pytest -q") -> tuple[bool, str]:
    """Vérification mécanique : les tests passent, ou pas."""
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    return process.returncode == 0, process.stdout[-400:]


async def review_check(task: str, result: str) -> tuple[bool, str]:
    """Relecture par un petit modèle : croiser deux types de vérification."""
    verdict = complete(
        "cheap",
        [
            {
                "role": "system",
                "content": "Tu es un relecteur exigeant. Réponds strictement OK ou KO, puis une phrase.",
            },
            {"role": "user", "content": f"Tâche: {task}\n\nRésultat:\n{result[:4000]}"},
        ],
    )
    return verdict.text.strip().upper().startswith("OK"), verdict.text
SIGI_EOF

# ─────────────────────────── sigi/memory.py ───────────────────────────
cat > sigi/memory.py <<'SIGI_EOF'
"""Mémoire hors contexte : fichiers + SQLite, jamais l'historique brut."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .llm import complete


class Memory:
    """Ce que SIGI apprend doit survivre aux sessions, hors de la fenêtre de contexte."""

    def __init__(self, root: str = "data/memory"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "memory.db")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS facts (key TEXT, text TEXT, created_at TEXT)"
        )
        self.db.commit()

    def remember(self, key: str, text: str) -> None:
        """Enregistre un fait durable."""
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "INSERT INTO facts (key, text, created_at) VALUES (?, ?, ?)", (key, text, now)
        )
        self.db.commit()

    def recall(self, query: str, limit: int = 5) -> list[str]:
        """Recherche par mots-clés ; les embeddings arrivent en phase 3."""
        words = query.lower().split()
        rows = self.db.execute("SELECT key, text FROM facts").fetchall()
        scored = [
            (sum(word in (key + " " + text).lower() for word in words), text)
            for key, text in rows
        ]
        scored.sort(key=lambda pair: -pair[0])
        return [text for score, text in scored if score > 0][:limit]

    def compact(self, messages: list[dict]) -> str:
        """Compaction : l'historique devient un résumé, pas un bagage."""
        transcript = "\n".join(message["content"] for message in messages)
        result = complete(
            "cheap",
            [
                {
                    "role": "system",
                    "content": "Résume en moins de 300 mots, en gardant décisions et faits.",
                },
                {"role": "user", "content": transcript[:30000]},
            ],
        )
        return result.text
SIGI_EOF

# ─────────────────────────── sigi/agent.py ───────────────────────────
cat > sigi/agent.py <<'SIGI_EOF'
"""Le harnais : une boucle CodeAct minimale, sans framework.

Le modèle produit du code Python ; le harnais l'exécute dans un
espace de travail confiné et renvoie l'observation. Agir en code
économise les tokens des appels d'outils JSON verbeux.
"""

import re
from dataclasses import dataclass

from .budget import Budget
from .llm import complete
from .memory import Memory
from .tools import bash, web
from .tools.files import FileTools

# \x60 = backtick, pour repérer les blocs de code python du modèle.
CODE_BLOCK = re.compile(r"\x60\x60\x60python\n(.*?)\x60\x60\x60", re.DOTALL)

SYSTEM_PROMPT = """Tu es SIGI, un agent qui agit en code Python.
Outils disponibles dans l'espace de travail :
- files : read(path), write(path, content), list(path=".")
- bash  : run(command)  (sandbox ; SIGI_SANDBOX contrôle le confinement)
- web   : fetch(url)    (page tronquée pour économiser le contexte)

À chaque tour, écris UN unique bloc de code python : ta prochaine action.
Le code est exécuté et son résultat te sera renvoyé comme observation.
Quand tu as terminé, écris un bloc python qui contient exactement :
RESULT = "ta réponse finale"
N'improvise jamais un résultat : exécute pour vérifier."""


@dataclass
class AgentResult:
    """Sortie d'une exécution d'agent."""

    output: str
    turns: int
    tokens: int


class Agent:
    """Agent single-tâche, contexte minimal dédié."""

    def __init__(self, tier: str, budget: Budget, memory: Memory, max_turns: int = 12):
        self.tier = tier
        self.budget = budget
        self.memory = memory
        self.max_turns = max_turns

    async def run(self, task: str) -> AgentResult:
        files = FileTools()
        namespace: dict = {"files": files, "bash": bash, "web": web}
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]
        spent = 0

        for turn in range(1, self.max_turns + 1):
            tier = self.budget.degrade(self.tier)
            result = complete(tier, messages)
            self.budget.charge(tier, result.tokens_in, result.tokens_out)
            spent += result.tokens_in + result.tokens_out
            messages.append({"role": "assistant", "content": result.text})

            block = CODE_BLOCK.search(result.text)
            if not block:
                return AgentResult(result.text, turn, spent)

            # Exécution de l'action, sortie capturée et tronquée.
            lines: list[str] = []

            def _print(*args) -> None:
                lines.append(" ".join(str(arg) for arg in args))

            namespace["print"] = _print
            try:
                exec(block.group(1), namespace)  # noqa: S102 - espace de travail confiné
            except Exception as error:  # noqa: BLE001 - l'échec nourrit le tour suivant
                lines.append(f"ERREUR: {error!r}")

            if namespace.get("RESULT") is not None:
                output = str(namespace["RESULT"])
                self.memory.remember(task[:60], output)
                return AgentResult(output, turn, spent)

            observation = "\n".join(lines)[-4000:] or "(aucune sortie)"
            messages.append({"role": "user", "content": observation})

        return AgentResult("Budget de tours épuisé.", self.max_turns, spent)
SIGI_EOF

# ─────────────────────────── sigi/supervisor.py ───────────────────────────
cat > sigi/supervisor.py <<'SIGI_EOF'
"""Superviseur : délégation à sous-agents à contexte isolé (pattern défaut 2026).

Le superviseur décompose, les sous-agents ne se voient pas entre eux,
et l'agrégation distille. La délégation est un routage de contexte
autant qu'une répartition de travail.
"""

import asyncio
import json

from .agent import Agent, AgentResult
from .budget import Budget
from .llm import complete
from .memory import Memory

MAX_SUBAGENTS = 3


class Supervisor:
    """Orchestre des équipes éphémères d'agents spécialisés."""

    def __init__(self, budget: Budget, memory: Memory):
        self.budget = budget
        self.memory = memory

    async def decompose(self, task: str) -> list[str]:
        """Découpe la tâche en 2-3 sous-tâches indépendantes et non chevauchées."""
        result = complete(
            "cheap",
            [
                {
                    "role": "system",
                    "content": (
                        "Décompose la tâche en 2 à 3 sous-tâches indépendantes. "
                        "Réponds en JSON strict : {\"subtasks\": [\"...\"]} et rien d'autre."
                    ),
                },
                {"role": "user", "content": task},
            ],
        )
        self.budget.charge("cheap", result.tokens_in, result.tokens_out)
        try:
            subtasks = json.loads(result.text)["subtasks"]
        except (json.JSONDecodeError, KeyError):
            subtasks = [task]  # décomposition impossible : on ne bloque pas la tâche
        return subtasks[:MAX_SUBAGENTS]

    async def run(self, task: str) -> str:
        """Plan, exécution parallèle, synthèse distillée."""
        subtasks = await self.decompose(task)
        agents = [Agent("local", self.budget, self.memory) for _ in subtasks]
        results: list[AgentResult] = await asyncio.gather(
            *(agent.run(subtask) for agent, subtask in zip(agents, subtasks))
        )
        return await self.aggregate(task, [r.output for r in results])

    async def aggregate(self, task: str, outputs: list[str]) -> str:
        """Le parent ne reçoit que l'essentiel de chaque sous-agent."""
        corpus = "\n\n---\n\n".join(outputs)
        synthesis = complete(
            "cheap",
            [
                {"role": "system", "content": "Synthèse finale distillée, moins de 400 mots."},
                {
                    "role": "user",
                    "content": f"Tâche: {task}\n\nRésultats des sous-agents:\n{corpus[:12000]}",
                },
            ],
        )
        self.budget.charge("cheap", synthesis.tokens_in, synthesis.tokens_out)
        return synthesis.text
SIGI_EOF

# ─────────────────────────── sigi/skills.py ───────────────────────────
cat > sigi/skills.py <<'SIGI_EOF'
"""Skills auto-écrites : l'expérience accumulée doit rapporter, pas coûter.

Chaque skill est un fichier Markdown avec en-tête YAML, registre de
coûts compris. La v1 sait charger et tenir le registre à jour ;
la proposition automatique de skills arrive en phase 3.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SKILLS_DIR = Path("skills")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

DEFAULT_LEDGER = {"calls": 0, "tokens": 0, "failures": 0}


@dataclass
class Skill:
    """Une procédure apprise, avec sa comptabilité."""

    name: str
    description: str = ""
    body: str = ""
    ledger: dict = field(default_factory=lambda: dict(DEFAULT_LEDGER))

    @property
    def cost_quality_ratio(self) -> float:
        """Tokens par usage réussi : plus bas = mieux amortie."""
        successes = max(1, self.ledger["calls"] - self.ledger["failures"])
        return self.ledger["tokens"] / successes

    @property
    def mature(self) -> bool:
        """Une skill qui a fait ses preuves au moins 3 fois."""
        return self.ledger["calls"] >= 3


def load_skills(directory: Path = SKILLS_DIR) -> dict[str, Skill]:
    """Charge les skills du registre local (les _templates sont ignorés)."""
    skills: dict[str, Skill] = {}
    if not directory.exists():
        return skills
    for path in sorted(directory.glob("*.md")):
        if path.name.startswith("_"):
            continue
        raw = path.read_text(encoding="utf-8")
        match = FRONTMATTER.match(raw)
        if not match:
            continue
        meta = yaml.safe_load(match.group(1)) or {}
        name = meta.get("name", path.stem)
        skills[name] = Skill(
            name=name,
            description=meta.get("description", ""),
            body=raw.split("---", 2)[-1].strip(),
            ledger={**DEFAULT_LEDGER, **(meta.get("cost_ledger") or {})},
        )
    return skills


def rank(skills: dict[str, Skill]) -> list[Skill]:
    """Trie les skills matures par meilleur ratio coût/qualité."""
    mature = [skill for skill in skills.values() if skill.mature]
    return sorted(mature, key=lambda skill: skill.cost_quality_ratio)


def record(skills: dict[str, Skill], name: str, tokens: int, ok: bool) -> None:
    """Met à jour le registre après un usage."""
    skill = skills.get(name)
    if skill is None:
        return
    skill.ledger["calls"] += 1
    skill.ledger["tokens"] += tokens
    if not ok:
        skill.ledger["failures"] += 1
SIGI_EOF

# ─────────────────────────── sigi/tools/__init__.py ───────────────────────────
cat > sigi/tools/__init__.py <<'SIGI_EOF'
"""Outils de l'agent : fichiers, bash, web.

Règle d'or : chaque outil économise le contexte (sorties tronquées)
et confine le rayon d'explosion (prison de répertoire, sandbox).
"""

from . import bash, web  # noqa: F401
from .files import FileTools  # noqa: F401
SIGI_EOF

# ─────────────────────────── sigi/tools/files.py ───────────────────────────
cat > sigi/tools/files.py <<'SIGI_EOF'
"""Outils fichiers, enfermés dans un répertoire racine."""

from pathlib import Path


class FileTools:
    """Prison de répertoire : aucun accès en dehors de la racine."""

    def __init__(self, root: str = "data/workspace"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()
        if not str(target).startswith(str(self.root)):
            raise ValueError("chemin hors de la racine interdit")
        return target

    def read(self, path: str) -> str:
        return self._resolve(path).read_text(encoding="utf-8")

    def write(self, path: str, content: str) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"écrit {len(content)} caractères dans {path}"

    def list(self, path: str = ".") -> list[str]:
        base = self._resolve(path)
        return sorted(str(p.relative_to(self.root)) for p in base.rglob("*"))
SIGI_EOF

# ─────────────────────────── sigi/tools/bash.py ───────────────────────────
cat > sigi/tools/bash.py <<'SIGI_EOF'
"""Exécution de commandes, confinée au conteneur Docker quand il existe."""

import shutil
import subprocess

from ..config import SANDBOX


def run(command: str, timeout: int = 120) -> str:
    """Exécute une commande ; SIGI_SANDBOX=docker confine dans le conteneur."""
    if SANDBOX == "docker":
        wrapped = [
            "docker", "run", "--rm",
            "-v", f"{shutil.getcwd()}:/work", "-w", "/work",
            "sigi-sandbox:latest", "bash", "-lc", command,
        ]
    else:
        wrapped = ["bash", "-lc", command]

    process = subprocess.run(wrapped, capture_output=True, text=True, timeout=timeout)
    output = (process.stdout + process.stderr)[-8000:]
    return f"[exit {process.returncode}]\n{output}"
SIGI_EOF

# ─────────────────────────── sigi/tools/web.py ───────────────────────────
cat > sigi/tools/web.py <<'SIGI_EOF'
"""Outil web minimal : récupérer une page, tronquée pour économiser le contexte."""

import httpx


def fetch(url: str, max_chars: int = 6000) -> str:
    """Télécharge une page et la tronque : le contexte est le budget le plus cher."""
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        response = client.get(url, headers={"User-Agent": "SIGI/0.1"})
        response.raise_for_status()
    return response.text[:max_chars]
SIGI_EOF

# ─────────────────────────── sigi/__main__.py ───────────────────────────
cat > sigi/__main__.py <<'SIGI_EOF'
"""Point d'entrée : python -m sigi "ta tâche"."""

import argparse
import asyncio
import sys

from .budget import Budget
from .config import AGENT_TOKEN_CEILING
from .memory import Memory
from .supervisor import Supervisor


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sigi",
        description="SIGI — Super Intelligence Générale Informatique",
    )
    parser.add_argument("task", help="la tâche à accomplir")
    parser.add_argument("--solo", action="store_true", help="un seul agent, pas de superviseur")
    parser.add_argument("--budget", type=int, default=AGENT_TOKEN_CEILING, help="plafond de tokens")
    args = parser.parse_args()

    budget = Budget(args.budget)
    memory = Memory()

    if args.solo:
        from .agent import Agent

        result = asyncio.run(Agent("local", budget, memory).run(args.task))
        print(result.output)
    else:
        print(asyncio.run(Supervisor(budget, memory).run(args.task)))

    print(f"\n[budget] {budget.report()}", file=sys.stderr)


if __name__ == "__main__":
    main()
SIGI_EOF

# ─────────────────────────── skills/_template.md ───────────────────────────
cat > skills/_template.md <<'SIGI_EOF'
---
name: ma-skill
description: Une phrase — quand utiliser cette skill et ce qu'elle produit.
cost_ledger:
  calls: 0
  tokens: 0
  failures: 0
---

# Ma skill

## Quand l'utiliser

Décrire les déclencheurs précis, pas de généralités.

## Procédure

1. Étape minimale qui marche.
2. ...
3. Comment vérifier le résultat avant de livrer.

## Registre de coûts

Mis à jour par SIGI après chaque usage : `calls`, `tokens`, `failures`.
Une skill trop coûteuse est candidate à réécriture.
SIGI_EOF

# ─────────────────────────── tests/test_harness.py ───────────────────────────
cat > tests/test_harness.py <<'SIGI_EOF'
"""Tests du harnais : tri de cascade, gouverneur de budget, prison fichiers."""

import pytest

from sigi.budget import Budget
from sigi.cascade import classify
from sigi.skills import DEFAULT_LEDGER, Skill
from sigi.tools.files import FileTools


def test_tache_triviale_part_en_local():
    assert classify("résume ce fichier") == "local"


def test_tache_critique_declaree_part_en_frontiere():
    assert classify("migration critique de la base de production") == "frontier"


def test_par_defaut_le_tier_bon_marche():
    assert classify("rédige un email de relance") == "cheap"


def test_budget_degrade_au_dela_du_plafond():
    budget = Budget(ceiling=100)
    budget.charge("frontier", 60, 60)
    assert budget.degrade("frontier") == "cheap"
    assert budget.degrade("cheap") == "local"


def test_taux_escalade_est_un_slo():
    budget = Budget(ceiling=1000)
    budget.charge("local", 1, 1)
    budget.charge("local", 1, 1)
    assert budget.escalation_rate == 0.0


def test_fichiers_enfermes_dans_la_racine(tmp_path):
    files = FileTools(root=str(tmp_path))
    files.write("a.txt", "bonjour")
    assert files.read("a.txt") == "bonjour"
    with pytest.raises(ValueError):
        files.read("../secret.txt")


def test_skill_mature_au_meilleur_ratio():
    mature = Skill("a", ledger={"calls": 10, "tokens": 1000, "failures": 0})
    jeune = Skill("b", ledger=dict(DEFAULT_LEDGER))
    assert mature.mature and not jeune.mature
    assert mature.cost_quality_ratio == 100.0
SIGI_EOF

# ─────────────────────────── restauration des blocs markdown ───────────────────────────
F=$(printf '\140\140\140')
sed -i "s/@@@FENCE@@@/$F/g" README.md docs/ARCHITECTURE.md

# ─────────────────────────── commit et push ───────────────────────────
if [ ! -d .git ]; then
  echo "Pas un dépôt git ici : initialisation et liaison au remote."
  git init
  git branch -M main
  git remote add origin https://github.com/Luwalker69/sigi.git
fi

git add -A
git commit -m "feat: bootstrap SIGI v0.1 — harnais CodeAct, cascade, superviseur, budget, skills, mémoire" \
  || echo "Rien à committer."
git push -u origin main

echo ""
echo "🦐 SIGI v0.1 est en place. Prochaines étapes (voir docs/ROADMAP.md) :"
echo "   pip install -e \".[dev]\" && pytest -q"
echo "   ollama pull qwen3:8b && docker build -t sigi-sandbox:latest ."
echo "   python -m sigi \"résume le README et propose 3 améliorations\" --solo"
