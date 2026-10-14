from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from agenttracecanary.audit import compare
from agenttracecanary.model import TraceInputError
from agenttracecanary.otlp import load_otlp

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "fixtures" / "baseline.otlp.json"
CANDIDATE = ROOT / "fixtures" / "candidate.otlp.json"


def test_mutation_corpus_beats_aggregate_baseline() -> None:
    report = compare(load_otlp(BASELINE), load_otlp(CANDIDATE))
    assert report["verdict"] == "regression"
    assert report["summary"]["baseline_cases"] == 10
    assert report["summary"]["candidate_cases"] == 10
    assert report["summary"]["aggregate_changed_cases"] == 0
    assert report["summary"]["detected_cases"] == 10
    assert report["summary"]["structural_changed_cases"] == 9


def test_identical_shape_ignores_span_ids_and_absolute_time() -> None:
    baseline = load_otlp(BASELINE)
    candidate = copy.deepcopy(baseline)
    shifted = []
    for span in candidate:
        shifted.append(
            span.__class__(
                trace_id=f"new-{span.trace_id}",
                span_id=f"new-{span.span_id}",
                parent_span_id=f"new-{span.parent_span_id}" if span.parent_span_id else "",
                name=span.name,
                start_ns=span.start_ns + 100_000,
                end_ns=span.end_ns + 100_000,
                status=span.status,
                attributes=span.attributes,
                links=tuple(
                    link.__class__(
                        trace_id=f"new-{link.trace_id}",
                        span_id=f"new-{link.span_id}",
                        relationship=link.relationship,
                    )
                    for link in span.links
                ),
            )
        )
    report = compare(baseline, shifted)
    assert report["verdict"] == "match"
    assert report["summary"]["finding_count"] == 0


def test_duplicate_attribute_is_rejected(tmp_path: Path) -> None:
    document = json.loads(BASELINE.read_text(encoding="utf-8"))
    raw = document["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    raw["attributes"].append(copy.deepcopy(raw["attributes"][0]))
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(TraceInputError, match="duplicate OTLP attribute"):
        load_otlp(path)


def test_duplicate_span_identity_is_rejected(tmp_path: Path) -> None:
    document = json.loads(BASELINE.read_text(encoding="utf-8"))
    spans = document["resourceSpans"][0]["scopeSpans"][0]["spans"]
    spans.append(copy.deepcopy(spans[0]))
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(TraceInputError, match="duplicate span identity"):
        load_otlp(path)


def test_cli_exit_contract_and_outputs(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    html = tmp_path / "report.html"
    svg = tmp_path / "report.svg"
    command = [
        sys.executable,
        "-m",
        "agenttracecanary.cli",
        str(BASELINE),
        str(CANDIDATE),
        "--output",
        str(output),
        "--html",
        str(html),
        "--svg",
        str(svg),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    assert completed.returncode == 1
    assert "regression:" in completed.stdout
    assert output.exists() and html.exists() and svg.exists()
    safe = subprocess.run(
        command[:4] + [str(BASELINE)] + command[5:],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert safe.returncode == 0


def test_output_collision_is_rejected(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agenttracecanary.cli",
            str(BASELINE),
            str(CANDIDATE),
            "--output",
            str(BASELINE),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "must be distinct" in completed.stderr
