"""Erreurs exploitables, sans corps brut, secret ou génération pendant doctor."""

import contextlib
import io
import json
import os
import socket
import ssl
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from urllib.error import URLError

from sigi.__main__ import ConfigurationError, configured_model, main
from sigi.engine import Engine
from sigi.models import ChatModel
from sigi.transport import ServiceError, post_json
from test_system import MemoryStore, Serving


class DiagnosticsTests(unittest.TestCase):
    def test_http_status_and_allowlisted_reason_reach_journal_without_secret(self):
        for status, reason in [(400, "API_KEY_INVALID"), (401, None), (402, None),
                               (403, "SERVICE_DISABLED"), (404, None), (429, None), (503, None)]:
            with self.subTest(status=status):
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self, *args):
                        pass

                    def do_POST(self):
                        body = json.dumps({"error": {"message": "SENSITIVE-DATA-MUST-STAY-HIDDEN",
                            "details": [{"reason": reason}, {"reason": "SENSITIVE-DATA-MUST-STAY-HIDDEN"}]}}).encode()
                        self.send_response(status)
                        self.end_headers()
                        self.wfile.write(body)
                with Serving(HTTPServer(("127.0.0.1", 0), Handler)) as url:
                    model = ChatModel(url, "fake-secret", "test-model", "1", "1")
                    result = Engine(model, object(), MemoryStore()).run("Test")
                self.assertEqual(result["status"], "failed")
                self.assertIn(f"HTTP {status}", result["error"])
                if reason:
                    self.assertIn(reason, result["error"])
                self.assertNotIn("SENSITIVE-DATA", json.dumps(result))
                self.assertNotIn("fake-secret", json.dumps(result))
                self.assertNotEqual(result["reserved_usd"], "0")

    def test_non_json_error_body_is_never_printed(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"<html>PRIVATE-KEY-IN-PROXY-PAGE</html>")
        with Serving(HTTPServer(("127.0.0.1", 0), Handler)) as url:
            with self.assertRaises(ServiceError) as caught:
                post_json(url, "secret", {})
        self.assertIn("HTTP 403", str(caught.exception))
        self.assertNotIn("PRIVATE-KEY", str(caught.exception))

    def test_tls_dns_and_timeout_are_identifiable_without_raw_exception(self):
        cases = [(ssl.SSLCertVerificationError("PRIVATE"), "TLS"),
                 (socket.gaierror("PRIVATE"), "DNS"), (TimeoutError("PRIVATE"), "Délai")]
        for cause, expected in cases:
            with self.subTest(expected=expected), patch("sigi.transport.build_opener") as opener:
                opener.return_value.open.side_effect = URLError(cause)
                with self.assertRaises(ServiceError) as caught:
                    post_json("https://example.org", "secret", {})
                self.assertIn(expected, str(caught.exception))
                self.assertNotIn("PRIVATE", str(caught.exception))

    def test_doctor_only_lists_metadata_and_does_not_generate(self):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                calls.append(("GET", self.path))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"data":[{"id":"models/test-model"}]}')

            def do_POST(self):
                calls.append(("POST", self.path))
                self.send_error(500)
        with Serving(HTTPServer(("127.0.0.1", 0), Handler)) as url:
            config_text = ('[model]\nendpoint="' + url + '"\nname="test-model"\n'
                           'key_env="SIGI_TEST_KEY"\ninput_usd_per_million="1"\noutput_usd_per_million="1"\n')
            with patch("sigi.__main__.Path.is_file", return_value=True), \
                 patch("sigi.__main__.Path.read_text", return_value=config_text), \
                 patch.dict(os.environ, {"SIGI_TEST_KEY": "fake-secret"}), \
                 patch("sys.argv", ["sigi", "doctor"]), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(), 0)
        self.assertEqual(calls, [("GET", "/models")])
        self.assertNotIn("fake-secret", output.getvalue())

    def test_hidden_prompt_overrides_stale_environment_and_does_not_save_key(self):
        config = {"model": {"endpoint": "https://example.org", "name": "test-model", "key_env": "SIGI_TEST_KEY",
                            "input_usd_per_million": "1", "output_usd_per_million": "1"}}
        with patch.dict(os.environ, {"SIGI_TEST_KEY": "stale"}), patch("sys.stdin.isatty", return_value=True), \
             patch("sigi.__main__.getpass.getpass", return_value="new-fake-key"):
            model = configured_model(config, ask_key=True)
            self.assertEqual(model.key, "new-fake-key")
            self.assertEqual(os.environ["SIGI_TEST_KEY"], "stale")
        with patch.dict(os.environ, {"SIGI_TEST_KEY": ""}), patch("sys.stdin.isatty", return_value=False):
            with self.assertRaises(ConfigurationError):
                configured_model(config)


if __name__ == "__main__":
    unittest.main()
