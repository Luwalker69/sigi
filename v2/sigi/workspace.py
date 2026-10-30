"""Outils fichiers bornés ; aucune exécution de code ou de commande."""

import os
from pathlib import Path


def spec(name, description, properties, required):
    return {"type": "function", "function": {"name": name, "description": description,
        "parameters": {"type": "object", "properties": properties,
                       "required": required, "additionalProperties": False}}}


TOOL_SPECS = [
    spec("list_files", "Liste les fichiers visibles du workspace.", {}, []),
    spec("read_file", "Lit un petit fichier texte.", {"path": {"type": "string"}}, ["path"]),
    spec("write_file", "Crée un fichier sans écraser l'existant.", {
        "path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
]


class FileWorkspace:
    def __init__(self, root: Path, writable: bool = True):
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("Le workspace doit être un dossier existant.")
        self.writable = writable

    def _path(self, value: str) -> Path:
        if not isinstance(value, str) or not value or "\\" in value or ":" in value:
            raise ValueError("Chemin relatif POSIX attendu.")
        relative = Path(value)
        if relative.is_absolute():
            raise ValueError("Chemin absolu interdit.")
        current = self.root
        for part in relative.parts:
            if part.startswith(".") or part.lower().endswith((".pem", ".key")):
                raise ValueError("Chemin caché ou sensible interdit.")
            current = current / part
            if current.is_symlink():
                raise ValueError("Lien symbolique interdit.")
        target = current.resolve()
        if not target.is_relative_to(self.root) or target == self.root:
            raise ValueError("Chemin hors du workspace.")
        return target

    def invoke(self, name: str, arguments: dict) -> dict:
        if not isinstance(arguments, dict):
            raise ValueError("Arguments objet attendus.")
        if name == "list_files":
            if arguments:
                raise ValueError("Aucun argument attendu.")
            names = []
            for base, directories, files in os.walk(self.root, followlinks=False):
                directories[:] = sorted(d for d in directories if not d.startswith(".")
                                        and not (Path(base) / d).is_symlink())
                for filename in sorted(files):
                    relative = (Path(base) / filename).relative_to(self.root).as_posix()
                    try:
                        self._path(relative)
                    except ValueError:
                        continue
                    names.append(relative)
                    if len(names) >= 200:
                        return {"files": names, "truncated": True}
            return {"files": names, "truncated": False}
        if name not in {"read_file", "write_file"}:
            raise ValueError("Outil inconnu.")
        expected = {"path"} if name == "read_file" else {"path", "content"}
        if set(arguments) != expected:
            raise ValueError("Arguments inattendus ou manquants.")
        path = self._path(arguments["path"])
        if name == "read_file":
            with path.open("rb") as stream:
                raw = stream.read(12001)
            return {"path": arguments["path"], "content": raw[:12000].decode("utf-8", errors="replace"),
                    "truncated": len(raw) > 12000}
        content = arguments["content"]
        if not self.writable:
            raise PermissionError("Écriture désactivée.")
        if not isinstance(content, str) or len(content.encode("utf-8")) > 32000:
            raise ValueError("Contenu limité à 32 Ko.")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
        return {"path": arguments["path"], "bytes": len(content.encode("utf-8")), "created": True}
