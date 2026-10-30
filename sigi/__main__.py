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
