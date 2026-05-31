from __future__ import annotations

import argparse
from pathlib import Path

from llm_pipeline.history import latest_output_json
from llm_pipeline.runner import run_pipeline


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        prog="api_call",
        description="Run a local prompt + inputs/ model call.",
    )
    parser.add_argument("--model", help="Model id from model_config.json. Defaults to configured default_model.")
    parser.add_argument("--prompt", default="prompt.txt", help="Prompt file path.")
    parser.add_argument("--inputs", default="inputs", help="Directory containing attachment files.")
    parser.add_argument("--outputs", default="outputs", help="Directory for saved results.")
    parser.add_argument(
        "--continue-last",
        action="store_true",
        help="Continue from the latest JSON output in the outputs directory.",
    )
    parser.add_argument("--continue-from", help="Continue from a specific previous output JSON file.")
    args = parser.parse_args()
    if args.continue_last and args.continue_from:
        parser.error("Use either --continue-last or --continue-from, not both.")

    output_dir = _resolve_path(root_dir, args.outputs)
    continue_from = _resolve_continue_path(root_dir, output_dir, args.continue_from, args.continue_last)

    result = run_pipeline(
        root_dir=root_dir,
        prompt_path=_resolve_path(root_dir, args.prompt),
        input_dir=_resolve_path(root_dir, args.inputs),
        output_dir=output_dir,
        model_id=args.model,
        continue_from=continue_from,
    )

    print(f"Model: {result.model_id} ({result.provider_model})")
    print(f"API key env: {result.api_key_env}")
    print(f"Included attachments: {len(result.included_attachments)}")
    print(f"Skipped attachments: {len(result.skipped_attachments)}")
    print(f"Reasoning returned: {'yes' if result.reasoning else 'no'}")
    print(f"Usage: {_format_usage(result.usage)}")
    if result.continued_from:
        print(f"Continued from: {result.continued_from}")
    print(f"Saved markdown: {result.markdown_path}")
    print(f"Saved raw JSON: {result.json_path}")
    print()
    print(result.answer or "(No answer text returned.)")


def _resolve_path(root_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root_dir / path


def _resolve_continue_path(
    root_dir: Path,
    output_dir: Path,
    continue_from: str | None,
    continue_last: bool,
) -> Path | None:
    if continue_last:
        return latest_output_json(output_dir)
    if not continue_from:
        return None
    return _resolve_path(root_dir, continue_from)


def _format_usage(usage: dict[str, object]) -> str:
    if not usage:
        return "not returned by provider"

    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")
    reasoning_tokens = _nested_usage_value(usage, "completion_tokens_details", "reasoning_tokens")
    parts = []
    if prompt_tokens is not None:
        parts.append(f"prompt={prompt_tokens}")
    if completion_tokens is not None:
        parts.append(f"completion={completion_tokens}")
    if reasoning_tokens is not None:
        parts.append(f"reasoning={reasoning_tokens}")
    if total_tokens is not None:
        parts.append(f"total={total_tokens}")

    if parts:
        return ", ".join(parts)
    return ", ".join(f"{key}={value}" for key, value in usage.items())


def _nested_usage_value(usage: dict[str, object], section: str, key: str) -> object | None:
    value = usage.get(section)
    if isinstance(value, dict):
        return value.get(key)
    return None


if __name__ == "__main__":
    main()
