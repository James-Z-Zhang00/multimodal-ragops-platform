from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class EvalMode(str, Enum):
    # faithfulness + answer_relevancy — no ground truth required
    reference_free = "reference_free"
    # + context_precision + context_recall — ground_truth required per query
    with_reference = "with_reference"


class QueryItem(BaseModel):
    question: str
    ground_truth: Optional[str] = None


class EvalRequest(BaseModel):
    queries: List[QueryItem]
    session_id: str = "eval-session"
    mode: EvalMode = EvalMode.reference_free
    log_to_mlflow: bool = True
    run_name: Optional[str] = None


class SingleEvalRequest(BaseModel):
    question: str
    ground_truth: Optional[str] = None
    session_id: str = "eval-single"
    mode: EvalMode = EvalMode.reference_free


class MetricScores(BaseModel):
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None


class QueryResult(BaseModel):
    question: str
    answer: str
    contexts: List[str]
    citations: Optional[List[str]] = None
    service_quality_score: Optional[float] = None
    ragas_scores: MetricScores


class EvalResponse(BaseModel):
    run_id: str
    mlflow_run_id: Optional[str] = None
    aggregate_scores: MetricScores
    results: List[QueryResult]
    total_queries: int
    failed_queries: int
