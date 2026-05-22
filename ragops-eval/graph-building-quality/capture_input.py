"""
Capture step 4 input: parse a small SEC filing and save chunks to results/input_chunks.json.

Usage:
    python capture_input.py
    python capture_input.py --file fixtures/sample.html
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

SEC_PARSER_URL = os.getenv("SEC_PARSER_URL", "http://localhost:8001")
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))


def _auth_headers() -> dict:
    """Return Google OIDC identity token header if gcloud is available."""
    import subprocess
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-identity-token"], stderr=subprocess.DEVNULL
        ).decode().strip()
        return {"Authorization": f"Bearer {token}"}
    except Exception:
        return {}


def parse_file(file_path: str) -> list:
    url = f"{SEC_PARSER_URL.rstrip('/')}/api/sec/parse"
    file_name = Path(file_path).name
    with open(file_path, "rb") as f:
        resp = requests.post(
            url,
            files={"files": (file_name, f, "application/octet-stream")},
            headers=_auth_headers(),
            timeout=120,
        )
    resp.raise_for_status()
    return resp.json()["documents"]


def extract_chunk_text(chunk) -> tuple:
    """Handle chunk as string, list of chars, or dict."""
    if isinstance(chunk, str):
        return chunk, ""
    if isinstance(chunk, list):
        return "".join(chunk), ""
    if isinstance(chunk, dict):
        text = chunk.get("text") or chunk.get("content") or ""
        section = chunk.get("source_section", "")
        return text, section
    return "", ""


def flatten_chunks(documents: list) -> list:
    chunks = []
    chunk_id = 0
    for doc in documents:
        for raw_chunk in doc.get("chunks", []):
            chunk_id += 1
            text, section = extract_chunk_text(raw_chunk)
            chunks.append({
                "chunk_id": chunk_id,
                "file_name": doc.get("filename", ""),
                "source_section": section,
                "text": text,
            })
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="fixtures/sample.html")
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"File not found: {args.file}")
        sys.exit(1)

    print(f"Parsing {args.file} via sec-parser at {SEC_PARSER_URL} ...")
    try:
        documents = parse_file(args.file)
    except Exception as e:
        print(f"sec-parser call failed: {e}")
        sys.exit(1)

    chunks = flatten_chunks(documents)
    print(f"Got {len(chunks)} chunk(s) from {len(documents)} document(s)")

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "input_chunks.json"
    with open(out, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"Saved → {out}")


if __name__ == "__main__":
    main()
