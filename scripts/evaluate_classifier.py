from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import Settings
from app.main import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate smart-ticket-classifier against a labeled dataset.")
    parser.add_argument(
        "--input",
        default="data/sample_tickets.json",
        help="Path to the labeled dataset JSON file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional number of examples to evaluate.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to persist the evaluation report as JSON.",
    )
    return parser.parse_args()


def load_dataset(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Dataset must be a JSON array.")
    return payload


def build_report(dataset: list[dict[str, object]]) -> dict[str, object]:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "evaluation.db"
        settings = Settings(
            environment="evaluation",
            database_url=f"sqlite:///{database_path.as_posix()}",
            log_level="WARNING",
        )
        app = create_app(settings)

        with TestClient(app) as client:
            return evaluate_examples(client, dataset)


def evaluate_examples(client: TestClient, dataset: list[dict[str, object]]) -> dict[str, object]:
    results: list[dict[str, object]] = []
    category_hits = 0
    priority_hits = 0
    llm_fallback_count = 0
    confidence_values: list[float] = []

    for example in dataset:
        payload = {
            "title": example["title"],
            "description": example["description"],
            "requester": example["requester"],
            "source_system": example.get("source_system"),
        }
        response = client.post("/classify", json=payload)
        response.raise_for_status()
        prediction = response.json()["data"]

        predicted_category = prediction["category"]
        predicted_priority = prediction["priority"]
        expected_category = example["expected_category"]
        expected_priority = example["expected_priority"]

        category_hit = predicted_category == expected_category
        priority_hit = predicted_priority == expected_priority
        decision_source = prediction["decision_source"]

        category_hits += int(category_hit)
        priority_hits += int(priority_hit)
        llm_fallback_count += int(decision_source == "llm")
        confidence_values.append(float(prediction["confidence_score"]))

        results.append(
            {
                "title": example["title"],
                "predicted_category": predicted_category,
                "expected_category": expected_category,
                "predicted_priority": predicted_priority,
                "expected_priority": expected_priority,
                "decision_source": decision_source,
                "confidence_score": prediction["confidence_score"],
                "category_hit": category_hit,
                "priority_hit": priority_hit,
            }
        )

    total = len(results)
    report = {
        "total_examples": total,
        "category_accuracy": round(category_hits / total, 4) if total else 0.0,
        "priority_accuracy": round(priority_hits / total, 4) if total else 0.0,
        "llm_fallback_rate": round(llm_fallback_count / total, 4) if total else 0.0,
        "average_confidence_score": round(sum(confidence_values) / total, 4) if total else 0.0,
        "results": results,
    }
    return report


def main() -> None:
    args = parse_args()
    dataset = load_dataset(Path(args.input))
    if args.limit is not None:
        dataset = dataset[: args.limit]

    report = build_report(dataset)
    print(json.dumps(report, indent=2, ensure_ascii=True))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")


if __name__ == "__main__":
    main()
