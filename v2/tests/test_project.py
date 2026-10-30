"""Accès au vrai projet via le moteur, sans modifier le code actif."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sigi.chat import ChatSession, DemoChatModel
from sigi.contracts import Reply
from sigi.engine import Engine
from sigi.project import AgentTools
from sigi.tool_registry import ToolRegistry
from sigi.workspace import FileWorkspace, spec
from test_system import MemoryStore


class ProjectTests(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).parent.parent / ".sigi" / "test-tmp"
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        (self.project / "sigi").mkdir(parents=True)
        (self.project / "pyproject.toml").write_text('[project]\nname="sigi-test"\n', encoding="utf-8")
        (self.project / "sigi" / "__init__.py").write_text('', encoding="utf-8")
        (self.project / "sigi" / "engine.py").write_text('class Engine:\n    pass\n', encoding="utf-8")
        (self.project / "CURRENT_STATE.md").write_text('Architecture cible : navigation Web future.\n', encoding="utf-8")
        self.output = self.root / "workspace"
        self.output.mkdir()
        self.tools = AgentTools(FileWorkspace(self.output), self.project)

    def test_catalog_and_context_distinguish_active_tools_from_future_capabilities(self):
        info = self.tools.invoke("agent_info", {})
        self.assertEqual(info["project_root"], str(self.project.resolve()))
        self.assertEqual(len(info["tools"]), 9)
        self.assertIn("navigation et recherche Web", info["not_available"])
        context = self.tools.system_context("test-provider")
        self.assertIn("test-provider", context)
        self.assertIn("project_read", context)
        self.assertNotIn("Architecture cible : navigation Web future.", context)

    def test_tree_and_reads_exclude_secrets_runtime_and_other_folders(self):
        for name in (".env", ".sigi/history.md", "essai/private.md", "data/private.md"):
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SECRET", encoding="utf-8")
        files = self.tools.invoke("project_tree", {})["files"]
        self.assertIn("sigi/engine.py", files)
        for path in (".env", ".sigi/history.md", "essai/private.md", "data/private.md", "../outside.md", "/etc/passwd"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.tools.invoke("project_read", {"path": path})
        self.assertFalse(any("private" in path for path in files))

    def test_read_pagination_and_search_are_grounded_in_source(self):
        source = self.project / "sigi" / "engine.py"
        read = self.tools.invoke("project_read", {"path": "sigi/engine.py"})
        self.assertIn("1: class Engine:", read["content"])
        self.assertEqual(read["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        matches = self.tools.invoke("project_search", {"query": "class engine"})["matches"]
        self.assertEqual(matches[0]["path"], "sigi/engine.py")
        self.assertEqual(matches[0]["line"], 1)
        source.write_text("\n".join(f"# line {index}" for index in range(250)), encoding="utf-8")
        self.assertIn("121: # line 120", self.tools.invoke("project_read", {"path": "sigi/engine.py", "start_line": 121})["content"])

    def test_syntax_check_does_not_execute_project_code(self):
        (self.project / "sigi" / "side_effect.py").write_text('raise RuntimeError("must not execute")\n', encoding="utf-8")
        result = self.tools.invoke("project_check_syntax", {})
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["executed_code"])
        self.assertIn("sigi/side_effect.py", result["checked"])

    def test_proposal_is_saved_separately_and_rejects_stale_source(self):
        old = self.tools.read("sigi/engine.py")
        new = 'class Engine:\n    enabled = True\n'
        result = self.tools.invoke("project_propose_change", {
            "path": "sigi/engine.py", "new_content": new, "expected_sha256": old["sha256"]})
        self.assertFalse(result["active_source_modified"])
        self.assertEqual((self.project / "sigi" / "engine.py").read_text(), 'class Engine:\n    pass\n')
        proposal = json.loads((self.output / result["proposal_path"]).read_text())
        self.assertEqual(proposal["new_content"], new)
        self.assertIn("+    enabled = True", proposal["diff"])
        with self.assertRaises(ValueError):
            self.tools.propose("sigi/engine.py", new, "wrong-sha")
        with self.assertRaises(ValueError):
            self.tools.propose("sigi/engine.py", "class : invalid", old["sha256"])

    def test_chat_can_inspect_and_propose_using_advertised_tools(self):
        class InspectModel(DemoChatModel):
            name = "inspect-test"

            def complete(model, messages, tools, limit):
                names = {tool["function"]["name"] for tool in tools}
                self.assertIn("project_read", names)
                self.assertIn("inspect-test", messages[0]["content"])
                observations = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
                actions = [("agent_info", {}), ("project_read", {"path": "sigi/engine.py"})]
                if len(observations) == 2:
                    actions.append(("project_propose_change", {"path": "sigi/engine.py", "new_content": "class Engine:\n    enabled = True\n",
                                                            "expected_sha256": observations[1]["sha256"]}))
                if len(observations) >= 3:
                    return Reply({"role": "assistant", "content": "Sources inspectées ; proposition non appliquée."}, 0, 0)
                name, arguments = actions[len(observations)]
                return Reply({"role": "assistant", "content": None, "tool_calls": [{"id": str(len(observations)), "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)}}]}, 0, 0)
        limits = {"budget_usd": "0.05", "max_turns": 8, "max_output_tokens": 1024}
        session = ChatSession(InspectModel(), self.tools, MemoryStore(), MemoryStore(), limits)
        state = session.send("Explore ton code et propose une amélioration.")
        self.assertEqual(state["messages"][-1]["status"], "completed")
        self.assertEqual([action["name"] for action in state["messages"][-1]["actions"]],
                         ["agent_info", "project_read", "project_propose_change"])
        self.assertEqual(len(list((self.output / "proposals").glob("*.json"))), 1)

    def test_new_tool_is_available_without_engine_modification(self):
        registry = ToolRegistry()
        registry.register(spec("hello", "Un outil ajouté.", {}, []), lambda: {"hello": True})
        class Model(DemoChatModel):
            def complete(model, messages, tools, limit):
                self.assertEqual([tool["function"]["name"] for tool in tools], ["hello"])
                if messages[-1]["role"] == "tool":
                    return Reply({"role": "assistant", "content": "Outil utilisé."}, 0, 0)
                return Reply({"role": "assistant", "content": None, "tool_calls": [{"id": "1", "type": "function",
                    "function": {"name": "hello", "arguments": "{}"}}]}, 0, 0)
        self.assertEqual(Engine(Model(), registry, MemoryStore()).run("Test")["status"], "completed")
        with self.assertRaises(ValueError):
            registry.invoke("hello", {"unexpected": "value"})
        with self.assertRaises(ValueError):
            registry.register(spec("hello", "Doublon.", {}, []), lambda: {})
