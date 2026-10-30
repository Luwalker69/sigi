"""Serveur de fichiers dédié ; proxy HTTPS nécessaire hors loopback."""

import argparse
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .workspace import FileWorkspace


def server(address: tuple[str, int], root: Path, token: str) -> HTTPServer:
    if len(token) < 24:
        raise ValueError("SIGI_WORKER_TOKEN doit contenir au moins 24 caractères.")
    workspace = FileWorkspace(root)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token):
                self.send_error(401)
                return
            if self.path != "/tool":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536:
                    raise ValueError("Taille invalide.")
                payload = json.loads(self.rfile.read(length))
                result = workspace.invoke(payload["name"], payload["arguments"])
            except (ValueError, KeyError, TypeError, OSError) as error:
                result = {"error": type(error).__name__ + " : opération refusée ou impossible"}
            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return HTTPServer(address, Handler)


def main():
    parser = argparse.ArgumentParser(description="Worker fichiers SIGI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    service = server((args.host, args.port), args.workspace, os.environ.get("SIGI_WORKER_TOKEN", ""))
    print(f"Worker fichiers sur {args.host}:{args.port}", flush=True)
    try:
        service.serve_forever()
    finally:
        service.server_close()


if __name__ == "__main__":
    main()
