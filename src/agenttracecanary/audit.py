from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .model import Finding, Span, TraceInputError


@dataclass(frozen=True)
class TraceShape:
    case_id: str
    trace_id: str
    canonical: str
    digest: str
    aggregate: dict[str, Any]


def _case_id(spans: list[Span]) -> str:
    values = {span.case_id for span in spans if span.case_id is not None}
    if len(values) != 1:
        raise TraceInputError("each trace requires exactly one agenttrace.case.id value")
    return values.pop()


def _canonical_trace(spans: list[Span]) -> str:
    by_id = {span.span_id: span for span in spans}
    children: dict[str, list[Span]] = defaultdict(list)
    roots: list[Span] = []
    for span in spans:
        if span.parent_span_id and span.parent_span_id in by_id:
            children[span.parent_span_id].append(span)
        else:
            roots.append(span)

    def render(span: Span, stack: frozenset[str]) -> str:
        if span.span_id in stack:
            return f"CYCLE({span.role})"
        ordered = sorted(
            children[span.span_id], key=lambda item: (item.start_ns, item.role, item.span_id)
        )
        link_roles = []
        for link in span.links:
            target = by_id.get(link.span_id)
            link_roles.append(f"{link.relationship}->{target.role if target else 'missing'}")
        status = "ERROR" if span.status in {"STATUS_CODE_ERROR", "2", "ERROR"} else "OK"
        nested = ",".join(render(child, stack | {span.span_id}) for child in ordered)
        links = ",".join(sorted(link_roles))
        return f"{span.role}|{status}|links({links})[{nested}]"

    ordered_roots = sorted(roots, key=lambda item: (item.start_ns, item.role, item.span_id))
    return "||".join(render(root, frozenset()) for root in ordered_roots)


def _aggregate(spans: list[Span]) -> dict[str, Any]:
    roles = Counter(span.role for span in spans)
    statuses = Counter(
        "ERROR" if span.status in {"STATUS_CODE_ERROR", "2", "ERROR"} else "OK" for span in spans
    )
    return {
        "span_count": len(spans),
        "roles": dict(sorted(roles.items())),
        "statuses": dict(sorted(statuses.items())),
    }


def _validate_trace(spans: list[Span], case_id: str) -> list[Finding]:
    findings: list[Finding] = []
    by_id = {span.span_id: span for span in spans}
    roots = [span for span in spans if not span.parent_span_id]
    if len(roots) != 1:
        findings.append(
            Finding("ROOT_COUNT", case_id, f"candidate trace has {len(roots)} root spans")
        )
    for span in spans:
        if span.end_ns < span.start_ns:
            findings.append(
                Finding("NEGATIVE_DURATION", case_id, f"{span.role} ends before it starts")
            )
        if span.parent_span_id:
            parent = by_id.get(span.parent_span_id)
            if parent is None:
                findings.append(
                    Finding("MISSING_PARENT", case_id, f"{span.role} has a missing parent")
                )
            elif span.start_ns < parent.start_ns or span.end_ns > parent.end_ns:
                findings.append(
                    Finding(
                        "PARENT_WINDOW", case_id, f"{span.role} falls outside its parent interval"
                    )
                )

        visited: set[str] = set()
        cursor = span
        while cursor.parent_span_id:
            if cursor.span_id in visited:
                findings.append(Finding("PARENT_CYCLE", case_id, f"cycle includes {span.role}"))
                break
            visited.add(cursor.span_id)
            parent = by_id.get(cursor.parent_span_id)
            if parent is None:
                break
            cursor = parent

    calls: dict[str, list[Span]] = defaultdict(list)
    for span in spans:
        if span.operation == "execute_tool":
            call_id = span.attributes.get("gen_ai.tool.call.id")
            if call_id:
                calls[str(call_id)].append(span)
            ancestor = by_id.get(span.parent_span_id)
            seen: set[str] = set()
            valid_parent = False
            while ancestor is not None and ancestor.span_id not in seen:
                seen.add(ancestor.span_id)
                if ancestor.operation in {"invoke_agent", "invoke_workflow"}:
                    valid_parent = True
                    break
                ancestor = by_id.get(ancestor.parent_span_id)
            if not valid_parent:
                findings.append(
                    Finding(
                        "TOOL_OUTSIDE_AGENT", case_id, f"{span.role} has no agent/workflow ancestor"
                    )
                )
    for call_id, matched in calls.items():
        if len(matched) > 1:
            findings.append(
                Finding(
                    "DUPLICATE_TOOL_CALL_ID",
                    case_id,
                    f"tool call id {call_id!r} appears on {len(matched)} execution spans",
                )
            )
    return findings


def shapes(spans: list[Span]) -> dict[str, TraceShape]:
    grouped: dict[str, list[Span]] = defaultdict(list)
    for span in spans:
        grouped[span.trace_id].append(span)
    result: dict[str, TraceShape] = {}
    for trace_id, trace_spans in grouped.items():
        case_id = _case_id(trace_spans)
        if case_id in result:
            raise TraceInputError(f"duplicate case id across traces: {case_id}")
        canonical = _canonical_trace(trace_spans)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        result[case_id] = TraceShape(case_id, trace_id, canonical, digest, _aggregate(trace_spans))
    return result


def compare(baseline: list[Span], candidate: list[Span]) -> dict[str, Any]:
    base_shapes = shapes(baseline)
    candidate_shapes = shapes(candidate)
    findings: list[Finding] = []
    structural_changed = 0
    aggregate_changed = 0

    base_cases = set(base_shapes)
    candidate_cases = set(candidate_shapes)
    for case_id in sorted(base_cases - candidate_cases):
        findings.append(Finding("MISSING_CASE", case_id, "candidate is missing a baseline case"))
    for case_id in sorted(candidate_cases - base_cases):
        findings.append(
            Finding("NEW_CASE", case_id, "candidate contains a case absent from baseline")
        )

    candidate_by_trace: dict[str, list[Span]] = defaultdict(list)
    for span in candidate:
        candidate_by_trace[span.trace_id].append(span)
    for case_id in sorted(base_cases & candidate_cases):
        base = base_shapes[case_id]
        current = candidate_shapes[case_id]
        findings.extend(_validate_trace(candidate_by_trace[current.trace_id], case_id))
        if base.aggregate != current.aggregate:
            aggregate_changed += 1
        if base.digest != current.digest:
            structural_changed += 1
            findings.append(
                Finding(
                    "STRUCTURE_CHANGED",
                    case_id,
                    "candidate causal shape differs from baseline",
                    baseline=base.canonical,
                    candidate=current.canonical,
                )
            )

    unique = {(finding.code, finding.case_id, finding.message): finding for finding in findings}
    ordered = sorted(unique.values(), key=lambda item: (item.case_id, item.code, item.message))
    detected_cases = len({finding.case_id for finding in ordered})
    report = {
        "schema_version": 1,
        "verdict": "regression" if ordered else "match",
        "summary": {
            "baseline_cases": len(base_shapes),
            "candidate_cases": len(candidate_shapes),
            "structural_changed_cases": structural_changed,
            "aggregate_changed_cases": aggregate_changed,
            "detected_cases": detected_cases,
            "finding_count": len(ordered),
        },
        "findings": [finding.to_dict() for finding in ordered],
        "cases": [
            {
                "case_id": case_id,
                "baseline_digest": base_shapes[case_id].digest,
                "candidate_digest": candidate_shapes[case_id].digest,
                "aggregate_equal": base_shapes[case_id].aggregate
                == candidate_shapes[case_id].aggregate,
            }
            for case_id in sorted(base_cases & candidate_cases)
        ],
    }
    report["evidence_digest"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return report
