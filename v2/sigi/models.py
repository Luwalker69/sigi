"""Modèles remplaçables : démonstration et API Chat Completions."""

import json
from decimal import Decimal

from .contracts import Reply
from .transport import post_json, request_json, validate_endpoint


class ChatModel:
    def __init__(self, endpoint: str, key: str, name: str, input_rate: str, output_rate: str):
        validate_endpoint(endpoint)
        self.endpoint, self.key, self.name = endpoint.rstrip("/"), key.strip(), name
        self.input_rate, self.output_rate = Decimal(input_rate), Decimal(output_rate)
        if not self.key or not name:
            raise ValueError("Clé API et modèle nécessaires.")
        if any(character.isspace() for character in self.key) or not self.key.isascii():
            raise ValueError("La clé doit être saisie seule, sans espaces ni retours à la ligne.")
        if any(not rate.is_finite() or rate <= 0 for rate in (self.input_rate, self.output_rate)):
            raise ValueError("Tarifs positifs et finis requis.")

    def reserve(self, messages, tools, limit):
        # Estimation prudente en octets ; pas un compteur universel de tokens.
        size = len(json.dumps({"messages": messages, "tools": tools}).encode("utf-8")) + 4096
        return (size * self.input_rate + limit * self.output_rate) / Decimal(1_000_000)

    def cost(self, reply):
        return (reply.input_tokens * self.input_rate + reply.output_tokens * self.output_rate) / Decimal(1_000_000)

    def available_models(self) -> tuple[bool, bool]:
        """Vérifie les métadonnées, sans lancer de génération ni changer de modèle."""
        result = request_json(self.endpoint + "/models", self.key)
        rows = result.get("data")
        if not isinstance(rows, list):
            raise ValueError("Liste de modèles inattendue.")
        ids = {row["id"].removeprefix("models/") for row in rows
               if isinstance(row, dict) and isinstance(row.get("id"), str)}
        return self.name in ids, bool(result.get("has_more"))

    def complete(self, messages, tools, limit):
        result = post_json(self.endpoint + "/chat/completions", self.key, {
            "model": self.name, "messages": messages, "tools": tools, "max_tokens": limit})
        usage = result.get("usage", {})
        counts = [usage.get("prompt_tokens"), usage.get("completion_tokens")]
        if any(type(count) is not int or count < 0 for count in counts):
            raise ValueError("Usage absent ; réservation conservée.")
        choice = result["choices"][0]
        if choice.get("finish_reason") not in {"stop", "tool_calls"}:
            raise ValueError("Réponse incomplète ; réservation conservée.")
        return Reply(choice["message"], *counts)


class DemoModel:
    """Scénario sans IA ; les fichiers sont réellement lus et écrits."""

    name = "demo-sans-IA"

    def reserve(self, messages, tools, limit):
        return Decimal(0)

    def cost(self, reply):
        return Decimal(0)

    def complete(self, messages, tools, limit):
        observations = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        actions = [("list_files", {}), ("read_file", {"path": "brief.txt"})]
        if len(observations) == 2:
            brief = observations[1]["content"]
            actions.append(("write_file", {"path": "resultat.md", "content":
                "# Rapport de démonstration SIGI\n\nParcours déterministe sans appel IA.\n\n"
                + "## Brief réellement lu\n\n" + brief + "\n\n"
                + f"Nombre de mots : {len(brief.split())}\n\n"
                + "Fichiers observés : " + ", ".join(observations[0]["files"]) + "\n"}))
        if len(observations) < 3:
            name, arguments = actions[len(observations)]
            message = {"role": "assistant", "content": None, "tool_calls": [{
                "id": f"demo-{len(observations)}", "type": "function", "function": {
                    "name": name, "arguments": json.dumps(arguments)}}]}
        else:
            message = {"role": "assistant", "content": "Rapport créé dans resultat.md (démo sans IA)."}
        return Reply(message, 0, 0)
