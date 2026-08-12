"""Offline retrieval and citation evaluation for DocIntel AI."""

import argparse
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate(rows: list[dict]) -> dict[str, float]:
    precisions, recalls = [], []
    cited = correct = 0
    for row in rows:
        relevant = set(row["relevant_chunk_ids"])
        retrieved = row["retrieved_chunk_ids"]
        hits = len(relevant.intersection(retrieved))
        precisions.append(safe_div(hits, len(retrieved)))
        recalls.append(safe_div(hits, len(relevant)))
        citations = row["cited_chunk_ids"]
        cited += len(citations)
        correct += len(set(citations).intersection(row["supported_citation_ids"]))
    return {
        "queries": len(rows),
        "macro_precision_at_k": sum(precisions) / len(precisions),
        "macro_recall_at_k": sum(recalls) / len(recalls),
        "citation_correctness": safe_div(correct, cited),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("golden_set.jsonl"))
    parser.add_argument("--min-precision", type=float, default=0.40)
    parser.add_argument("--min-recall", type=float, default=0.90)
    parser.add_argument("--min-citation-correctness", type=float, default=0.80)
    args = parser.parse_args()
    metrics = evaluate(load_jsonl(args.dataset))
    print(json.dumps(metrics, indent=2))
    assert metrics["macro_precision_at_k"] >= args.min_precision
    assert metrics["macro_recall_at_k"] >= args.min_recall
    assert metrics["citation_correctness"] >= args.min_citation_correctness


if __name__ == "__main__":
    main()
