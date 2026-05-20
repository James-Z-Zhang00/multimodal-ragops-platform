# graph-building-quality

Benchmarks for the graph-building pipeline. Start with step 4 (entity/relationship extraction).

Each script is independent — no shared imports.

## Step 4: Extraction Quality

Three scripts, run in order:

```
capture_input.py   → results/input_chunks.json
    [run a graph build on the same file]
capture_output.py  → results/output_entities.json
compare.py         → terminal output or results/comparison_TIMESTAMP.json
```

### Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in values
```

### 1. Capture Input (chunks going into step 4)

```bash
python capture_input.py --file fixtures/sample.html
```

Calls sec-parser, saves all chunks to `results/input_chunks.json`.

### 2. Build the graph

Run a full build on the same file via the build-service:

```bash
curl -X POST http://localhost:8004/build/full
```

### 3. Capture Output (entities extracted in step 4)

```bash
python capture_output.py --file-name sample.html
```

Queries Neo4j, saves entities and relationships per chunk to `results/output_entities.json`.

### 4. Compare

**Manual** — read and judge yourself:
```bash
python compare.py --mode manual
```

**LLM judge** — GPT-4o scores completeness, accuracy, relationship quality (0.0–1.0):
```bash
python compare.py --mode judge
```

## Fixtures

`fixtures/sample.html` — small Apple 8-K with 3 sections: financial results, market risk, executive appointment. Produces ~3–5 chunks. Replace with any SEC filing HTML for broader testing.
