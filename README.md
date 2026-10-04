# pg2spark-rag

A hybrid RAG application that converts PostgreSQL SQL into valid Spark SQL and validates the output with PySpark.

## Overview

This project follows a two-pass translation flow:

1. Parse PostgreSQL SQL with sqlglot and capture the query features.
2. Attempt a deterministic translation to Spark SQL.
3. If the draft fails, retrieve mapping rules and call an LLM to produce a corrected Spark query.
4. Re-run validation in PySpark and return the final SQL plus conversion notes.

## Project structure

- `src/pg2spark/config.py` loads environment variables and project settings.
- `src/pg2spark/` contains parsing, translation, validation, retrieval, and orchestration modules.
- `data/` stores mapping rules and evaluation fixtures.
- `tests/` contains pytest coverage for each module as it is added.

## Environment setup

1. Create a virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in the required values.

## Local validation

Run the test suite from the project root:

```bash
pytest
```

## Milestones

- M1: project scaffold, requirements, environment template, config loader, README skeleton
- M2: parser and transpiler improvements with starter eval queries
- M3: Spark validator using temp views and schema DDL
- M4: mapping ingestion and retrieval
- M5: LLM integration and retry loop
- M6: evaluation runner and reporting
- M7: FastAPI + Streamlit UI
- M8: Docker packaging and deployment guidance
