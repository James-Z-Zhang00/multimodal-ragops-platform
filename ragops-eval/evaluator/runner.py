import asyncio
import json
import logging
import uuid
from models import EvalMode, EvalRequest, EvalResponse, MetricScores, QueryItem, QueryResult, SingleEvalRequest
from evaluator.client import SearchServiceClient
from evaluator.metrics import compute_ragas_metrics_async
from config.settings import settings

logger = logging.getLogger(__name__)


async def run_evaluation(request: EvalRequest) -> EvalResponse:
    client = SearchServiceClient(
        base_url=settings.SEARCH_SERVICE_URL,
        timeout=settings.SEARCH_SERVICE_TIMEOUT,
    )

    raw_results: list[dict] = []
    failed = 0

    for item in request.queries:
        try:
            resp = await client.search(item.question, request.session_id)
            raw_results.append({
                "question": item.question,
                "answer": resp.get("answer", ""),
                "contexts": resp.get("contexts") or [],
                "ground_truth": item.ground_truth or "",
                "citations": resp.get("citations"),
                "service_quality_score": resp.get("quality_score"),
            })
        except Exception as e:
            failed += 1
            logger.warning("Query failed (%s): %s", item.question[:60], e)

    if not raw_results:
        raise RuntimeError("All queries to search-service failed — check SEARCH_SERVICE_URL and that the service is running.")

    aggregate, per_sample = await compute_ragas_metrics_async(raw_results, request.mode)

    mlflow_run_id: str | None = None
    if request.log_to_mlflow:
        try:
            mlflow_run_id = await asyncio.to_thread(_log_to_mlflow, aggregate, raw_results, request, failed)
        except Exception as e:
            logger.warning("MLflow logging skipped: %s", e)

    query_results = [
        QueryResult(
            question=r["question"],
            answer=r["answer"],
            contexts=r["contexts"],
            citations=r["citations"],
            service_quality_score=r["service_quality_score"],
            ragas_scores=per_sample[i],
        )
        for i, r in enumerate(raw_results)
    ]

    return EvalResponse(
        run_id=str(uuid.uuid4()),
        mlflow_run_id=mlflow_run_id,
        aggregate_scores=aggregate,
        results=query_results,
        total_queries=len(request.queries),
        failed_queries=failed,
    )


async def run_single(request: SingleEvalRequest) -> EvalResponse:
    return await run_evaluation(EvalRequest(
        queries=[QueryItem(question=request.question, ground_truth=request.ground_truth)],
        session_id=request.session_id,
        mode=request.mode,
        log_to_mlflow=False,
    ))


def _log_to_mlflow(
    aggregate: MetricScores,
    raw_results: list[dict],
    request: EvalRequest,
    failed: int,
) -> str:
    import mlflow

    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)

    run_name = request.run_name or f"eval-{len(raw_results)}-queries"

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params({
            "search_service_url": settings.SEARCH_SERVICE_URL,
            "eval_mode": request.mode.value,
            "total_queries": len(request.queries),
            "failed_queries": failed,
        })

        for metric, value in aggregate.model_dump(exclude_none=True).items():
            mlflow.log_metric(metric, value)

        mlflow.log_text(
            json.dumps(raw_results, indent=2, default=str),
            "raw_results.json",
        )

        return run.info.run_id
