"""Tests for deterministic PostgreSQL-to-Spark transpilation."""

from src.pg2spark.transpiler import TranspileResult, transpile_postgres_to_spark


def test_transpiles_postgres_cast_to_spark() -> None:
    result = transpile_postgres_to_spark("SELECT amount::numeric FROM payments")

    assert isinstance(result, TranspileResult)
    assert result.succeeded
    assert result.draft_sql == "SELECT CAST(amount AS DECIMAL) FROM payments"
    assert result.error is None


def test_transpiles_valid_select_without_llm() -> None:
    result = transpile_postgres_to_spark(
        "SELECT date_trunc('day', created_at) FROM events"
    )

    assert result.succeeded
    assert result.draft_sql == (
        "SELECT DATE_TRUNC('DAY', created_at) FROM events"
    )


def test_invalid_sql_returns_error_without_raising() -> None:
    result = transpile_postgres_to_spark("SELECT FROM")

    assert not result.succeeded
    assert result.draft_sql is None
    assert result.error
