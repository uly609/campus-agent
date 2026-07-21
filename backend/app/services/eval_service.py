from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_eval_and_load() -> dict[str, object]:
    root = Path(__file__).resolve().parents[3]
    subprocess.run([sys.executable, "evals/run_eval.py", "--write-report"], cwd=root, check=True)
    latest = root / "evals" / "reports" / "latest.json"
    return json.loads(latest.read_text(encoding="utf-8"))

