import asyncio
import pandas as pd
from models import EvalMode, MetricScores
from config.settings import settings

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextPrecisionWithReference, LLMContextRecall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper


def _llm() -> LangchainLLMWrapper:
    return LangchainLLMWrapper(ChatOpenAI(
        model=settings.OPENAI_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    ))


def _embeddings() -> LangchainEmbeddingsWrapper:
    return LangchainEmbeddingsWrapper(OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    ))


def _pick(df: pd.DataFrame, *candidates: str) -> float | None:
    for col in candidates:
        if col in df.columns:
            return float(df[col].mean())
    return None


def compute_ragas_metrics(
    samples: list[dict],
    mode: EvalMode,
) -> tuple[MetricScores, list[MetricScores]]:
    llm = _llm()
    emb = _embeddings()

    ragas_samples = [
        SingleTurnSample(
            user_input=s["question"],
            response=s["answer"],
            retrieved_contexts=s["contexts"] if s["contexts"] else [""],
            reference=s.get("ground_truth") or "",
        )
        for s in samples
    ]

    if mode == EvalMode.reference_free:
        metrics = [Faithfulness(llm=llm), ResponseRelevancy(llm=llm, embeddings=emb)]
    else:
        metrics = [
            Faithfulness(llm=llm),
            ResponseRelevancy(llm=llm, embeddings=emb),
            LLMContextPrecisionWithReference(llm=llm),
            LLMContextRecall(llm=llm),
        ]

    result = evaluate(dataset=EvaluationDataset(samples=ragas_samples), metrics=metrics)
    df = result.to_pandas()

    aggregate = MetricScores(
        faithfulness=_pick(df, "faithfulness"),
        answer_relevancy=_pick(df, "answer_relevancy", "response_relevancy"),
        context_precision=_pick(df, "context_precision", "llm_context_precision_with_reference"),
        context_recall=_pick(df, "context_recall", "llm_context_recall"),
    )

    def _row_scores(row: pd.Series) -> MetricScores:
        def get(col: str, *alts: str) -> float | None:
            for c in (col, *alts):
                if c in row and pd.notna(row[c]):
                    return float(row[c])
            return None

        return MetricScores(
            faithfulness=get("faithfulness"),
            answer_relevancy=get("answer_relevancy", "response_relevancy"),
            context_precision=get("context_precision", "llm_context_precision_with_reference"),
            context_recall=get("context_recall", "llm_context_recall"),
        )

    per_sample = [_row_scores(row) for _, row in df.iterrows()]
    return aggregate, per_sample


async def compute_ragas_metrics_async(
    samples: list[dict],
    mode: EvalMode,
) -> tuple[MetricScores, list[MetricScores]]:
    return await asyncio.to_thread(compute_ragas_metrics, samples, mode)
