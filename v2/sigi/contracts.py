"""Contrats indépendants des fournisseurs et du transport."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class Reply:
    message: dict
    input_tokens: int
    output_tokens: int


class Model(Protocol):
    name: str
    def reserve(self, messages: list[dict], tools: list[dict], limit: int) -> Decimal: ...
    def complete(self, messages: list[dict], tools: list[dict], limit: int) -> Reply: ...
    def cost(self, reply: Reply) -> Decimal: ...


class Workspace(Protocol):
    def invoke(self, name: str, arguments: dict) -> dict: ...


class RunStore(Protocol):
    def save(self, run: dict) -> None: ...
