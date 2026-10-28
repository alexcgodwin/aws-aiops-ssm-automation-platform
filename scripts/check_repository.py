"""Prevent publishing credentials, state, artifacts and accidental active remediation."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    problems: list[str] = []
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            continue
        if any(part in (".terraform", "__pycache__", ".venv") for part in path.parts):
            problems.append(f"Forbidden directory: {relative}")
        if path.name in ("terraform.tfvars", "backend.hcl", ".env", "credentials", "triage-lambda.zip") or path.suffix in (".tfstate", ".pem", ".key", ".p12"):
            problems.append(f"Potential secret artifact: {relative}")
        if path.suffix in (".tf", ".py", ".json", ".md", ".yml", ".yaml"):
            raw = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", raw):
                problems.append(f"PEM private key detected in {relative}")
    print("\n".join(problems) if problems else "Repository hygiene checks passed")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
