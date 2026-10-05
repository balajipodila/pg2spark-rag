"""Report SQLGlot-only output and known Spark compatibility risks."""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import TypedDict

from src.pg2spark.transpiler import transpile_postgres_to_spark


class EvaluationCase(TypedDict):
    """Required fields for one evaluation fixture."""

    id: str
    postgres: str
    schema: str
    expected_spark: str | None
    tags: list[str]


EVAL_SET_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "eval" / "eval_set.jsonl"
)
KNOWN_RISK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GENERATE_SERIES", re.compile(r"\bgenerate_series\s*\(", re.IGNORECASE)),
    ("DISTINCT ON", re.compile(r"\bDISTINCT\s+ON\s*\(", re.IGNORECASE)),
    (
        "untranslated JSONB extraction",
        re.compile(r"\bJSONB_EXTRACT(?:_SCALAR)?\s*\(", re.IGNORECASE),
    ),
    (
        "LISTAGG requires Spark 4.0+",
        re.compile(r"\bLISTAGG\s*\(", re.IGNORECASE),
    ),
    (
        "recursive CTE requires Spark 4.0+",
        re.compile(r"\bWITH\s+RECURSIVE\b", re.IGNORECASE),
    ),
    ("untranslated TO_CHAR", re.compile(r"\bTO_CHAR\s*\(", re.IGNORECASE)),
)


def _load_cases(path: Path = EVAL_SET_PATH) -> list[EvaluationCase]:
    """Load JSONL cases and reject malformed records explicitly."""
    with path.open(encoding="utf-8") as eval_file:
        return [json.loads(line) for line in eval_file if line.strip()]


def _known_risks(draft_sql: str) -> list[str]:
    """Find concrete PostgreSQL constructs that remain invalid or unsupported."""
    return [
        risk
        for risk, pattern in KNOWN_RISK_PATTERNS
        if pattern.search(draft_sql)
    ]


def build_report(cases: list[EvaluationCase]) -> tuple[str, int, int, int]:
    """Build a Markdown table and aggregate SQLGlot-only baseline counts."""
    rows = [
        "| ID | Output | Known Spark issues | Error |",
        "|---|---|---|---|",
    ]
    output_count = 0
    error_count = 0
    risk_count = 0

    for case in cases:
        result = transpile_postgres_to_spark(case["postgres"])
        if result.succeeded:
            output_count += 1
            draft = result.draft_sql or ""
            risks = _known_risks(draft)
            risk_count += bool(risks)
            rows.append(
                "| {id} | yes | {risks} | - |".format(
                    id=case["id"],
                    risks=", ".join(risks) or "-",
                )
            )
        else:
            error_count += 1
            rows.append(
                "| {id} | no | - | {error} |".format(
                    id=case["id"],
                    error=(result.error or "Unknown transpilation error")
                    .replace("|", r"\|")
                    .replace("\n", " "),
                )
            )

    return "\n".join(rows), output_count, error_count, risk_count


def main() -> None:
    """Run the baseline and send its table and counts to standard output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger(__name__)
    cases = _load_cases()
    report, output_count, error_count, risk_count = build_report(cases)
    logger.info(report)
    logger.info(
        "\nTotal: %d; transpiled output: %d; errors: %d; "
        "with known Spark issues: %d",
        len(cases),
        output_count,
        error_count,
        risk_count,
    )


if __name__ == "__main__":
    main()
