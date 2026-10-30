"""Transport JSON borné ; ne redirige jamais un jeton."""

import ipaddress
import json
import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .contracts import UserFacingError


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


KNOWN_REASONS = {
    "API_KEY_INVALID", "API_KEY_EXPIRED", "API_KEY_NOT_FOUND", "API_KEY_SERVICE_BLOCKED",
    "API_KEY_HTTP_REFERRER_BLOCKED", "API_KEY_IP_ADDRESS_BLOCKED", "SERVICE_DISABLED",
    "BILLING_DISABLED", "BILLING_NOT_ACTIVE", "CONSUMER_INVALID", "ACCESS_TOKEN_SCOPE_INSUFFICIENT",
}


class ServiceError(UserFacingError):
    """Diagnostic construit uniquement à partir de codes connus, jamais du corps brut."""

    def __init__(self, status: int | None = None, reason: str | None = None, kind: str = "network"):
        self.status = status
        self.reason = reason if reason in KNOWN_REASONS else None
        hints = {
            400: "Requête refusée : vérifier la clé, le modèle et les paramètres.",
            401: "Authentification refusée : saisir une clé API valide.",
            402: "Paiement requis : vérifier les crédits du projet dans Google AI Studio.",
            403: "Accès refusé : vérifier les restrictions de la clé et les droits du projet.",
            404: "Modèle ou URL introuvable : lancer la commande doctor.",
            429: "Quota ou limite de débit atteint : vérifier les quotas et la facturation du projet.",
        }
        network_hints = {
            "network": "Connexion impossible : vérifier la connexion, le proxy ou le pare-feu.",
            "tls": "Certificat TLS non validé : vérifier les certificats de Python/Conda ; ne pas désactiver TLS.",
            "dns": "Résolution DNS impossible : vérifier la connexion réseau.",
            "timeout": "Délai réseau dépassé ; le résultat de l'appel reste incertain.",
            "response": "Réponse du service illisible ou trop volumineuse.",
        }
        if status is not None:
            hint = hints.get(status, "Erreur temporaire du service." if status >= 500
                             else "Réponse HTTP refusée, sans redirection automatique.")
            prefix = f"HTTP {status}"
        else:
            hint, prefix = network_hints.get(kind, network_hints["network"]), "Réseau/API"
        if self.reason in {"API_KEY_INVALID", "API_KEY_EXPIRED", "API_KEY_NOT_FOUND"}:
            hint = "Clé API invalide ou expirée : créer une nouvelle clé dans Google AI Studio."
        elif self.reason == "SERVICE_DISABLED":
            hint = "API désactivée pour ce projet : vérifier le projet de la clé dans Google AI Studio."
        elif self.reason in {"BILLING_DISABLED", "BILLING_NOT_ACTIVE"}:
            hint = "Facturation inactive pour ce projet : vérifier Google AI Studio."
        self.public_message = prefix + (f" [{self.reason}]" if self.reason else "") + " : " + hint
        super().__init__(self.public_message)


def _http_diagnostic(error: HTTPError) -> ServiceError:
    reason = None
    try:
        body = json.loads(error.read(65536))
        details = body.get("error", {}).get("details", [])
        for detail in details if isinstance(details, list) else []:
            candidate = detail.get("reason") if isinstance(detail, dict) else None
            if isinstance(candidate, str) and candidate in KNOWN_REASONS:
                reason = candidate
                break
    except (ValueError, OSError, AttributeError, TypeError):
        pass
    finally:
        error.close()
    return ServiceError(error.code, reason)


def request_json(url: str, token: str, payload: dict | None = None) -> dict:
    validate_endpoint(url)
    request = Request(url, data=json.dumps(payload).encode("utf-8") if payload is not None else None,
                      method="POST" if payload is not None else "GET", headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with build_opener(NoRedirect()).open(request, timeout=60) as response:
            raw = response.read(2_000_001)
    except HTTPError as error:
        raise _http_diagnostic(error) from None
    except (URLError, TimeoutError, OSError) as error:
        cause = error.reason if isinstance(error, URLError) else error
        kind = ("tls" if isinstance(cause, ssl.SSLCertVerificationError) else
                "dns" if isinstance(cause, socket.gaierror) else
                "timeout" if isinstance(cause, TimeoutError) else "network")
        raise ServiceError(kind=kind) from None
    if len(raw) > 2_000_000:
        raise ServiceError(kind="response")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise ServiceError(kind="response") from None
    if not isinstance(value, dict):
        raise ServiceError(kind="response")
    return value


def post_json(url: str, token: str, payload: dict) -> dict:
    return request_json(url, token, payload)


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
