"""Verify runbook ownership, freshness, and approval metadata."""
from __future__ import annotations
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs" / "runbooks"
REVIEW_DAYS = 180


def check(as_of: dt.date | None = None) -> list[str]:
    as_of = as_of or dt.date.today()
    problems: list[str] = []
    files = sorted(ROOT.glob("*.md"))
    if not files:
        return ["No operational runbooks were found"]
    for file in files:
        body = file.read_text(encoding="utf-8")
        for key in ("Owner", "Last reviewed", "Approval", "Rollback"):
            if not re.search(rf"(?m)^\*\*{re.escape(key)}:\*\*\s*\S", body):
                problems.append(f"{file.name}: missing {key}")
        match = re.search(r"(?m)^\*\*Last reviewed:\*\*\s*(\d{4}-\d{2}-\d{2})", body)
        if match:
            try:
                last = dt.date.fromisoformat(match.group(1))
                if last > as_of:
                    problems.append(f"{file.name}: review date is in the future")
                elif (as_of - last).days > REVIEW_DAYS:
                    problems.append(f"{file.name}: review overdue by {(as_of - last).days - REVIEW_DAYS} days")
            except ValueError:
                problems.append(f"{file.name}: invalid review date")
    return problems


if __name__ == "__main__":
    problems = check()
    print("\n".join(problems) if problems else "Runbook ownership and review checks passed")
    raise SystemExit(bool(problems))
