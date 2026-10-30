"""Passerelle LLM unique : tout passe par LiteLLM, jamais d'appel direct."""

from dataclasses import dataclass

import litellm

from .config import TIERS

litellm.suppress_debug_info = True


@dataclass
class LLMResult:
    """Une complétion, avec sa facture."""

    text: str
    tokens_in: int
    tokens_out: int
    model: str


def complete(tier: str, messages: list[dict], **kwargs) -> LLMResult:
    """Appelle l'étage demandé via LiteLLM et renvoie le texte + les tokens."""
    cfg = TIERS[tier]
    response = litellm.completion(model=cfg.model, messages=messages, **kwargs)
    usage = getattr(response, "usage", None)
    tokens_in = getattr(usage, "prompt_tokens", 0) or 0
    tokens_out = getattr(usage, "completion_tokens", 0) or 0
    text = response.choices[0].message.content or ""
    return LLMResult(text=text, tokens_in=tokens_in, tokens_out=tokens_out, model=cfg.model)
