from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    """Raised when model configuration is missing or invalid."""


@dataclass(frozen=True)
class ModelProfile:
    id: str
    display_name: str
    provider: str
    base_url: str
    endpoint: str
    model: str
    api_key_env: tuple[str, ...]
    temperature: float = 0.2
    max_tokens: int | None = None
    model_env: str | None = None

    @property
    def request_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.endpoint.lstrip('/')}"

    @property
    def resolved_model(self) -> str:
        if self.model_env:
            override = os.getenv(self.model_env)
            if override:
                return override
        return self.model


@dataclass(frozen=True)
class PipelineConfig:
    default_model: str
    system_prompt: str
    timeout_seconds: int
    max_retries: int
    retry_backoff_seconds: float
    text_attachment_max_chars: int
    models: dict[str, ModelProfile]

    def get_model(self, model_id: str | None = None) -> ModelProfile:
        selected = model_id or self.default_model
        try:
            return self.models[selected]
        except KeyError as exc:
            available = ", ".join(sorted(self.models))
            raise ConfigError(f"Unknown model '{selected}'. Available: {available}") from exc


def load_config(path: Path) -> PipelineConfig:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    models = [_parse_model(item) for item in data.get("models", [])]
    if not models:
        raise ConfigError("model_config.json must contain at least one model.")

    model_map = {model.id: model for model in models}
    default_model = str(data.get("default_model", "")).strip()
    if default_model not in model_map:
        available = ", ".join(sorted(model_map))
        raise ConfigError(f"default_model '{default_model}' is not configured. Available: {available}")

    return PipelineConfig(
        default_model=default_model,
        system_prompt=str(data.get("system_prompt", "")).strip(),
        timeout_seconds=int(data.get("timeout_seconds", 120)),
        max_retries=int(data.get("max_retries", 2)),
        retry_backoff_seconds=float(data.get("retry_backoff_seconds", 1.5)),
        text_attachment_max_chars=int(data.get("text_attachment_max_chars", 120000)),
        models=model_map,
    )


def save_default_model(path: Path, model_id: str) -> None:
    config = load_config(path)
    config.get_model(model_id)

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    data["default_model"] = model_id
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _parse_model(data: dict[str, Any]) -> ModelProfile:
    required = ["id", "provider", "base_url", "endpoint", "model", "api_key_env"]
    missing = [name for name in required if name not in data]
    if missing:
        raise ConfigError(f"Model entry is missing fields: {', '.join(missing)}")

    api_key_env = data["api_key_env"]
    if not isinstance(api_key_env, list) or not api_key_env:
        raise ConfigError(f"Model '{data.get('id')}' api_key_env must be a non-empty list.")

    model_id = str(data["id"])
    return ModelProfile(
        id=model_id,
        display_name=str(data.get("display_name") or model_id),
        provider=str(data["provider"]),
        base_url=str(data["base_url"]),
        endpoint=str(data["endpoint"]),
        model=str(data["model"]),
        model_env=str(data["model_env"]) if data.get("model_env") else None,
        api_key_env=tuple(str(item) for item in api_key_env),
        temperature=float(data.get("temperature", 0.2)),
        max_tokens=int(data["max_tokens"]) if data.get("max_tokens") else None,
    )
