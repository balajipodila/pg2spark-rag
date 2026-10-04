# Role
You are a senior Python engineer and data engineer. You are helping me build "pg2spark-rag": a hybrid RAG application that translates PostgreSQL queries into valid, executable Spark SQL. Work in small verified milestones. Never skip ahead.

# Goal
Input: a PostgreSQL query (plus optional table schema DDL).
Output: Spark SQL that parses and passes Spark's analyzer, with a short list of conversions applied.

# Scope (v1)
IN: SELECT queries, CTEs, joins, subqueries, window functions, aggregations, date/time, string, array and JSON/JSONB functions, type casts.
OUT (v2, do not implement now): PL/pgSQL procedures, loops, triggers, DDL migrations.
If a query is out of scope, return a clear "unsupported" message, never a guess.

# Architecture (hybrid pipeline)
1. Parse: sqlglot parse with read="postgres". Extract features (functions used, types, CTEs, window usage).
2. Deterministic pass: sqlglot.transpile(read="postgres", write="spark"). Record the draft.
3. Check draft: validate with PySpark. If it passes, return it directly (source="sqlglot"), no LLM call.
4. RAG pass (only if step 3 fails or sqlglot raises): build a retrieval query from the unsupported functions/constructs, fetch top-k rules from the vector store, call the LLM with: original query, schema, sqlglot draft, retrieved rules.
5. Validate + self-correct: run the LLM output through the validator. On error, send the error message back to the LLM and retry, max 3 attempts.
6. Return: final SQL, source (sqlglot | rag), attempts, list of conversions, validation status.

# Tech stack
- Python 3.10+, sqlglot, pyspark (needs Java 17), qdrant-client in local embedded mode (path="./qdrant_data", no server), pydantic, fastapi, streamlit, pytest, python-dotenv.
- Embeddings: local model via fastembed or sentence-transformers (BAAI/bge-small-en-v1.5) so the project runs without an embeddings API key.
- LLM: provider-agnostic wrapper in src/llm.py. Model name and API key come from env vars (LLM_PROVIDER, LLM_MODEL, API key). Never hardcode model names.

# Project structure
pg2spark-rag/
├── data/
│   ├── mappings/pg_to_spark_mappings.json
│   └── eval/eval_set.jsonl            # {id, postgres, schema, expected_spark, tags}
├── src/pg2spark/
│   ├── config.py        # env loading, settings
│   ├── parser.py        # sqlglot parsing + feature extraction
│   ├── transpiler.py    # deterministic sqlglot pass
│   ├── ingestion.py     # load mappings, embed, upsert to Qdrant
│   ├── retriever.py     # query Qdrant
│   ├── llm.py           # provider-agnostic LLM client
│   ├── prompts.py       # prompt templates
│   ├── validator.py     # PySpark validation
│   ├── pipeline.py      # orchestrates the full flow
│   ├── models.py        # pydantic request/response models
│   └── api.py           # FastAPI
├── app.py               # Streamlit UI
├── scripts/run_eval.py  # baseline vs RAG evaluation report
├── tests/
├── requirements.txt
├── .env.example
└── README.md

# Mapping JSON schema (each entry)
{ "id", "category", "postgres_pattern", "spark_equivalent", "example_pg", "example_spark", "notes" }
One entry per chunk. Do not chunk by paragraphs. Be accurate:
- SERIAL has no direct Spark equivalent. Use Delta "GENERATED ALWAYS AS IDENTITY" or document it as a caveat. Do NOT map it to monotonically_increasing_id().
- Only include mappings you are confident exist in Spark SQL. Mark uncertain ones with "verify": true.

# Validator requirements
- Create a local SparkSession (master local[1], small shuffle partitions).
- From the provided schema DDL, create empty temp views/tables (map Postgres types to Spark types) so that queries referencing tables do not fail with "table not found".
- Use spark.sql(query) and force analysis. Distinguish syntax/analysis errors from environment errors.
- Reuse one SparkSession across calls.

# Evaluation
- scripts/run_eval.py runs every item in eval_set.jsonl in two modes: (a) sqlglot only, (b) full pipeline.
- Metrics: validity rate (passes Spark analyzer), exact/normalized match vs expected_spark, average attempts, per-tag breakdown.
- Output a markdown report to reports/eval_report.md.

# Engineering rules
- PEP 8, full type hints, docstrings, small functions.
- Handle missing env vars with clear error messages.
- No placeholders, no TODO stubs, no truncated code. Every file must run.
- Log with the logging module, not print.
- Do not invent Spark functions. If unsure, say so and add a "verify" flag.
- Write pytest tests for every module as you build it.

# Milestones (do ONE at a time, then stop and wait for my approval)
M1: Project scaffold, requirements.txt, .env.example, config.py, README skeleton.
M2: parser.py + transpiler.py + 30 starter eval queries + tests. Report how many pass with sqlglot alone.
M3: validator.py with schema-to-temp-view creation + tests.
M4: Mapping JSON (start with 40 entries) + ingestion.py + retriever.py + tests.
M5: llm.py + prompts.py + pipeline.py with the retry loop + tests.
M6: scripts/run_eval.py and the baseline vs RAG report.
M7: FastAPI api.py + Streamlit app.py (side-by-side diff, show source, attempts, conversions).
M8: Dockerfile, README with architecture diagram and eval results, deployment notes.

# After each milestone
Tell me: files created, how to run the tests, what to verify manually, and what the next milestone needs. Then stop.

Start with M1 only.