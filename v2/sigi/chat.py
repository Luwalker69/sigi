"""Conversation au-dessus du moteur ; modèle et outils restent remplaçables."""

import json
import threading
import uuid
from decimal import Decimal

from .contracts import Reply
from .engine import Engine


class DemoChatModel:
    """Adaptateur d'essai de l'interface, explicitement sans IA."""

    name = "Démo sans IA"

    def reserve(self, *args):
        return Decimal(0)

    def cost(self, reply):
        return Decimal(0)

    def complete(self, messages, tools, limit):
        count = sum(message["role"] == "user" for message in messages)
        return Reply({"role": "assistant", "content":
            f"Démo sans IA : j'ai reçu ton message. Notre conversation contient {count} message(s) de ta part.\n\n"
            "Pour obtenir une vraie réponse de Gemini, lance l'interface sans --demo et connecte ta clé."}, 0, 0)


class ChatSession:
    def __init__(self, model, workspace, store, chat_store, limits):
        self.model, self.workspace, self.store, self.chat_store = model, workspace, store, chat_store
        self.limits = limits
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.id = str(uuid.uuid4())
        self.history, self.visible = [], []
        self.spent, self.reserved = Decimal(0), Decimal(0)

    def public_state(self):
        return {"id": self.id, "messages": list(self.visible), "spent_usd": str(self.spent),
                "reserved_usd": str(self.reserved), "budget_usd": str(self.limits["budget_usd"]),
                "model": self.model.name}

    def send(self, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 20000:
            raise ValueError("Message vide ou trop long (20 000 caractères maximum).")
        key = getattr(self.model, "key", "")
        if key and key in text:
            raise ValueError("La clé API ne doit pas être envoyée dans la conversation.")
        starting = self.spent + self.reserved
        run = Engine(self.model, self.workspace, self.store).run(
            text.strip(), str(self.limits["budget_usd"]), self.limits["max_turns"],
            self.limits["max_output_tokens"], history=self.history, previous_spent=str(starting))
        self.spent += Decimal(run["spent_usd"]) - starting
        self.reserved += Decimal(run["reserved_usd"])
        self.visible.append({"role": "user", "content": text.strip()})
        if run["status"] == "completed":
            self.history = run["messages"]
            response = run["output"]
        else:
            response = run.get("error") or {
                "budget_exhausted": "Budget de cette conversation atteint. Tu peux ouvrir une nouvelle conversation.",
                "budget_overrun": "Coût déclaré supérieur au budget : la conversation est arrêtée.",
                "turns_exhausted": "Limite d'étapes atteinte ; les actions déjà réalisées sont dans le journal.",
            }.get(run["status"], "La demande n'a pas abouti.")
        actions = [{"name": event["name"], "status": event["status"]} for event in run["events"] if event["type"] == "tool"]
        self.visible.append({"role": "assistant", "content": response, "status": run["status"], "actions": actions})
        record = self.public_state()
        # Conserver le contexte complet pour inspection ; la clé n'en fait jamais partie.
        record["history"] = self.history
        self.chat_store.save(record)
        return self.public_state()
