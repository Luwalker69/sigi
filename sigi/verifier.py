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
