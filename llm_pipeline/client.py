from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from llm_pipeline.config import ModelProfile, PipelineConfig


class ModelCallError(RuntimeError):
    """Raised when the remote model call fails."""


def call_openai_compatible_chat(
    profile: ModelProfile,
    config: PipelineConfig,
    api_key: str,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": profile.resolved_model,
        "messages": messages,
    }
    if profile.thinking:
        payload["thinking"] = {"type": profile.thinking}
    if profile.reasoning_effort:
        payload["reasoning_effort"] = profile.reasoning_effort
    if profile.temperature is not None and not profile.is_thinking_enabled:
        payload["temperature"] = profile.temperature
    if profile.max_tokens:
        payload["max_tokens"] = profile.max_tokens

    encoded_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(config.max_retries + 1):
        request = urllib.request.Request(
            profile.request_url,
            data=encoded_payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            detail = _read_http_error(exc)
            last_error = ModelCallError(f"HTTP {exc.code}: {detail}")
            if exc.code not in {408, 409, 429, 500, 502, 503, 504}:
                break
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc

        if attempt < config.max_retries:
            time.sleep(config.retry_backoff_seconds * (attempt + 1))

    raise ModelCallError(f"Model call failed after retries: {last_error}")


def extract_answer_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        return ""

    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part)

    return str(content)


def extract_reasoning_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        return ""

    message = choices[0].get("message") or {}
    reasoning_content = message.get("reasoning_content", "")
    if isinstance(reasoning_content, str):
        return reasoning_content
    return str(reasoning_content) if reasoning_content else ""


def _read_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - best-effort diagnostic only.
        return str(exc)
