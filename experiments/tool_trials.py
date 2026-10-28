"""Evidence-labeled evaluation rubric for operational tooling.

Inputs are hypothetical examples until measured with a repeatable pilot.
Never present example scores as real benchmark results.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

WEIGHTS = {"security": 0.30, "operability": 0.25, "cost": 0.15, "reliability": 0.20, "integration": 0.10}


def evaluate(data: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for item in data["candidates"]:
        scores = item["scores"]
        if set(scores) != set(WEIGHTS) or any(type(scores[k]) not in (int, float) or not 0 <= scores[k] <= 5 for k in WEIGHTS):
            raise ValueError(f"Invalid scores: {item.get('name')}")
        score = round(sum(scores[k] * weight for k, weight in WEIGHTS.items()), 2)
        security_floor_met = scores["security"] >= 3.5
        recommendation = "reject" if not security_floor_met else "pilot" if score >= 3.7 else "revisit"
        results.append({
            "tool": item["name"], "weighted_score_out_of_5": score,
            "security_floor_met": security_floor_met, "recommendation": recommendation,
            "evidence_type": item.get("evidence_type", "unverified"),
            "measured_results_claimed": item.get("evidence_type") == "measured",
        })
    return sorted(results, key=lambda result: result["weighted_score_out_of_5"], reverse=True)


if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "experiments/illustrative-tool-evaluation.json")
    print(json.dumps(evaluate(json.loads(path.read_text(encoding="utf-8"))), indent=2))
