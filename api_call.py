from __future__ import annotations

import argparse
from pathlib import Path

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
    args = parser.parse_args()

    result = run_pipeline(
        root_dir=root_dir,
        prompt_path=_resolve_path(root_dir, args.prompt),
        input_dir=_resolve_path(root_dir, args.inputs),
        output_dir=_resolve_path(root_dir, args.outputs),
        model_id=args.model,
    )

    print(f"Model: {result.model_id} ({result.provider_model})")
    print(f"API key env: {result.api_key_env}")
    print(f"Included attachments: {len(result.included_attachments)}")
    print(f"Skipped attachments: {len(result.skipped_attachments)}")
    print(f"Saved markdown: {result.markdown_path}")
    print(f"Saved raw JSON: {result.json_path}")
    print()
    print(result.answer or "(No answer text returned.)")


def _resolve_path(root_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root_dir / path


if __name__ == "__main__":
    main()
