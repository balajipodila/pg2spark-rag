"""Deterministic PostgreSQL-to-Spark SQL transpilation."""

from __future__ import annotations

from typing import Optional

import sqlglot
from pydantic import BaseModel, ConfigDict
from sqlglot.errors import SqlglotError


class TranspileResult(BaseModel):
    """Result of attempting a deterministic SQLGlot transpilation."""

    model_config = ConfigDict(frozen=True)

    postgres_sql: str
    draft_sql: Optional[str] = None
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        """Whether transpilation produced Spark SQL."""
        return self.error is None and self.draft_sql is not None


def transpile_postgres_to_spark(sql: str) -> TranspileResult:
    """Transpile PostgreSQL SQL to Spark SQL without invoking an LLM."""
    try:
        statements = sqlglot.transpile(sql, read="postgres", write="spark")
    except SqlglotError as error:
        return TranspileResult(postgres_sql=sql, error=str(error))

    return TranspileResult(
        postgres_sql=sql,
        draft_sql=";\n".join(statements),
    )
