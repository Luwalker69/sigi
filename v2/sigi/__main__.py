"""CLI : démo gratuite, mission API, consultation du journal."""

import argparse
import os
import sys
import tomllib
import uuid
from pathlib import Path

from .engine import Engine
from .models import ChatModel, DemoModel
from .store import JsonRunStore
from .transport import RemoteWorkspace
from .workspace import FileWorkspace


def main() -> int:
    parser = argparse.ArgumentParser(prog="sigi")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Parcours déterministe sans IA")
    demo.add_argument("--state", type=Path, default=Path(".sigi"))
    live = sub.add_parser("run", help="Mission avec une vraie API")
    live.add_argument("task")
    live.add_argument("--config", type=Path, default=Path("config.example.toml"))
    live.add_argument("--workspace", type=Path)
    live.add_argument("--worker-url")
    live.add_argument("--state", type=Path, default=Path(".sigi"))
    inspect = sub.add_parser("inspect", help="Affiche un journal sauvegardé")
    inspect.add_argument("journal", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            print(args.journal.read_text(encoding="utf-8"))
            return 0
        store = JsonRunStore(args.state / "runs")
        if args.command == "demo":
            root = args.state / "demo" / str(uuid.uuid4())
            root.mkdir(parents=True)
            (root / "brief.txt").write_text("SIGI doit rester modulaire, économique et facile à reprendre.\n", encoding="utf-8")
            result = Engine(DemoModel(), FileWorkspace(root), store).run("Lis le brief et crée resultat.md.")
            print(f"Démonstration sans IA. Dossier : {root.resolve()}")
        else:
            if bool(args.workspace) == bool(args.worker_url):
                raise ValueError("Choisir exactement --workspace ou --worker-url.")
            config = tomllib.loads(args.config.read_text(encoding="utf-8"))
            cfg, limits = config["model"], config["limits"]
            model = ChatModel(cfg["endpoint"], os.environ.get(cfg["key_env"], ""), cfg["name"],
                              str(cfg["input_usd_per_million"]), str(cfg["output_usd_per_million"]))
            workspace = (RemoteWorkspace(args.worker_url, os.environ.get("SIGI_WORKER_TOKEN", ""))
                         if args.worker_url else FileWorkspace(args.workspace))
            result = Engine(model, workspace, store).run(args.task, str(limits["budget_usd"]),
                limits["max_turns"], limits["max_output_tokens"])
        print(result.get("output", result.get("error", result["status"])))
        print(f"État : {result['status']} | coût déclaré : {result['spent_usd']} USD")
        print(f"Journal : {(store.root / (result['id'] + '.json')).resolve()}")
        return 0 if result["status"] == "completed" else 1
    except (ValueError, KeyError, OSError) as error:
        print(f"Configuration invalide ({type(error).__name__}). Consulte README.md.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
