from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from loguru import logger

from sqlglot import parse_one, exp
from sqlglot.errors import ParseError

from src.llm_client import OpenRouterLLMClient, build_default_llm_client
from src.types import (
    PipelineOutput,
    SQLExecutionOutput,
    SQLValidationOutput,
)


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "data" / "gaming_mental_health.sqlite"


class SQLValidationError(Exception):
    pass


class SQLValidator:
    ALLOWED_TABLE = "gaming_mental_health"

    ALLOWED_COLUMNS = {
        "age",
        "gender",
        "income",
        "daily_gaming_hours",
        "weekly_sessions",
        "years_gaming",
        "sleep_hours",
        "caffeine_intake",
        "exercise_hours",
        "stress_level",
        "anxiety_score",
        "depression_score",
        "social_interaction_score",
        "relationship_satisfaction",
        "academic_performance",
        "work_productivity",
        "addiction_level",
        "multiplayer_ratio",
        "toxic_exposure",
        "violent_games_ratio",
        "mobile_gaming_ratio",
        "night_gaming_ratio",
        "weekend_gaming_hours",
        "friends_gaming_count",
        "online_friends",
        "streaming_hours",
        "esports_interest",
        "headset_usage",
        "microtransactions_spending",
        "parental_supervision",
        "loneliness_score",
        "aggression_score",
        "happiness_score",
        "bmi",
        "screen_time_total",
        "eye_strain_score",
        "back_pain_score",
        "competitive_rank",
        "internet_quality",
    }

    ALLOWED_FUNCTIONS = {
        "COUNT",
        "AVG",
        "MIN",
        "MAX",
        "SUM",
        "LOWER",
        "UPPER",
        "ROUND",
    }

    DISALLOWED_NODES = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.Create,
        exp.TruncateTable,
        exp.Merge,
    )
    @classmethod
    def validate(cls, sql: str | None) -> SQLValidationOutput:
        start = time.perf_counter()

        def fail(message: str) -> SQLValidationOutput:
            return SQLValidationOutput(
                is_valid=False,
                validated_sql=None,
                error=message,
                timing_ms=(time.perf_counter() - start) * 1000,
            )

        # TODO: Implement SQL validation logic
        # Consider what validation is needed for this use case
        # Check if the sql query is valid and check
        if sql is None or not sql.strip():
            return fail("No SQL provided")

        sql = sql.strip()

        # Optional hard precheck: only one statement
        if ";" in sql.rstrip(";"):
            return fail("Multiple SQL statements are not allowed")

        try:
            ast = parse_one(sql, read="sqlite")
        except ParseError as e:
            return fail(f"SQL parse error: {e}")
        except Exception as e:
            return fail(f"SQL validation failed during parsing: {e}")

        # 1) Only SELECT queries allowed
        if not isinstance(ast, exp.Select):
            logger.info(f"SQL validation failed: Only SELECT statements are allowed. Received: {sql}")
            return fail("Only SELECT statements are allowed")

        # 2) Reject dangerous statement types anywhere
        for node_type in cls.DISALLOWED_NODES:
            if next(ast.find_all(node_type), None) is not None:
                logger.info(f"SQL validation failed: Disallowed SQL operation: {node_type.__name__}")
                return fail(f"Disallowed SQL operation: {node_type.__name__}")

        # 3) No JOINs for single-table use case
        if next(ast.find_all(exp.Join), None) is not None:
            logger.info("SQL validation failed: JOIN is not allowed")
            return fail("JOIN is not allowed")

        # 4) No subqueries for v1 validator
        if next(ast.find_all(exp.Subquery), None) is not None:
            logger.info("SQL validation failed: Subqueries are not allowed")
            return fail("Subqueries are not allowed")

        # 5) Validate tables
        tables = list(ast.find_all(exp.Table))
        if not tables:
            logger.info("SQL validation failed: Query must reference a table")
            return fail("Query must reference a table")

        for table in tables:
            table_name = table.name
            if table_name != cls.ALLOWED_TABLE:
                logger.info(f"SQL validation failed: Disallowed table: {table_name}")
                return fail(f"Disallowed table: {table_name}")

        # 6a) Collect alias names defined via AS (column and table aliases)
        defined_aliases: set[str] = set()
        for alias in ast.find_all(exp.Alias):
            alias_name = alias.alias
            if alias_name:
                defined_aliases.add(alias_name)
        for table in tables:
            if table.alias:
                defined_aliases.add(table.alias)

        # 6b) Validate columns (allow references to aliases defined in this query)
        for column in ast.find_all(exp.Column):
            column_name = column.name

            # Reference to an alias defined in SELECT (e.g. ORDER BY avg_anxiety)
            if column_name in defined_aliases:
                continue

            # Qualified reference like t.age where t is a table alias
            table_ref = column.table
            if table_ref and table_ref in defined_aliases and column_name in cls.ALLOWED_COLUMNS:
                continue

            if column_name not in cls.ALLOWED_COLUMNS:
                logger.info(f"SQL validation failed: Disallowed or unknown column: {column_name}")
                return fail(f"Disallowed or unknown column: {column_name}")

        # 7) Validate functions
        for func in ast.find_all(exp.Func):
            func_name = func.sql_name()
            if not func_name:
                func_name = func.__class__.__name__
            func_name = func_name.upper()

            if func_name not in cls.ALLOWED_FUNCTIONS:
                logger.info(f"SQL validation failed: Disallowed function: {func_name}")
                return fail(f"Disallowed function: {func_name}")

        # 8) Optional: disallow SELECT *
        # comment this out if you want to allow it
        # for _ in ast.find_all(exp.Star):
        #     return fail("SELECT * is not allowed")

        # 9) Normalize SQL back to SQLite dialect
        validated_sql = ast.sql(dialect="sqlite")

        return SQLValidationOutput(
            is_valid=True,
            validated_sql=validated_sql,
            error=None,
            timing_ms=(time.perf_counter() - start) * 1000,
        )


class SQLiteExecutor:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)

    def run(self, sql: str | None) -> SQLExecutionOutput:
        start = time.perf_counter()
        error = None
        rows = []
        row_count = 0

        if sql is None:
            return SQLExecutionOutput(
                rows=[],
                row_count=0,
                timing_ms=(time.perf_counter() - start) * 1000,
                error=None,
            )

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql)
                rows = [dict(r) for r in cur.fetchmany(100)]
                row_count = len(rows)
        except Exception as exc:
            error = str(exc)
            rows = []
            row_count = 0

        return SQLExecutionOutput(
            rows=rows,
            row_count=row_count,
            timing_ms=(time.perf_counter() - start) * 1000,
            error=error,
        )


class AnalyticsPipeline:
    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB_PATH,
        llm_client: OpenRouterLLMClient | None = None,
        session_manager = dict | None,
        benchmark: bool = False,
    ) -> None:
        self.db_path = Path(db_path)
        self.llm = llm_client or build_default_llm_client()
        self.executor = SQLiteExecutor(self.db_path)
        self.session_manager = session_manager or {
            "AIresponse": [],
            "Humanquestion": [],
        }
        self.benchmark = benchmark

    def run(self, question: str, request_id: str | None = None) -> PipelineOutput:
        start = time.perf_counter()

        # Build context to do a pre hit to the LLM
        context = self.llm.build_context(question, self.session_manager)

        # Stage 1: SQL Generation
        sql_gen_output = self.llm.generate_sql(question, context)
        sql = sql_gen_output.sql

        # Stage 2: SQL Validation
        validation_output = SQLValidator.validate(sql)
        if not validation_output.is_valid:
            sql = None

        # Stage 3: SQL Execution
        execution_output = self.executor.run(sql)
        rows = execution_output.rows

        # Stage 4: Answer Generation
        answer_output = self.llm.generate_answer(question, sql, rows, self.session_manager)
        if not self.benchmark:
            self.session_manager["AIresponse"].append(answer_output.answer)
            self.session_manager["Humanquestion"].append(f"Query: {question}\nSQL: {sql}\nRows: {rows}")


        # Determine status
        status = "success"
        if sql_gen_output.sql is None and sql_gen_output.error:
            status = "unanswerable"
        elif not validation_output.is_valid:
            status = "invalid_sql"
        elif execution_output.error:
            status = "error"
        elif sql is None:
            status = "unanswerable"

        # Build timings aggregate
        timings = {
            "sql_generation_ms": sql_gen_output.timing_ms,
            "sql_validation_ms": validation_output.timing_ms,
            "sql_execution_ms": execution_output.timing_ms,
            "answer_generation_ms": answer_output.timing_ms,
            "total_ms": (time.perf_counter() - start) * 1000,
        }

        # Build total LLM stats
        total_llm_stats = {
            "llm_calls": sql_gen_output.llm_stats.get("llm_calls", 0)
            + answer_output.llm_stats.get("llm_calls", 0),
            "prompt_tokens": sql_gen_output.llm_stats.get("prompt_tokens", 0)
            + answer_output.llm_stats.get("prompt_tokens", 0),
            "completion_tokens": sql_gen_output.llm_stats.get("completion_tokens", 0)
            + answer_output.llm_stats.get("completion_tokens", 0),
            "total_tokens": sql_gen_output.llm_stats.get("total_tokens", 0)
            + answer_output.llm_stats.get("total_tokens", 0),
            "model": sql_gen_output.llm_stats.get("model", "unknown"),
        }

        return PipelineOutput(
            status=status,
            question=question,
            request_id=request_id,
            sql_generation=sql_gen_output,
            sql_validation=validation_output,
            sql_execution=execution_output,
            answer_generation=answer_output,
            sql=sql,
            rows=rows,
            answer=answer_output.answer,
            timings=timings,
            total_llm_stats=total_llm_stats,
        )
