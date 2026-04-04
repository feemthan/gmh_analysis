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
        return SQLValidationOutput(
            is_valid=True,
            validated_sql=sql,
            error=None,
            timing_ms=(time.perf_counter() - start) * 1000,
        )
