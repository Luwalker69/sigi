"""Gouverneur de budget : le compteur de vitesse du portefeuille."""


class Budget:
    """Plafond de tokens par tâche, dégradation douce, taux d'escalade en SLO."""

    DEGRADATION_ORDER = ["frontier", "cheap", "local"]

    def __init__(self, ceiling: int):
        self.ceiling = ceiling
        self.spent = 0
        self.calls: list[dict] = []

    def charge(self, tier: str, tokens_in: int, tokens_out: int) -> None:
        """Facture un appel et l'enregistre pour le rapport."""
        self.spent += tokens_in + tokens_out
        self.calls.append({"tier": tier, "in": tokens_in, "out": tokens_out})

    def degrade(self, tier: str) -> str:
        """Baisse d'un cran le niveau demandé si le plafond est dépassé."""
        if self.spent >= self.ceiling:
            index = self.DEGRADATION_ORDER.index(tier)
            return self.DEGRADATION_ORDER[min(index + 1, len(self.DEGRADATION_ORDER) - 1)]
        return tier

    @property
    def escalation_rate(self) -> float:
        """Part des appels servie par autre chose que le tier local."""
        if not self.calls:
            return 0.0
        escalated = sum(1 for call in self.calls if call["tier"] != "local")
        return escalated / len(self.calls)

    def report(self) -> str:
        """Une ligne, affichée après chaque tâche."""
        return (
            f"budget: {self.spent}/{self.ceiling} tokens, "
            f"escalade: {self.escalation_rate:.0%}"
        )
