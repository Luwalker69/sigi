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
