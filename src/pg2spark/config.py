"""Environment and application configuration for pg2spark-rag."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    """Project settings loaded from environment variables."""

    project_root: Path = PROJECT_ROOT
    qdrant_path: Path = PROJECT_ROOT / "qdrant_data"
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from the current environment."""
        return cls(
            project_root=PROJECT_ROOT,
            qdrant_path=Path(os.getenv("QDRANT_PATH", str(PROJECT_ROOT / "qdrant_data"))),
            llm_provider=os.getenv("LLM_PROVIDER"),
            llm_model=os.getenv("LLM_MODEL"),
            llm_api_key=os.getenv("LLM_API_KEY"),
        )

    def require_llm_settings(self) -> None:
        """Validate environment variables needed by the LLM integration."""
        missing = [
            name
            for name, value in {
                "LLM_PROVIDER": self.llm_provider,
                "LLM_MODEL": self.llm_model,
                "LLM_API_KEY": self.llm_api_key,
            }.items()
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(
                "Missing required LLM environment variable(s): "
                f"{joined}. Populate them in .env or the process environment."
            )


def get_settings() -> Settings:
    """Return a settings object from the environment."""
    return Settings.from_env()


settings = get_settings()
