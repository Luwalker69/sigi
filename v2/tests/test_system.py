"""Contrôles de bout en bout, sans API externe ni modification du poste."""

import copy
import json
import tempfile
import threading
import unittest
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from sigi.contracts import Reply
from sigi.engine import Engine
from sigi.models import ChatModel, DemoModel
from sigi.store import JsonRunStore
from sigi.transport import RemoteWorkspace, post_json, validate_endpoint
from sigi.worker import server
from sigi.workspace import FileWorkspace


class MemoryStore:
    def __init__(self):
        self.saved = []

    def save(self, run):
        self.saved.append(copy.deepcopy(run))


class Serving:
    def __init__(self, service):
        self.service = service

    def __enter__(self):
        self.thread = threading.Thread(target=self.service.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.service.server_port}"

    def __exit__(self, *args):
        self.service.shutdown()
        self.service.server_close()
        self.thread.join()


class SystemTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).parent.parent / ".sigi" / "test-tmp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temporary_root)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        (self.workspace / "brief.txt").write_text("Un agent modulaire et économique.", encoding="utf-8")

    def test_demo_local_creates_real_report_and_journal(self):
        store = JsonRunStore(self.root / "runs")
        result = Engine(DemoModel(), FileWorkspace(self.workspace), store).run("Rapport")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["spent_usd"], "0")
        report = (self.workspace / "resultat.md").read_text(encoding="utf-8")
        self.assertIn("Un agent modulaire", report)
        self.assertEqual([e["status"] for e in result["events"] if e["type"] == "tool"], ["succeeded"] * 3)
        self.assertEqual(json.loads((store.root / (result["id"] + ".json")).read_text(encoding="utf-8")), result)

    def test_same_engine_works_with_http_worker(self):
        token = "test-worker-token-long-enough"
        with Serving(server(("127.0.0.1", 0), self.workspace, token)) as url:
            worker = RemoteWorkspace(url, token)
            result = Engine(DemoModel(), worker, MemoryStore()).run("Rapport")
            self.assertEqual(result["status"], "completed")
            self.assertTrue((self.workspace / "resultat.md").exists())
            with self.assertRaises(RuntimeError):
                RemoteWorkspace(url, "wrong-token-but-long-enough").invoke("list_files", {})

    def test_paths_and_existing_files_are_protected(self):
        workspace = FileWorkspace(self.workspace)
        for path in ("../workspace-other/secret.txt", "/etc/passwd", ".env", "folder/.secret", "C:/x"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                workspace.invoke("read_file", {"path": path})
        with self.assertRaises(FileExistsError):
            workspace.invoke("write_file", {"path": "brief.txt", "content": "écrasé"})
        with self.assertRaises(PermissionError):
            FileWorkspace(self.workspace, writable=False).invoke("write_file", {"path": "x", "content": "x"})

    def test_symlinks_cannot_escape(self):
        try:
            (self.workspace / "outside").symlink_to(self.root, target_is_directory=True)
        except OSError:
            self.skipTest("Création de liens symboliques indisponible sur cet hôte")
        with self.assertRaises(ValueError):
            FileWorkspace(self.workspace).invoke("read_file", {"path": "outside/secret.txt"})

    def test_budget_blocks_before_call(self):
        class Expensive(DemoModel):
            def reserve(self, *args):
                return Decimal("1")

            def complete(self, *args):
                raise AssertionError("Ne doit jamais être appelé")
        result = Engine(Expensive(), FileWorkspace(self.workspace), MemoryStore()).run("Test", "0.01")
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["events"], [])

    def test_uncertain_model_call_keeps_reservation_without_secret(self):
        class Broken(DemoModel):
            def reserve(self, *args):
                return Decimal("0.01")

            def complete(self, *args):
                raise RuntimeError("SECRET-MUST-NOT-APPEAR")
        result = Engine(Broken(), FileWorkspace(self.workspace), MemoryStore()).run("Test")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reserved_usd"], "0.01")
        self.assertNotIn("SECRET-MUST-NOT-APPEAR", json.dumps(result))

    def test_provider_payload_cost_and_secret_separation(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                received.append((self.path, self.headers["Authorization"], payload))
                body = json.dumps({"choices": [{"message": {"role": "assistant", "content": "Réponse simulée"},
                                                "finish_reason": "stop"}],
                                   "usage": {"prompt_tokens": 100, "completion_tokens": 20}}).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)
        with Serving(HTTPServer(("127.0.0.1", 0), Handler)) as url:
            model = ChatModel(url, "test-secret", "test-model", "1", "5")
            result = Engine(model, FileWorkspace(self.workspace), MemoryStore()).run("Test")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(Decimal(result["spent_usd"]), Decimal("0.0002"))
        self.assertEqual(received[0][0], "/chat/completions")
        self.assertEqual(received[0][1], "Bearer test-secret")
        self.assertNotIn("test-secret", json.dumps(result))
        self.assertEqual(received[0][2]["max_tokens"], 1024)

    def test_redirect_is_not_followed(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                received.append(self.path)
                self.send_response(307)
                self.send_header("Location", "/leak")
                self.end_headers()
        with Serving(HTTPServer(("127.0.0.1", 0), Handler)) as url:
            with self.assertRaises(RuntimeError):
                post_json(url + "/initial", "secret", {})
        self.assertEqual(received, ["/initial"])

    def test_remote_plaintext_and_invalid_rates_are_rejected(self):
        for url in ("http://example.org", "https://user:pass@example.org", "https://example.org?key=x"):
            with self.assertRaises(ValueError):
                validate_endpoint(url)
        for rate in ("0", "NaN", "-1"):
            with self.assertRaises(ValueError):
                ChatModel("https://example.org", "key", "model", rate, "1")


if __name__ == "__main__":
    unittest.main()
