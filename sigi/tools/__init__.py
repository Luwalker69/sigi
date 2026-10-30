"""Outils de l'agent : fichiers, bash, web.

Règle d'or : chaque outil économise le contexte (sorties tronquées)
et confine le rayon d'explosion (prison de répertoire, sandbox).
"""

from . import bash, web  # noqa: F401
from .files import FileTools  # noqa: F401
