from __future__ import annotations

import argparse
from pathlib import Path

from llm_pipeline.config import ModelProfile, load_config, save_default_model
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
            raise SystemExit("Usage: python .\\switch_model.py set <model_id>")
        _set_model(config_path, args.model_id)
        return

    _set_model(config_path, args.command)


def _show_current(config_path: Path) -> None:
    config = load_config(config_path)
    profile = config.get_model()
    api_key_name = first_existing_env_name(profile.api_key_env) or "missing"
    print(f"Current model: {profile.id}")
    _print_profile_details(profile, api_key_name)


def _list_models(config_path: Path) -> None:
    config = load_config(config_path)
    for profile in config.models.values():
        marker = "*" if profile.id == config.default_model else " "
        api_key_name = first_existing_env_name(profile.api_key_env) or "missing"
        print(
            f"{marker} {profile.id:<30} "
            f"model={profile.resolved_model:<18} "
            f"thinking={profile.thinking or 'default':<8} "
            f"effort={profile.reasoning_effort or 'default':<7} "
            f"max_tokens={profile.max_tokens or 'default':<8} "
            f"api_key={api_key_name}"
        )


def _set_model(config_path: Path, model_id: str) -> None:
    save_default_model(config_path, model_id)
    config = load_config(config_path)
    profile = config.get_model(model_id)
    api_key_name = first_existing_env_name(profile.api_key_env) or "missing"
    print(f"Default model set to: {profile.id}")
    _print_profile_details(profile, api_key_name)


def _print_profile_details(profile: ModelProfile, api_key_name: str) -> None:
    print(f"Display name: {profile.display_name}")
    print(f"Provider model: {profile.resolved_model}")
    print(f"Thinking: {profile.thinking or 'provider default'}")
    print(f"Reasoning effort: {profile.reasoning_effort or 'provider default'}")
    print(f"Max tokens: {profile.max_tokens or 'provider default'}")
    print(f"API key env: {api_key_name}")


if __name__ == "__main__":
    main()
