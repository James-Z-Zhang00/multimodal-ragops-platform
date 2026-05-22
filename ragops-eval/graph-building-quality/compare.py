"""
Compare step 4 input vs output.

Loads input_chunks.json (from capture_input.py) and output_entities.json
(from capture_output.py), matches them by chunk text, and shows what the
LLM extracted from each chunk.

Modes:
  --mode manual   Print formatted side-by-side for human review (default)
  --mode judge    Score each chunk with an LLM judge

Usage:
    python compare.py --mode manual
    python compare.py --mode judge
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

JUDGE_SYSTEM_PROMPT = """\
You are evaluating entity and relationship extraction quality from a financial SEC filing.

Given the original text and what was extracted from it, score on three dimensions (0.0 to 1.0 each):
- completeness: Are all important entities present? Did the model miss anything significant?
- accuracy: Are entity types correctly classified (Company, Executive, FinancialMetric, etc.)?
- relationship_quality: Are the relationships logically correct and meaningful?

Return ONLY a JSON object in this exact format:
{
  "completeness": 0.0,
  "accuracy": 0.0,
  "relationship_quality": 0.0,
  "reasoning": "brief explanation"
}"""


def load_json(path: Path, label: str) -> list:
    if not path.exists():
        print(f"File not found: {path}\nRun {label} first.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def match_pairs(inputs: list, outputs: list) -> list:
    """Match input chunks to output chunks by first 120 chars of text."""
    output_by_text = {(c.get("chunk_text") or "")[:120]: c for c in outputs}
    pairs = []
    for inp in inputs:
        key = (inp.get("text") or "")[:120]
        pairs.append({"input": inp, "output": output_by_text.get(key, {})})
    return pairs


# ── Manual mode ──────────────────────────────────────────────────────────────

def print_manual(pairs: list):
    for i, pair in enumerate(pairs, 1):
        inp = pair["input"]
        out = pair["output"]

        section = inp.get("source_section", "")
        header = f"Chunk {i}" + (f"  [{section}]" if section else "")
        print(f"\n{'─' * 70}")
        print(header)
        print(f"{'─' * 70}")

        print("\nINPUT TEXT:")
        for line in (inp.get("text") or "").split("\n"):
            print(f"  {line}")

        if not out:
            print("\n  (no matching output found)")
            continue

        entities = out.get("entities", [])
        print(f"\nEXTRACTED ENTITIES ({len(entities)}):")
        if entities:
            rows = [
                [e.get("name", ""), e.get("type", ""), (e.get("description") or "")[:60]]
                for e in entities
            ]
            print(tabulate(rows, headers=["Name", "Type", "Description"], tablefmt="simple"))
        else:
            print("  (none)")

        rels = out.get("relationships", [])
        print(f"\nEXTRACTED RELATIONSHIPS ({len(rels)}):")
        if rels:
            rows = [[r.get("source", ""), r.get("type", ""), r.get("target", "")] for r in rels]
            print(tabulate(rows, headers=["Source", "Type", "Target"], tablefmt="simple"))
        else:
            print("  (none)")

    matched = sum(1 for p in pairs if p["output"])
    total_e = sum(len(p["output"].get("entities", [])) for p in pairs if p["output"])
    total_r = sum(len(p["output"].get("relationships", [])) for p in pairs if p["output"])
    print(f"\n{'─' * 70}")
    print(f"TOTAL  {len(pairs)} input chunks  |  {matched} matched  |  {total_e} entities  |  {total_r} relationships")


# ── Judge mode ────────────────────────────────────────────────────────────────

def judge_chunk(client, pair: dict) -> dict:
    inp = pair["input"]
    out = pair["output"]
    user_content = (
        f"TEXT:\n{inp.get('text', '')}\n\n"
        f"EXTRACTED ENTITIES:\n{json.dumps(out.get('entities', []), indent=2)}\n\n"
        f"EXTRACTED RELATIONSHIPS:\n{json.dumps(out.get('relationships', []), indent=2)}"
    )
    resp = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def run_judge(pairs: list):
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY not set in .env")
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    results = []
    score_lists = {"completeness": [], "accuracy": [], "relationship_quality": []}

    for i, pair in enumerate(pairs, 1):
        print(f"Judging chunk {i}/{len(pairs)} ...", end=" ", flush=True)
        try:
            scores = judge_chunk(client, pair)
            results.append({"chunk_id": i, "scores": scores})
            for k in score_lists:
                if k in scores:
                    score_lists[k].append(float(scores[k]))
            print(
                f"completeness={scores.get('completeness', '?'):.2f}  "
                f"accuracy={scores.get('accuracy', '?'):.2f}  "
                f"relationship_quality={scores.get('relationship_quality', '?'):.2f}"
            )
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"chunk_id": i, "error": str(e)})

    averages = {k: sum(v) / len(v) if v else 0.0 for k, v in score_lists.items()}

    print(f"\n{'─' * 50}")
    print("AVERAGES:")
    print(tabulate([[k, f"{v:.3f}"] for k, v in averages.items()],
                   headers=["Metric", "Score"], tablefmt="simple"))

    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"comparison_{ts}.json"
    with open(out_path, "w") as f:
        json.dump({"averages": averages, "per_chunk": results}, f, indent=2)
    print(f"\nSaved → {out_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["manual", "judge"], default="manual")
    args = parser.parse_args()

    inputs = load_json(RESULTS_DIR / "input_chunks.json", "capture_input.py")
    outputs = load_json(RESULTS_DIR / "output_entities.json", "capture_output.py")
    pairs = match_pairs(inputs, outputs)

    print(f"Loaded {len(inputs)} input chunks, {len(outputs)} output chunks → {len(pairs)} pairs\n")

    if args.mode == "manual":
        print_manual(pairs)
    else:
        run_judge(pairs)


if __name__ == "__main__":
    main()
