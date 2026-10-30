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
