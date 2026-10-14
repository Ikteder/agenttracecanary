from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(candidate: str, output: str, expected: int) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agenttracecanary.cli",
            "fixtures/baseline.otlp.json",
            candidate,
            "--output",
            output,
        ],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != expected:
        raise SystemExit(f"expected exit {expected}, received {completed.returncode}")


def main() -> None:
    run("fixtures/candidate.otlp.json", "artifacts/mutation-report.json", 1)
    run("fixtures/baseline.otlp.json", "artifacts/safe-report.json", 0)
    report = json.loads((ROOT / "artifacts/mutation-report.json").read_text(encoding="utf-8"))
    assert report["summary"]["detected_cases"] == 10
    assert report["summary"]["aggregate_changed_cases"] == 0
    assert report["summary"]["structural_changed_cases"] == 9
    ET.parse(ROOT / "docs/graphics/agenttracecanary-comparison.svg")


if __name__ == "__main__":
    main()
