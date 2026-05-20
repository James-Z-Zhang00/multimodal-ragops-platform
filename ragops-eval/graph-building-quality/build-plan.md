# graph-building-quality: Step 4 Extraction Benchmark

## Goal
Capture what goes **into** step 4 and what comes **out** of step 4, then compare them — either manually or with LLM-as-judge.

---

## Structure

```
graph-building-quality/
├── capture_input.py          ← extract chunks from a small SEC filing (step 3 output)
├── capture_output.py         ← query Neo4j for extracted entities + relationships (step 4 output)
├── compare.py                ← manual diff view OR LLM-as-judge scoring
├── fixtures/
│   └── sample.html           ← one small SEC filing to test with
├── requirements.txt
├── .env.example
└── results/                  ← captured inputs/outputs saved here as JSON
```

---

## File-by-File

### `capture_input.py`
Sends the sample SEC filing to the sec-parser service and saves the resulting chunks to `results/input_chunks.json`.

Each chunk in the output:
```json
{
  "chunk_id": 1,
  "text": "Apple Inc. reported total net sales of $391.0 billion...",
  "source_section": "Item 6",
  "token_count": 487
}
```

Run: `python capture_input.py`
Output: `results/input_chunks.json`

---

### `capture_output.py`
After a graph build has run, queries Neo4j to capture what was extracted for each chunk.

Each record in the output:
```json
{
  "chunk_id": 1,
  "chunk_text": "Apple Inc. reported...",
  "entities": [
    {"name": "Apple Inc.", "type": "Company", "description": "..."},
    {"name": "$391.0 billion", "type": "FinancialMetric", "description": "..."}
  ],
  "relationships": [
    {"source": "Apple Inc.", "type": "HAS_REVENUE", "target": "$391.0 billion", "description": "..."}
  ]
}
```

Run: `python capture_output.py`
Output: `results/output_entities.json`

---

### `compare.py`
Loads `input_chunks.json` and `output_entities.json` side by side.

Two modes (set via `--mode` flag):

**`--mode manual`** (default)
Prints each chunk + its extracted entities/relationships in a readable table. For small files — human reads and judges quality directly.

**`--mode judge`**
Sends each (chunk_text, extracted_entities, extracted_relationships) to the judge LLM and asks it to score:
- Completeness (0.0–1.0): important entities missed?
- Accuracy (0.0–1.0): types correctly classified?
- Relationship quality (0.0–1.0): relationships logically correct?

Prints per-chunk scores and overall averages. Saves full results to `results/comparison_TIMESTAMP.json`.

Run:
```bash
python compare.py --mode manual
python compare.py --mode judge
```

---

## Configuration

### `requirements.txt`
```
openai>=1.30.0
python-dotenv
requests
neo4j>=5.0.0
tabulate
```

### `.env.example`
```
# sec-parser endpoint (for capture_input.py)
SEC_PARSER_URL=http://localhost:8001

# Neo4j (for capture_output.py)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=

# Judge model (for compare.py --mode judge)
OPENAI_API_KEY=
JUDGE_MODEL=gpt-4o
```

---

## Workflow

```
1. python capture_input.py          → results/input_chunks.json
2. [run a graph build on the same file]
3. python capture_output.py         → results/output_entities.json
4. python compare.py --mode manual  → read and inspect
   python compare.py --mode judge   → get LLM scores
```
