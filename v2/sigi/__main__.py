"""CLI : démo gratuite, mission API, consultation du journal."""

import argparse
import getpass
import os
import sys
import tomllib
import uuid
from pathlib import Path

from .engine import Engine
from .contracts import UserFacingError
from .models import ChatModel, DemoModel
from .store import JsonRunStore
from .transport import RemoteWorkspace
from .workspace import FileWorkspace


class ConfigurationError(ValueError):
    pass


def configured_model(config: dict, ask_key: bool = False) -> ChatModel:
    cfg = config["model"]
    key = os.environ.get(cfg["key_env"], "")
    if ask_key or not key.strip():
        if not sys.stdin.isatty():
            raise ConfigurationError("Clé API absente : lancer cette commande dans un terminal interactif.")
        key = getpass.getpass("Colle uniquement ta clé API puis appuie sur Entrée (saisie masquée) : ")
    if not key.strip():
        raise ConfigurationError("Aucune clé saisie.")
    if any(character.isspace() for character in key.strip()) or not key.strip().isascii():
        raise ConfigurationError("La clé doit être collée seule, sans commande, espace ou retour à la ligne.")
    return ChatModel(cfg["endpoint"], key, cfg["name"],
                     str(cfg["input_usd_per_million"]), str(cfg["output_usd_per_million"]))


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
    live.add_argument("--ask-key", action="store_true", help="Demande la clé en saisie masquée pour cette commande")
    doctor = sub.add_parser("doctor", help="Vérifie la clé et l'accès au modèle, sans génération")
    doctor.add_argument("--config", type=Path, default=Path("config.example.toml"))
    doctor.add_argument("--ask-key", action="store_true", help="Demande une clé sans utiliser celle du terminal")
    ui = sub.add_parser("ui", help="Ouvre un chat dans le navigateur, sur cet ordinateur")
    ui.add_argument("--config", type=Path, default=Path("config.example.toml"))
    ui.add_argument("--workspace", type=Path, default=Path("essai"))
    ui.add_argument("--state", type=Path, default=Path(".sigi"))
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument("--demo", action="store_true", help="Interface de démonstration sans IA ni API")
    inspect = sub.add_parser("inspect", help="Affiche un journal sauvegardé")
    inspect.add_argument("journal", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            print(args.journal.read_text(encoding="utf-8"))
            return 0
        if args.command == "ui":
            if not args.config.is_file():
                raise ConfigurationError("Configuration introuvable : se placer dans ~/ai/sigi/v2.")
            from .ui import serve
            config = tomllib.loads(args.config.read_text(encoding="utf-8"))
            try:
                serve(args.port, config, args.workspace, args.state, args.demo)
            except OSError:
                raise ConfigurationError("Impossible d'ouvrir le serveur local. Essaie --port 8766.") from None
            return 0
        if args.command in {"run", "doctor"}:
            if not args.config.is_file():
                raise ConfigurationError("Configuration introuvable : se placer dans ~/ai/sigi/v2.")
            config = tomllib.loads(args.config.read_text(encoding="utf-8"))
            if args.command == "run":
                if bool(args.workspace) == bool(args.worker_url):
                    raise ConfigurationError("Choisir exactement --workspace ou --worker-url.")
                if args.workspace and not args.workspace.is_dir():
                    raise ConfigurationError("Dossier workspace introuvable : créer essai et utiliser --workspace essai.")
            model = configured_model(config, args.ask_key)
            if args.command == "doctor":
                print("Clé chargée sans être affichée. Vérification des métadonnées du service…")
                available, has_more = model.available_models()
                if not available:
                    print("Connexion acceptée, mais le modèle configuré n'apparaît pas dans la liste reçue.")
                    if has_more:
                        print("La liste est paginée ; cela ne prouve pas que le modèle est absent.")
                    print("Aucun modèle ni tarif n'a été modifié. Aucune génération n'a été lancée.")
                    return 1
                print("Connexion acceptée ; modèle configuré présent dans la liste.")
                print("Aucune génération lancée. Le quota de génération n'est pas vérifié par ce diagnostic.")
                return 0
        store = JsonRunStore(args.state / "runs")
        if args.command == "demo":
            root = args.state / "demo" / str(uuid.uuid4())
            root.mkdir(parents=True)
            (root / "brief.txt").write_text("SIGI doit rester modulaire, économique et facile à reprendre.\n", encoding="utf-8")
            result = Engine(DemoModel(), FileWorkspace(root), store).run("Lis le brief et crée resultat.md.")
            print(f"Démonstration sans IA. Dossier : {root.resolve()}")
        else:
            limits = config["limits"]
            workspace = (RemoteWorkspace(args.worker_url, os.environ.get("SIGI_WORKER_TOKEN", ""))
                         if args.worker_url else FileWorkspace(args.workspace))
            result = Engine(model, workspace, store).run(args.task, str(limits["budget_usd"]),
                limits["max_turns"], limits["max_output_tokens"])
        print(result.get("output", result.get("error", result["status"])))
        print(f"État : {result['status']} | coût déclaré : {result['spent_usd']} USD")
        if result["reserved_usd"] != "0":
            print("Coût de l'appel interrompu non confirmé ; une réservation reste dans le journal.")
        print(f"Journal : {(store.root / (result['id'] + '.json')).resolve()}")
        return 0 if result["status"] == "completed" else 1
    except UserFacingError as error:
        print(error.public_message, file=sys.stderr)
        return 1
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print("Saisie interrompue ; clé non enregistrée.", file=sys.stderr)
        return 2
    except (ValueError, KeyError, OSError) as error:
        print(f"Configuration invalide ({type(error).__name__}). Consulte README.md.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
