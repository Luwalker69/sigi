"""Transport JSON borné ; ne redirige jamais un jeton."""

import ipaddress
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_endpoint(url: str) -> None:
    parsed = urlsplit(url)
    try:
        loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        loopback = parsed.hostname == "localhost"
    if (parsed.scheme != "https" and not (parsed.scheme == "http" and loopback)
            or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("HTTPS requis ; HTTP permis uniquement sur loopback.")


def post_json(url: str, token: str, payload: dict) -> dict:
    validate_endpoint(url)
    request = Request(url, data=json.dumps(payload).encode("utf-8"), method="POST", headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with build_opener(NoRedirect()).open(request, timeout=60) as response:
            raw = response.read(2_000_001)
    except HTTPError as error:
        raise RuntimeError(f"Service HTTP {error.code} ; corps de réponse masqué.") from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError("Service inaccessible ; résultat incertain, aucun nouvel essai automatique.") from None
    if len(raw) > 2_000_000:
        raise ValueError("Réponse trop volumineuse.")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Objet JSON attendu.")
    return value


class RemoteWorkspace:
    def __init__(self, url: str, token: str):
        validate_endpoint(url)
        if len(token) < 24:
            raise ValueError("Jeton worker trop court.")
        self.url, self.token = url.rstrip("/"), token

    def invoke(self, name: str, arguments: dict) -> dict:
        result = post_json(self.url + "/tool", self.token, {"name": name, "arguments": arguments})
        if "error" in result:
            raise ValueError(result["error"])
        return result
