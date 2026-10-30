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
