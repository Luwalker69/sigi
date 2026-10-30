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
