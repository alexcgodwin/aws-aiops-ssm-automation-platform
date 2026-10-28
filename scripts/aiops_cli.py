"""Offline workflow demonstrations; no cloud authentication or writes."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))
from triage import classify, normalize_event, safe_summary  # noqa: E402
from rca import draft_rca  # noqa: E402
from tool_trials import evaluate  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline AWS SSM AIOps project workflows")
    parser.add_argument("workflow", choices=("triage", "rca", "tool-trial"))
    parser.add_argument("--input", default=None)
    args = parser.parse_args()
    if args.workflow == "tool-trial":
        p = Path(args.input or ROOT / "experiments/illustrative-tool-evaluation.json")
        print(json.dumps(evaluate(json.loads(p.read_text(encoding="utf-8"))), indent=2))
        return
    p = Path(args.input or ROOT / "examples/cloudwatch-alarm.json")
    assessment = classify(normalize_event(json.loads(p.read_text(encoding="utf-8"))))
    print(json.dumps(assessment, indent=2) if args.workflow == "triage" else draft_rca(assessment))


if __name__ == "__main__":
    main()
