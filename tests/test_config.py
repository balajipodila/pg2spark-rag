"""Tests for project configuration and environment handling."""

import pytest

from src.pg2spark.config import Settings


def test_settings_reads_values_from_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_API_KEY", "secret-key")
    monkeypatch.setenv("QDRANT_PATH", "./custom_qdrant")

    settings = Settings.from_env()

    assert settings.llm_provider == "openai"
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.llm_api_key == "secret-key"
    assert str(settings.qdrant_path).endswith("custom_qdrant")


def test_require_llm_settings_raises_when_missing(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    settings = Settings.from_env()

    with pytest.raises(RuntimeError, match="Missing required LLM environment variable"):
        settings.require_llm_settings()
