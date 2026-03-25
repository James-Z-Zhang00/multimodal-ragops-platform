# multimodal-ragops-platform

A vendor-neutral RAGOps platform for evaluating, fine-tuning, and optimizing AI models across multiple providers and input modalities. Designed as a systematic engineering platform — not a one-off script — where model selection, prompt variants, and retrieval configurations are treated as measurable, versioned experiment variables.

> **Status:** Active development

---

## Overview

Most RAG systems are built once and never systematically improved. This platform provides the tooling to benchmark, tune, and optimize every layer of a RAG pipeline — from the model tier selected for each task, to the chunking strategy, to the fine-tuning technique applied.

Built as a companion to [graph-rag-finance-assistant](../graph-rag-finance-assistant) — extending its financial document intelligence with systematic evaluation, multi-provider model routing, and multimodal input support.

---

## Key Capabilities

### Model-Agnostic Evaluation & Adaptive Routing
- Benchmarks AI models across 4 provider tiers: OpenAI, Anthropic, Google, and open-source (Ollama)
- A/B tests model configurations, prompt variants (zero-shot, few-shot, chain-of-thought), and retrieval parameters
- Adaptive cost-aware routing dispatches each task to the highest-ROI model meeting the quality threshold
- Pluggable `ModelAdapter` interface — extensible to computer vision and recommendation models
- Experiment tracking via MLflow

### Fine-tuning: Multi-Technique & Multi-Provider
- **SFT** (Supervised Fine-Tuning) via OpenAI fine-tuning API and Google Vertex AI
- **DPO** (Direct Preference Optimization) via QLoRA on Llama 3.2 3B using HuggingFace TRL
- All approaches evaluated against the same RAGAS benchmark for direct cross-technique comparison

### Multimodal Financial Document Understanding
- Two-model cascade for financial chart extraction from SEC filings:
  - Stage 1: GPT-4o-mini classifies image type (chart / table / diagram / logo)
  - Stage 2: DePlot for standard charts (free, local); GPT-4o Vision for complex types
  - Stage 3: XBRL cross-validation scores accuracy; triggers escalation if deviation exceeds 5%
- Automatic accuracy validation against XBRL-tagged numeric ground truth

### Multimodal Ingestion & Query Optimization
- Unified ingestion layer: text, voice (Whisper), tabular (.xlsx via text-to-SQL), PDF, visual charts
- LLM-reinforced query rewriting with token budget enforcement
- All modalities normalized into a structured query before dispatch to the routing framework

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Evaluation | RAGAS, MLflow |
| LLM Providers | OpenAI, Anthropic, Google Vertex AI, Ollama |
| Fine-tuning | OpenAI Fine-tuning API, Vertex AI, HuggingFace TRL (QLoRA/DPO) |
| Vision | DePlot, GPT-4o Vision, img2table |
| Audio | OpenAI Whisper |
| API Framework | FastAPI |
| Containerization | Docker, docker-compose |

---

## Architecture

```
Multimodal Input Layer
  (text / voice / .xlsx / PDF / visual charts)
          │
          ▼
  Query Normalization & Rewriting
          │
          ▼
  Model-Agnostic Routing Framework
  ┌───────────────────────────────┐
  │  Eval Framework (RAGAS)       │
  │  A/B Testing & MLflow         │
  │  Pluggable Model Adapters     │
  │  Cost-Quality Threshold       │
  └───────────────────────────────┘
          │
    ┌─────┴──────┐
    ▼            ▼
OpenAI      Anthropic    Google    Ollama
GPT-4o      Claude       Gemini    Llama/Mistral
```

---

## Project Structure

```
multimodal-ragops-platform/
├── eval-service/         # RAGAS evaluation + MLflow experiment tracking
├── routing-service/      # Model adapter layer + cost-aware dispatch
├── ingestion-service/    # Multimodal input normalization
├── vision-service/       # Chart extraction pipeline (DePlot + GPT-4o Vision)
├── finetune/             # Fine-tuning scripts (SFT + DPO)
├── docker-compose.yml
└── .env.example
```

---

## Related Projects

- **[graph-rag-finance-assistant](../graph-rag-finance-assistant)** — Production GraphRAG system for SEC financial filings; provides the RAG pipeline this platform evaluates and optimizes
- `agentic-research-pipeline` _(coming soon)_ — Multi-agent automation system with Kafka streaming and gRPC

---

## License

MIT
