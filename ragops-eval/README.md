# ragops-eval

Retrieval quality evaluation microservice for [`search-service`](../Flagship/graph-rag-finance-assistant/search-service). Sends queries to the search-service, collects retrieved contexts and answers, and scores them using [RAGAS](https://docs.ragas.io) metrics. Results are optionally logged to MLflow.

---

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENAI_API_KEY
python main.py         # starts on port 8010
```

> `OPENAI_API_KEY` must be a real OpenAI key — RAGAS calls the OpenAI API directly for metric computation, not through the local gateway.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/eval/run` | Batch eval: list of queries → RAGAS scores + per-query breakdown |
| `POST` | `/eval/single` | Single query eval (MLflow logging skipped) |
| `GET` | `/health` | Service status + search-service reachability |

---

## Eval Modes

Set `mode` in the request body:

| Mode | Metrics | Ground truth required |
|------|---------|----------------------|
| `reference_free` (default) | `faithfulness`, `answer_relevancy` | No |
| `with_reference` | + `context_precision`, `context_recall` | Yes — `ground_truth` per query |

---

## Usage

**Batch run (reference-free):**
```json
POST /eval/run
{
  "queries": [
    { "question": "What was Apple's revenue in FY2023?" },
    { "question": "What are Microsoft's key risk factors?" }
  ],
  "mode": "reference_free",
  "log_to_mlflow": true,
  "run_name": "baseline-run-1"
}
```

**With reference answers:**
```json
POST /eval/run
{
  "queries": [
    {
      "question": "What was Apple's revenue in FY2023?",
      "ground_truth": "Apple's total net sales were $383.3 billion in fiscal year 2023."
    }
  ],
  "mode": "with_reference",
  "log_to_mlflow": true
}
```

**Single query (quick test):**
```json
POST /eval/single
{
  "question": "What is Tesla's gross margin trend?",
  "mode": "reference_free"
}
```

**Response shape:**
```json
{
  "run_id": "...",
  "mlflow_run_id": "...",
  "aggregate_scores": {
    "faithfulness": 0.87,
    "answer_relevancy": 0.91
  },
  "results": [
    {
      "question": "...",
      "answer": "...",
      "contexts": ["..."],
      "service_quality_score": 0.85,
      "ragas_scores": { "faithfulness": 0.87, "answer_relevancy": 0.91 }
    }
  ],
  "total_queries": 2,
  "failed_queries": 0
}
```

---

## Sample Dataset

`datasets/sample_queries.json` contains five financial queries for quick smoke-testing. Pass them via `/eval/run` or extend with `ground_truth` values to enable `with_reference` mode.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCH_SERVICE_URL` | `http://localhost:8003` | Target search-service base URL |
| `SEARCH_SERVICE_TIMEOUT` | `30` | Per-request timeout in seconds |
| `EVAL_SERVICE_PORT` | `8010` | Port this service listens on |
| `OPENAI_API_KEY` | — | Required for RAGAS metric computation |
| `OPENAI_LLM_MODEL` | `gpt-4o-mini` | LLM used by RAGAS |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server URL |
| `MLFLOW_EXPERIMENT_NAME` | `ragops-retrieval-eval` | MLflow experiment name |
