"""Type definitions for SQL Agent pipeline input/output structures."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any

from sqlglot import parse_one, exp
from sqlglot.errors import ParseError

@dataclass
class PipelineInput:
    """Input to the AnalyticsPipeline.run() method."""

    question: str
    request_id: str | None = None


@dataclass
class SQLGenerationOutput:
    """Output from the SQL generation stage.

    For complex solutions with multiple LLM calls (chain-of-thought, planning,
    query refinement), populate intermediate_outputs with per-call details.
    llm_stats aggregates all calls for efficient evaluation.
    """

    sql: str | None
    timing_ms: float
    llm_stats: dict[
        str, Any
    ]  # Aggregated: {llm_calls, prompt_tokens, completion_tokens, total_tokens, model}
    intermediate_outputs: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@dataclass
class SQLValidationOutput:
    """Output from the SQL validation stage."""

    is_valid: bool
    validated_sql: str | None
    error: str | None = None
    timing_ms: float = 0.0


@dataclass
class SQLExecutionOutput:
    """Output from the SQL execution stage."""

    rows: list[dict[str, Any]]
    row_count: int
    timing_ms: float
    error: str | None = None


@dataclass
class AnswerGenerationOutput:
    """Output from the answer generation stage.

    For complex solutions with multiple LLM calls (summarization, verification),
    populate intermediate_outputs with per-call details.
    llm_stats aggregates all calls for efficient evaluation.
    """

    answer: str
    timing_ms: float
    llm_stats: dict[
        str, Any
    ]  # Aggregated: {llm_calls, prompt_tokens, completion_tokens, total_tokens, model}
    intermediate_outputs: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@dataclass
class PipelineOutput:
    """Complete output from AnalyticsPipeline.run()."""

    # Status
    status: str  # "success" | "unanswerable" | "invalid_sql" | "error"
    question: str
    request_id: str | None

    # Stage outputs (for evaluation)
    sql_generation: SQLGenerationOutput
    sql_validation: SQLValidationOutput
    sql_execution: SQLExecutionOutput
    answer_generation: AnswerGenerationOutput

    # Convenience fields
    sql: str | None = None
    rows: list[dict[str, Any]] = field(default_factory=list)
    answer: str = ""

    # Aggregates
    timings: dict[str, float] = field(default_factory=dict)
    total_llm_stats: dict[str, Any] = field(default_factory=dict)

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
            return fail("Only SELECT statements are allowed")

        # 2) Reject dangerous statement types anywhere
        for node_type in cls.DISALLOWED_NODES:
            if next(ast.find_all(node_type), None) is not None:
                return fail(f"Disallowed SQL operation: {node_type.__name__}")

        # 3) No JOINs for single-table use case
        if next(ast.find_all(exp.Join), None) is not None:
            return fail("JOIN is not allowed")

        # 4) No subqueries for v1 validator
        if next(ast.find_all(exp.Subquery), None) is not None:
            return fail("Subqueries are not allowed")

        # 5) Validate tables
        tables = list(ast.find_all(exp.Table))
        if not tables:
            return fail("Query must reference a table")

        for table in tables:
            table_name = table.name
            if table_name != cls.ALLOWED_TABLE:
                return fail(f"Disallowed table: {table_name}")

        # 6) Validate columns
        for column in ast.find_all(exp.Column):
            column_name = column.name
            if column_name not in cls.ALLOWED_COLUMNS:
                return fail(f"Disallowed or unknown column: {column_name}")

        # 7) Validate functions
        for func in ast.find_all(exp.Func):
            func_name = func.sql_name()
            if not func_name:
                func_name = func.__class__.__name__
            func_name = func_name.upper()

            if func_name not in cls.ALLOWED_FUNCTIONS:
                return fail(f"Disallowed function: {func_name}")

        # 8) Optional: disallow SELECT *
        # comment this out if you want to allow it
        for _ in ast.find_all(exp.Star):
            return fail("SELECT * is not allowed")

        # 9) Normalize SQL back to SQLite dialect
        validated_sql = ast.sql(dialect="sqlite")

        return SQLValidationOutput(
            is_valid=True,
            validated_sql=validated_sql,
            error=None,
            timing_ms=(time.perf_counter() - start) * 1000,
        )
