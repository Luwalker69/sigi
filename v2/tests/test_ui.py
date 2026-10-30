"""Parcours navigateur par HTTP, contexte, budgets et frontières locales."""

import copy
import json
import re
import tempfile
import unittest
from decimal import Decimal
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlsplit

from sigi.chat import ChatSession, DemoChatModel
from sigi.contracts import Reply
from sigi.ui import make_server
from test_system import MemoryStore, Serving


class FakeModel(DemoChatModel):
    calls = []

    def __init__(self, endpoint, key, name, input_rate, output_rate):
        self.key, self.name = key, name

    def available_models(self):
        return True, False

    def reserve(self, *args):
        return Decimal("0.002")

    def cost(self, reply):
        return Decimal("0.001")

    def complete(self, messages, tools, limit):
        self.calls.append(copy.deepcopy(messages))
        users = [message["content"] for message in messages if message["role"] == "user"]
        return Reply({"role": "assistant", "content": "Premier message : " + users[0]}, 100, 20)


class UITests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).parent.parent / ".sigi" / "test-tmp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.config = {"model": {"endpoint": "https://example.org", "name": "test-model", "key_env": "TEST_KEY",
            "input_usd_per_million": "1", "output_usd_per_million": "1"},
            "limits": {"budget_usd": "0.05", "max_turns": 8, "max_output_tokens": 1024}}
        FakeModel.calls = []
        service = make_server(0, self.config, self.workspace, self.root / "state", model_factory=FakeModel)
        self.serving = Serving(service)
        self.url = self.serving.__enter__()
        self.addCleanup(self.serving.__exit__)
        self.cookie = ""
        status, body, headers = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.cookie = headers["Set-Cookie"].split(";", 1)[0]
        self.csrf = re.search(r'name="sigi-csrf" content="([^"]+)"', body).group(1)

    def request(self, method, path, payload=None, overrides=None):
        headers = {"Cookie": self.cookie}
        if method == "POST":
            headers.update({"Origin": self.url, "Content-Type": "application/json", "X-SIGI-CSRF": self.csrf})
        headers.update(overrides or {})
        address = urlsplit(self.url)
        connection = HTTPConnection(address.hostname, address.port, timeout=10)
        try:
            connection.request(method, path, body=json.dumps(payload) if payload is not None else None, headers=headers)
            response = connection.getresponse()
            raw = response.read().decode("utf-8")
            return response.status, raw, dict(response.getheaders())
        finally:
            connection.close()

    def post(self, path, payload):
        status, body, _ = self.request("POST", path, payload)
        return status, json.loads(body)

    def test_connect_two_messages_refresh_and_disconnect(self):
        status, state = self.post("/api/connect", {"key": "FAKE-PRIVATE-KEY"})
        self.assertEqual(status, 200)
        self.assertTrue(state["connected"])
        self.assertNotIn("FAKE-PRIVATE-KEY", json.dumps(state))
        self.assertEqual(self.post("/api/chat", {"message": "Je m'appelle Alice."})[0], 200)
        _, state = self.post("/api/chat", {"message": "Comment je m'appelle ?"})
        self.assertEqual(state["messages"][-1]["content"], "Premier message : Je m'appelle Alice.")
        self.assertEqual(state["spent_usd"], "0.002")
        self.assertEqual(len(FakeModel.calls[1]), 4)
        _, refreshed, _ = self.request("GET", "/api/state")
        self.assertEqual(len(json.loads(refreshed)["messages"]), 4)
        files = list((self.root / "state").rglob("*.json"))
        self.assertGreater(len(files), 0)
        for path in files:
            self.assertNotIn("FAKE-PRIVATE-KEY", path.read_text(encoding="utf-8"))
        _, state = self.post("/api/disconnect", {})
        self.assertFalse(state["connected"])
        self.assertEqual(self.post("/api/chat", {"message": "test"})[0], 401)

    def test_new_conversation_resets_context_and_budget_only_for_that_chat(self):
        self.post("/api/connect", {"key": "fake-key"})
        _, previous = self.post("/api/chat", {"message": "Ancienne conversation"})
        _, current = self.post("/api/new", {})
        self.assertNotEqual(current["id"], previous["id"])
        self.assertEqual(current["messages"], [])
        self.assertEqual(current["spent_usd"], "0")
        self.assertTrue((self.root / "state" / "chats" / (previous["id"] + ".json")).exists())

    def test_cross_origin_host_and_csrf_fail_before_any_api_call(self):
        for overrides in ({"Origin": "https://untrusted.example"}, {"X-SIGI-CSRF": "wrong"},
                          {"Host": "rebind.example"}, {"Content-Type": "text/plain"}):
            with self.subTest(headers=overrides):
                status, _, _ = self.request("POST", "/api/connect", {"key": "do-not-send"}, overrides)
                self.assertEqual(status, 403)
        self.assertEqual(FakeModel.calls, [])

    def test_browser_sessions_are_separate_and_key_in_chat_is_rejected(self):
        self.post("/api/connect", {"key": "FAKE-PRIVATE-KEY"})
        status, _ = self.post("/api/chat", {"message": "ma clé FAKE-PRIVATE-KEY"})
        self.assertEqual(status, 400)
        _, body, _ = self.request("GET", "/api/state", overrides={"Cookie": ""})
        self.assertNotIn("FAKE-PRIVATE-KEY", body)
        self.assertEqual(FakeModel.calls, [])

    def test_static_assets_and_headers(self):
        for path in ("/", "/app.js", "/styles.css"):
            status, _, headers = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
            self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.request("GET", "/../config.example.toml")[0], 404)

    def test_budget_accumulates_across_messages_and_blocks_before_next_call(self):
        class Model(FakeModel):
            def cost(self, reply):
                return Decimal("0.03")

            def reserve(self, *args):
                return Decimal("0.03")
        model = Model("", "", "", "", "")
        session = ChatSession(model, object(), MemoryStore(), MemoryStore(), self.config["limits"])
        self.assertEqual(session.send("premier")["spent_usd"], "0.03")
        state = session.send("second")
        self.assertEqual(len(FakeModel.calls), 1)
        self.assertEqual(state["spent_usd"], "0.03")
        self.assertEqual(state["messages"][-1]["status"], "budget_exhausted")

    def test_uncertain_reservations_are_carried_to_next_message(self):
        class Model(FakeModel):
            def reserve(self, *args):
                return Decimal("0.04")

            def complete(self, *args):
                raise RuntimeError("not-for-display")
        session = ChatSession(Model("", "", "", "", ""), object(), MemoryStore(), MemoryStore(), self.config["limits"])
        self.assertEqual(session.send("premier")["reserved_usd"], "0.04")
        state = session.send("second")
        self.assertEqual(state["messages"][-1]["status"], "budget_exhausted")
        self.assertEqual(state["reserved_usd"], "0.04")
        self.assertEqual(state["spent_usd"], "0.00")


if __name__ == "__main__":
    unittest.main()
