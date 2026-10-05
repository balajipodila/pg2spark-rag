"""PostgreSQL SQL parsing and feature extraction."""

from __future__ import annotations

from typing import Optional

import sqlglot
from pydantic import BaseModel, ConfigDict
from sqlglot import exp
from sqlglot.errors import SqlglotError


class ParsedQuery(BaseModel):
    """PostgreSQL query and syntax features extracted from its AST."""

    model_config = ConfigDict(frozen=True)

    sql: str
    functions: list[str]
    cte_count: int
    window_functions: list[str]
    casts: list[str]
    json_operators: list[str]
    parse_error: Optional[str] = None

    @property
    def parsed(self) -> bool:
        """Whether sqlglot parsed the input successfully."""
        return self.parse_error is None


def _function_name(function: exp.Func) -> str:
    """Return a stable SQL name for a function expression."""
    if isinstance(function, exp.Anonymous):
        name = function.name
    else:
        name = function.sql_name()
        if type(function).__name__ == "TimestampTrunc":
            name = "DATE_TRUNC"
    return name.upper()


def _ordered_unique(values: list[str]) -> list[str]:
    """Remove duplicate feature names without changing traversal order."""
    return list(dict.fromkeys(values))


def _json_operator(expression: exp.Expression) -> Optional[str]:
    """Map sqlglot's PostgreSQL JSON extraction nodes to source operators."""
    node_name = type(expression).__name__
    operator_by_node = {
        "JSONExtract": "->",
        "JSONExtractScalar": "->>",
        "JSONBExtract": "#>",
        "JSONBExtractScalar": "#>>",
    }
    return operator_by_node.get(node_name)


def parse_postgres_sql(sql: str) -> ParsedQuery:
    """Parse PostgreSQL SQL and return extracted syntax features.

    Parse failures are represented on the result instead of being raised, so
    callers can report the error without losing the original input.
    """
    try:
        trees = sqlglot.parse(sql, read="postgres")
    except SqlglotError as error:
        return ParsedQuery(
            sql=sql,
            functions=[],
            cte_count=0,
            window_functions=[],
            casts=[],
            json_operators=[],
            parse_error=str(error),
        )

    expressions = [tree for tree in trees if tree is not None]
    functions: list[str] = []
    window_functions: list[str] = []
    casts: list[str] = []
    json_operators: list[str] = []
    cte_count = 0

    for tree in expressions:
        cte_count += sum(1 for _ in tree.find_all(exp.CTE))
        functions.extend(
            _function_name(node)
            for node in tree.find_all(exp.Func)
            if not isinstance(node, exp.Cast) and _json_operator(node) is None
        )
        for window in tree.find_all(exp.Window):
            if isinstance(window.this, exp.Func):
                window_functions.append(_function_name(window.this))
        casts.extend(
            node.args["to"].sql(dialect="postgres")
            for node in tree.find_all(exp.Cast)
            if node.args.get("to") is not None
        )
        json_operators.extend(
            operator
            for node in tree.walk()
            if (operator := _json_operator(node)) is not None
        )

    return ParsedQuery(
        sql=sql,
        functions=_ordered_unique(functions),
        cte_count=cte_count,
        window_functions=_ordered_unique(window_functions),
        casts=_ordered_unique(casts),
        json_operators=_ordered_unique(json_operators),
    )
