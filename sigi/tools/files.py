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
