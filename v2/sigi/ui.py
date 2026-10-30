"""Interface locale ; clés en mémoire, aucune exposition réseau configurable."""

import hmac
import json
import secrets
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .chat import ChatSession, DemoChatModel
from .contracts import UserFacingError
from .models import ChatModel
from .project import AgentTools
from .store import JsonRunStore
from .workspace import FileWorkspace

STATIC = Path(__file__).with_name("static")


def make_server(port, config, workspace, state, demo=False, model_factory=ChatModel, project_root=None):
    workspace = AgentTools(FileWorkspace(workspace), project_root)
    runs, chats = JsonRunStore(state / "runs"), JsonRunStore(state / "chats")
    clients, clients_lock = {}, threading.Lock()
    csrf = secrets.token_urlsafe(32)
    cfg, limits = config["model"], config["limits"]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(120)

        def allowed_host(self):
            host = self.headers.get("Host", "")
            return host if host in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"} else None

        def respond(self, status, data, kind="application/json; charset=utf-8", cookie=None):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8") if isinstance(data, dict) else data
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if cookie:
                self.send_header("Set-Cookie", f"sigi_client={cookie}; HttpOnly; SameSite=Strict; Path=/")
            self.end_headers()
            self.wfile.write(body)

        def client(self, create=False):
            cookie = SimpleCookie()
            try:
                cookie.load(self.headers.get("Cookie", ""))
            except Exception:
                pass
            identifier = cookie["sigi_client"].value if "sigi_client" in cookie else None
            with clients_lock:
                # Sessions inactives depuis une heure : oublier aussi la clé.
                now = time.monotonic()
                for key, value in list(clients.items()):
                    if now - value["seen"] > 3600 and not value["lock"].locked():
                        del clients[key]
                if identifier not in clients:
                    if not create or len(clients) >= 16:
                        return None, None
                    identifier = secrets.token_urlsafe(32)
                    chat = ChatSession(DemoChatModel(), workspace, runs, chats, limits) if demo else None
                    clients[identifier] = {"chat": chat, "seen": now, "lock": threading.Lock()}
                clients[identifier]["seen"] = now
                return identifier, clients[identifier]

        def state_of(self, client):
            chat = client["chat"]
            value = chat.public_state() if chat else {"messages": [], "model": cfg["name"],
                "spent_usd": "0", "reserved_usd": "0", "budget_usd": str(limits["budget_usd"])}
            return {**value, "connected": chat is not None, "demo": demo, "agent": workspace.info()}

        def do_GET(self):
            if not self.allowed_host():
                self.respond(403, {"error": "Adresse locale non autorisée."})
                return
            if self.path in {"/", "/app.js", "/styles.css"}:
                identifier, client = self.client(create=True)
                if client is None:
                    self.respond(503, {"error": "Trop de sessions locales."})
                    return
                name = "index.html" if self.path == "/" else self.path[1:]
                content = (STATIC / name).read_bytes()
                if name == "index.html":
                    content = content.replace(b"__CSRF__", csrf.encode("ascii"))
                kind = {"index.html": "text/html", "app.js": "text/javascript", "styles.css": "text/css"}[name]
                self.respond(200, content, kind + "; charset=utf-8", cookie=identifier)
                return
            _, client = self.client()
            if self.path == "/api/state" and client:
                self.respond(200, self.state_of(client))
            else:
                self.respond(404, {"error": "Session absente : actualise la page."})

        def do_POST(self):
            host = self.allowed_host()
            if (not host or self.headers.get("Origin") != "http://" + host
                    or not hmac.compare_digest(self.headers.get("X-SIGI-CSRF", ""), csrf)
                    or self.headers.get_content_type() != "application/json"):
                self.respond(403, {"error": "Requête locale non autorisée."})
                return
            _, client = self.client()
            if not client:
                self.respond(401, {"error": "Session expirée : actualise la page."})
                return
            if not client["lock"].acquire(blocking=False):
                self.respond(409, {"error": "Une réponse est déjà en cours."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 100000:
                    raise ValueError("Requête trop volumineuse.")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("Requête invalide.")
                if self.path == "/api/connect":
                    if demo:
                        raise ValueError("Connexion API désactivée dans la démonstration.")
                    key = payload.get("key")
                    if not isinstance(key, str) or not key.strip() or len(key) > 4096:
                        raise ValueError("Colle uniquement ta clé dans le champ prévu.")
                    model = model_factory(cfg["endpoint"], key, cfg["name"],
                        str(cfg["input_usd_per_million"]), str(cfg["output_usd_per_million"]))
                    available, _ = model.available_models()
                    if not available:
                        raise ValueError("Le modèle configuré n'apparaît pas dans la liste du service.")
                    client["chat"] = ChatSession(model, workspace, runs, chats, limits)
                elif self.path == "/api/disconnect":
                    client["chat"] = None
                elif not client["chat"]:
                    self.respond(401, {"error": "Connecte d'abord ta clé."})
                    return
                elif self.path == "/api/new":
                    client["chat"].reset()
                elif self.path == "/api/chat":
                    client["chat"].send(payload.get("message"))
                else:
                    self.respond(404, {"error": "Action inconnue."})
                    return
                self.respond(200, self.state_of(client))
            except UserFacingError as error:
                self.respond(400, {"error": error.public_message})
            except ValueError:
                self.respond(400, {"error": "Saisie invalide ou modèle indisponible. Vérifie le champ clé et le message."})
            except Exception:
                self.respond(500, {"error": "L'action a été interrompue. Actualise la page pour vérifier son état avant de réessayer."})
            finally:
                client["lock"].release()

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port, config, workspace, state, demo=False, project_root=None):
    workspace.mkdir(parents=True, exist_ok=True)
    service = make_server(port, config, workspace, state, demo, project_root=project_root)
    print(f"SIGI est prêt : http://127.0.0.1:{service.server_port}", flush=True)
    print("Ouvre cette adresse dans ton navigateur. Ctrl+C pour arrêter et oublier les clés.", flush=True)
    if demo:
        print("Mode démonstration : aucune IA ni API externe.", flush=True)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.server_close()
