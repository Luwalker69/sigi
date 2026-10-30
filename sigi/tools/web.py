"""Outil web minimal : récupérer une page, tronquée pour économiser le contexte."""

import httpx


def fetch(url: str, max_chars: int = 6000) -> str:
    """Télécharge une page et la tronque : le contexte est le budget le plus cher."""
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        response = client.get(url, headers={"User-Agent": "SIGI/0.1"})
        response.raise_for_status()
    return response.text[:max_chars]
