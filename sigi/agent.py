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
