from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from llm_pipeline.attachments import (
    collect_attachments,
    render_attachments_for_prompt,
    skipped_attachment_summary,
)
from llm_pipeline.client import call_openai_compatible_chat, extract_answer_text
from llm_pipeline.config import load_config
from llm_pipeline.env import first_existing_env, load_env_file


@dataclass(frozen=True)
class PipelineRunResult:
    model_id: str
    provider_model: str
    api_key_env: str
    markdown_path: Path
    json_path: Path
    answer: str
    included_attachments: list[str]
    skipped_attachments: list[str]


def run_pipeline(
    root_dir: Path,
    prompt_path: Path,
    input_dir: Path,
    output_dir: Path,
    model_id: str | None = None,
) -> PipelineRunResult:
    load_env_file(root_dir / ".env")
    config = load_config(root_dir / "model_config.json")
    profile = config.get_model(model_id)
    api_key_env, api_key = first_existing_env(profile.api_key_env)

    prompt = prompt_path.read_text(encoding="utf-8").strip()
    attachments = collect_attachments(input_dir, config.text_attachment_max_chars)
    attachment_context = render_attachments_for_prompt(attachments)
    skipped = skipped_attachment_summary(attachments)

    user_content = _compose_user_content(prompt, attachment_context, skipped)
    messages = _build_messages(config.system_prompt, user_content)

    response = call_openai_compatible_chat(profile, config, api_key, messages)
    answer = extract_answer_text(response).strip()

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    safe_model_id = _safe_filename(profile.id)
    markdown_path = output_dir / f"{timestamp}_{safe_model_id}.md"
    json_path = output_dir / f"{timestamp}_{safe_model_id}.json"

    included = [attachment.relative_path for attachment in attachments if attachment.included]
    metadata = {
        "timestamp": timestamp,
        "model_id": profile.id,
        "display_name": profile.display_name,
        "provider": profile.provider,
        "provider_model": profile.resolved_model,
        "api_key_env": api_key_env,
        "prompt_path": str(prompt_path),
        "input_dir": str(input_dir),
        "included_attachments": included,
        "skipped_attachments": skipped,
    }

    markdown_path.write_text(
        _render_markdown(prompt, answer, metadata),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps({"metadata": metadata, "response": response}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return PipelineRunResult(
        model_id=profile.id,
        provider_model=profile.resolved_model,
        api_key_env=api_key_env,
        markdown_path=markdown_path,
        json_path=json_path,
        answer=answer,
        included_attachments=included,
        skipped_attachments=skipped,
    )


def _build_messages(system_prompt: str, user_content: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_content})
    return messages


def _compose_user_content(prompt: str, attachment_context: str, skipped: list[str]) -> str:
    sections = [prompt or "(No prompt was provided.)"]
    if attachment_context:
        sections.append(attachment_context)
    if skipped:
        sections.append("Skipped attachments:\n" + "\n".join(f"- {item}" for item in skipped))
    return "\n\n".join(sections)


def _render_markdown(prompt: str, answer: str, metadata: dict[str, Any]) -> str:
    included = metadata["included_attachments"] or ["None"]
    skipped = metadata["skipped_attachments"] or ["None"]
    return "\n".join(
        [
            "# Model Call Output",
            "",
            f"- Time: {metadata['timestamp']}",
            f"- Model: {metadata['model_id']} ({metadata['provider_model']})",
            f"- API key env: {metadata['api_key_env']}",
            "- Included attachments: " + ", ".join(included),
            "- Skipped attachments: " + ", ".join(skipped),
            "",
            "## Prompt",
            "",
            prompt or "(No prompt was provided.)",
            "",
            "## Answer",
            "",
            answer or "(No answer text returned.)",
            "",
        ]
    )


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return cleaned or "model"
