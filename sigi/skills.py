"""Skills auto-écrites : l'expérience accumulée doit rapporter, pas coûter.

Chaque skill est un fichier Markdown avec en-tête YAML, registre de
coûts compris. La v1 sait charger et tenir le registre à jour ;
la proposition automatique de skills arrive en phase 3.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SKILLS_DIR = Path("skills")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

DEFAULT_LEDGER = {"calls": 0, "tokens": 0, "failures": 0}


@dataclass
class Skill:
    """Une procédure apprise, avec sa comptabilité."""

    name: str
    description: str = ""
    body: str = ""
    ledger: dict = field(default_factory=lambda: dict(DEFAULT_LEDGER))

    @property
    def cost_quality_ratio(self) -> float:
        """Tokens par usage réussi : plus bas = mieux amortie."""
        successes = max(1, self.ledger["calls"] - self.ledger["failures"])
        return self.ledger["tokens"] / successes

    @property
    def mature(self) -> bool:
        """Une skill qui a fait ses preuves au moins 3 fois."""
        return self.ledger["calls"] >= 3


def load_skills(directory: Path = SKILLS_DIR) -> dict[str, Skill]:
    """Charge les skills du registre local (les _templates sont ignorés)."""
    skills: dict[str, Skill] = {}
    if not directory.exists():
        return skills
    for path in sorted(directory.glob("*.md")):
        if path.name.startswith("_"):
            continue
        raw = path.read_text(encoding="utf-8")
        match = FRONTMATTER.match(raw)
        if not match:
            continue
        meta = yaml.safe_load(match.group(1)) or {}
        name = meta.get("name", path.stem)
        skills[name] = Skill(
            name=name,
            description=meta.get("description", ""),
            body=raw.split("---", 2)[-1].strip(),
            ledger={**DEFAULT_LEDGER, **(meta.get("cost_ledger") or {})},
        )
    return skills


def rank(skills: dict[str, Skill]) -> list[Skill]:
    """Trie les skills matures par meilleur ratio coût/qualité."""
    mature = [skill for skill in skills.values() if skill.mature]
    return sorted(mature, key=lambda skill: skill.cost_quality_ratio)


def record(skills: dict[str, Skill], name: str, tokens: int, ok: bool) -> None:
    """Met à jour le registre après un usage."""
    skill = skills.get(name)
    if skill is None:
        return
    skill.ledger["calls"] += 1
    skill.ledger["tokens"] += tokens
    if not ok:
        skill.ledger["failures"] += 1
