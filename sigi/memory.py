"""Mémoire hors contexte : fichiers + SQLite, jamais l'historique brut."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .llm import complete


class Memory:
    """Ce que SIGI apprend doit survivre aux sessions, hors de la fenêtre de contexte."""

    def __init__(self, root: str = "data/memory"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "memory.db")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS facts (key TEXT, text TEXT, created_at TEXT)"
        )
        self.db.commit()

    def remember(self, key: str, text: str) -> None:
        """Enregistre un fait durable."""
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "INSERT INTO facts (key, text, created_at) VALUES (?, ?, ?)", (key, text, now)
        )
        self.db.commit()

    def recall(self, query: str, limit: int = 5) -> list[str]:
        """Recherche par mots-clés ; les embeddings arrivent en phase 3."""
        words = query.lower().split()
        rows = self.db.execute("SELECT key, text FROM facts").fetchall()
        scored = [
            (sum(word in (key + " " + text).lower() for word in words), text)
            for key, text in rows
        ]
        scored.sort(key=lambda pair: -pair[0])
        return [text for score, text in scored if score > 0][:limit]

    def compact(self, messages: list[dict]) -> str:
        """Compaction : l'historique devient un résumé, pas un bagage."""
        transcript = "\n".join(message["content"] for message in messages)
        result = complete(
            "cheap",
            [
                {
                    "role": "system",
                    "content": "Résume en moins de 300 mots, en gardant décisions et faits.",
                },
                {"role": "user", "content": transcript[:30000]},
            ],
        )
        return result.text
