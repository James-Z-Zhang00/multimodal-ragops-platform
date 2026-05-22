"""
Capture step 4 output: query Neo4j for entities and relationships extracted per chunk.
Run this after a graph build using the same file as capture_input.py.

Usage:
    python capture_output.py --file-name sample.html
"""
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))


def query_chunks(driver, file_name: str) -> list:
    with driver.session() as session:
        # Entities per chunk
        entity_rows = session.run(
            """
            MATCH (c:__Chunk__)
            WHERE c.fileName = $file_name
            OPTIONAL MATCH (c)-[:MENTIONS]->(e:__Entity__)
            WITH c, collect(DISTINCT {
                name: e.id,
                type: [l IN labels(e) WHERE l <> '__Entity__'][0],
                description: e.description
            }) AS entities
            RETURN c.id AS chunk_id, c.text AS chunk_text, entities
            ORDER BY c.content_offset
            """,
            file_name=file_name,
        )

        chunks = []
        for row in entity_rows:
            chunks.append({
                "chunk_id": row["chunk_id"],
                "chunk_text": row["chunk_text"],
                "entities": [e for e in row["entities"] if e.get("name")],
                "relationships": [],
            })

        # Relationships between entities that share a chunk
        rel_rows = session.run(
            """
            MATCH (c:__Chunk__)-[:MENTIONS]->(s:__Entity__)-[r]->(t:__Entity__)<-[:MENTIONS]-(c)
            WHERE c.fileName = $file_name
              AND NOT type(r) IN ['SIMILAR', 'IN_COMMUNITY']
            RETURN DISTINCT
                c.id AS chunk_id,
                s.id AS source,
                type(r) AS rel_type,
                t.id AS target,
                r.description AS description
            """,
            file_name=file_name,
        )

        rel_map = {}
        for row in rel_rows:
            rel_map.setdefault(row["chunk_id"], []).append({
                "source": row["source"],
                "type": row["rel_type"],
                "target": row["target"],
                "description": row["description"],
            })

        for chunk in chunks:
            chunk["relationships"] = rel_map.get(chunk["chunk_id"], [])

    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file-name",
        default="sample.html",
        help="File name as stored in Neo4j (e.g. sample.html)",
    )
    args = parser.parse_args()

    print(f"Connecting to Neo4j at {NEO4J_URI} ...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        sys.exit(1)

    print(f"Querying chunks for file: {args.file_name}")
    chunks = query_chunks(driver, args.file_name)
    driver.close()

    if not chunks:
        print(f"No chunks found for '{args.file_name}'. Has the graph been built?")
        sys.exit(1)

    total_entities = sum(len(c["entities"]) for c in chunks)
    total_rels = sum(len(c["relationships"]) for c in chunks)
    print(f"Found {len(chunks)} chunk(s), {total_entities} entities, {total_rels} relationships")

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "output_entities.json"
    with open(out, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"Saved → {out}")


if __name__ == "__main__":
    main()
