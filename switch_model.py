from __future__ import annotations

import argparse
from pathlib import Path

from llm_pipeline.config import load_config, save_default_model
from llm_pipeline.env import first_existing_env_name, load_env_file


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    config_path = root_dir / "model_config.json"
    load_env_file(root_dir / ".env")

    parser = argparse.ArgumentParser(
        prog="switch_model",
        description="Show or switch the default model.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="show",
        help="show, list, set, or a model id to set directly.",
    )
    parser.add_argument("model_id", nargs="?", help="Model id when using: set <model_id>.")
    args = parser.parse_args()

    command = args.command.lower()
    if command == "list":
        _list_models(config_path)
        return
    if command == "show":
        _show_current(config_path)
        return
    if command == "set":
        if not args.model_id:
            raise SystemExit("Usage: python .\\切换模型.py set <model_id>")
        _set_model(config_path, args.model_id)
        return

    _set_model(config_path, args.command)


def _show_current(config_path: Path) -> None:
    config = load_config(config_path)
    profile = config.get_model()
    api_key_name = first_existing_env_name(profile.api_key_env) or "missing"
    print(f"Current model: {profile.id}")
    print(f"Display name: {profile.display_name}")
    print(f"Provider model: {profile.resolved_model}")
    print(f"API key env: {api_key_name}")


def _list_models(config_path: Path) -> None:
    config = load_config(config_path)
    for profile in config.models.values():
        marker = "*" if profile.id == config.default_model else " "
        api_key_name = first_existing_env_name(profile.api_key_env) or "missing"
        print(
            f"{marker} {profile.id:<20} "
            f"{profile.display_name:<22} "
            f"provider={profile.provider:<10} "
            f"api_key={api_key_name}"
        )


def _set_model(config_path: Path, model_id: str) -> None:
    save_default_model(config_path, model_id)
    config = load_config(config_path)
    profile = config.get_model(model_id)
    api_key_name = first_existing_env_name(profile.api_key_env) or "missing"
    print(f"Default model set to: {profile.id}")
    print(f"Provider model: {profile.resolved_model}")
    print(f"API key env: {api_key_name}")


if __name__ == "__main__":
    main()
