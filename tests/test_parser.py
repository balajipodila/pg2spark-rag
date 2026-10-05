"""Tests for PostgreSQL parsing and feature extraction."""

from src.pg2spark.parser import ParsedQuery, parse_postgres_sql


def test_parse_extracts_query_features() -> None:
    query = """
    WITH recent AS (
        SELECT user_id, created_at::date AS event_day,
               row_number() OVER (PARTITION BY user_id ORDER BY created_at) AS n
        FROM events
    )
    SELECT payload ->> 'name', payload #>> '{profile,city}',
           date_trunc('day', created_at)
    FROM recent
    """

    result = parse_postgres_sql(query)

    assert isinstance(result, ParsedQuery)
    assert result.parsed
    assert result.cte_count == 1
    assert set(result.functions) == {"ROW_NUMBER", "DATE_TRUNC"}
    assert result.window_functions == ["ROW_NUMBER"]
    assert result.casts == ["DATE"]
    assert result.json_operators == ["->>", "#>>"]


def test_parse_counts_nested_ctes_and_distinct_windows() -> None:
    result = parse_postgres_sql(
        "WITH a AS (SELECT 1), b AS (SELECT 2) "
        "SELECT lag(value) OVER (ORDER BY value) FROM a"
    )

    assert result.cte_count == 2
    assert result.window_functions == ["LAG"]


def test_invalid_sql_returns_parse_error_without_raising() -> None:
    result = parse_postgres_sql("SELECT FROM")

    assert not result.parsed
    assert result.parse_error
    assert result.functions == []
    assert result.cte_count == 0
