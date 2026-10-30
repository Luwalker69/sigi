"""Journal JSON atomique ; un pilote unique par mission."""

import json
import os
import tempfile
from pathlib import Path


class JsonRunStore:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def save(self, run: dict) -> None:
        descriptor, name = tempfile.mkstemp(prefix=".run-", dir=self.root)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(run, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.root / (run["id"] + ".json"))
        finally:
            if os.path.exists(name):
                os.unlink(name)
