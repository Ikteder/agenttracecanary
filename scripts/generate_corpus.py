from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    "wrong-parent",
    "tool-order",
    "flattened-agent",
    "error-rebound",
    "missing-parent",
    "duplicate-call-id",
    "interval-escape",
    "link-retarget",
    "agent-order",
    "workflow-reparent",
)


def attr(key: str, value: str) -> dict[str, Any]:
    return {"key": key, "value": {"stringValue": value}}


def span(
    prefix: str,
    ident: str,
    parent: str,
    name: str,
    operation: str,
    identity_key: str,
    identity: str,
    start: int,
    end: int,
    *,
    status: str = "STATUS_CODE_OK",
    call_id: str | None = None,
    link: tuple[str, str] | None = None,
) -> dict[str, Any]:
    attributes = [attr("gen_ai.operation.name", operation), attr(identity_key, identity)]
    if call_id:
        attributes.append(attr("gen_ai.tool.call.id", call_id))
    links = []
    if link:
        links.append(
            {
                "traceId": f"{prefix}-trace",
                "spanId": f"{prefix}-{link[0]}",
                "attributes": [attr("gen_ai.relationship.type", link[1])],
            }
        )
    raw = {
        "traceId": f"{prefix}-trace",
        "spanId": f"{prefix}-{ident}",
        "name": name,
        "startTimeUnixNano": str(start),
        "endTimeUnixNano": str(end),
        "status": {"code": status},
        "attributes": attributes,
        "links": links,
    }
    if parent:
        raw["parentSpanId"] = f"{prefix}-{parent}"
    return raw


def base_trace(prefix: str, case_id: str) -> list[dict[str, Any]]:
    spans = [
        span(
            prefix,
            "root",
            "",
            "support",
            "invoke_workflow",
            "gen_ai.workflow.name",
            "support",
            0,
            1000,
        ),
        span(
            prefix,
            "agent",
            "root",
            "planner",
            "invoke_agent",
            "gen_ai.agent.name",
            "planner",
            100,
            900,
        ),
        span(
            prefix,
            "sub",
            "agent",
            "researcher",
            "invoke_agent",
            "gen_ai.agent.name",
            "researcher",
            200,
            500,
        ),
        span(
            prefix, "plan", "sub", "plan", "chat", "gen_ai.request.model", "local-fixture", 220, 250
        ),
        span(
            prefix,
            "search",
            "sub",
            "search",
            "execute_tool",
            "gen_ai.tool.name",
            "search",
            260,
            330,
            call_id="call-1",
        ),
        span(
            prefix,
            "fetch",
            "sub",
            "fetch",
            "execute_tool",
            "gen_ai.tool.name",
            "fetch",
            350,
            430,
            call_id="call-2",
        ),
        span(
            prefix,
            "final",
            "agent",
            "final",
            "chat",
            "gen_ai.request.model",
            "local-fixture",
            520,
            700,
            link=("search", "uses_result"),
        ),
    ]
    spans[0]["attributes"].append(attr("agenttrace.case.id", case_id))
    return spans


def by_suffix(spans: list[dict[str, Any]], suffix: str) -> dict[str, Any]:
    return next(item for item in spans if item["spanId"].endswith(f"-{suffix}"))


def mutate(case_id: str, spans: list[dict[str, Any]], prefix: str) -> None:
    if case_id == "wrong-parent":
        by_suffix(spans, "search")["parentSpanId"] = f"{prefix}-plan"
    elif case_id == "tool-order":
        search, fetch = by_suffix(spans, "search"), by_suffix(spans, "fetch")
        search["startTimeUnixNano"], fetch["startTimeUnixNano"] = "350", "260"
        search["endTimeUnixNano"], fetch["endTimeUnixNano"] = "430", "330"
    elif case_id == "flattened-agent":
        by_suffix(spans, "plan")["parentSpanId"] = f"{prefix}-agent"
    elif case_id == "error-rebound":
        by_suffix(spans, "search")["status"]["code"] = "STATUS_CODE_ERROR"
        by_suffix(spans, "fetch")["status"]["code"] = "STATUS_CODE_OK"
    elif case_id == "missing-parent":
        by_suffix(spans, "fetch")["parentSpanId"] = f"{prefix}-absent"
    elif case_id == "duplicate-call-id":
        attrs = by_suffix(spans, "fetch")["attributes"]
        next(item for item in attrs if item["key"] == "gen_ai.tool.call.id")["value"][
            "stringValue"
        ] = "call-1"
    elif case_id == "interval-escape":
        by_suffix(spans, "search")["startTimeUnixNano"] = "150"
    elif case_id == "link-retarget":
        by_suffix(spans, "final")["links"][0]["spanId"] = f"{prefix}-fetch"
    elif case_id == "agent-order":
        sub, final = by_suffix(spans, "sub"), by_suffix(spans, "final")
        sub["startTimeUnixNano"], final["startTimeUnixNano"] = "520", "200"
        sub["endTimeUnixNano"], final["endTimeUnixNano"] = "800", "480"
        for suffix, start, end in (("plan", 540, 570), ("search", 580, 650), ("fetch", 670, 750)):
            item = by_suffix(spans, suffix)
            item["startTimeUnixNano"], item["endTimeUnixNano"] = str(start), str(end)
    elif case_id == "workflow-reparent":
        by_suffix(spans, "fetch")["parentSpanId"] = f"{prefix}-root"
    else:
        raise AssertionError(case_id)


def document(candidate: bool) -> dict[str, Any]:
    all_spans: list[dict[str, Any]] = []
    for index, case_id in enumerate(CASES):
        prefix = f"{'c' if candidate else 'b'}{index:02d}"
        spans = base_trace(prefix, case_id)
        if case_id == "error-rebound":
            by_suffix(spans, "fetch")["status"]["code"] = "STATUS_CODE_ERROR"
        if candidate:
            mutate(case_id, spans, prefix)
        all_spans.extend(copy.deepcopy(spans))
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": [attr("service.name", "synthetic-agent")]},
                "scopeSpans": [
                    {
                        "scope": {"name": "agenttracecanary.synthetic", "version": "1"},
                        "spans": all_spans,
                    }
                ],
            }
        ]
    }


def main() -> None:
    fixtures = ROOT / "fixtures"
    fixtures.mkdir(exist_ok=True)
    (fixtures / "baseline.otlp.json").write_text(
        json.dumps(document(False), indent=2) + "\n", encoding="utf-8"
    )
    (fixtures / "candidate.otlp.json").write_text(
        json.dumps(document(True), indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
