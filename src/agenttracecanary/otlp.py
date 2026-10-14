from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import Link, Span, TraceInputError


def _value(value: Any) -> Any:
    if not isinstance(value, dict):
        raise TraceInputError("OTLP attribute value must be an object")
    keys = (
        "stringValue",
        "boolValue",
        "intValue",
        "doubleValue",
        "bytesValue",
    )
    for key in keys:
        if key in value:
            return value[key]
    if "arrayValue" in value:
        values = value["arrayValue"].get("values", [])
        return [_value(item) for item in values]
    if "kvlistValue" in value:
        return _attributes(value["kvlistValue"].get("values", []))
    raise TraceInputError("unsupported OTLP attribute value")


def _attributes(items: Any) -> dict[str, Any]:
    if items is None:
        return {}
    if not isinstance(items, list):
        raise TraceInputError("OTLP attributes must be a list")
    result: dict[str, Any] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("key"), str):
            raise TraceInputError("every OTLP attribute requires a string key")
        key = item["key"]
        if key in result:
            raise TraceInputError(f"duplicate OTLP attribute: {key}")
        result[key] = _value(item.get("value"))
    return result


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise TraceInputError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TraceInputError(f"{field} must be an integer") from exc
    if parsed < 0:
        raise TraceInputError(f"{field} cannot be negative")
    return parsed


def _links(items: Any) -> tuple[Link, ...]:
    if items is None:
        return ()
    if not isinstance(items, list):
        raise TraceInputError("span links must be a list")
    links: list[Link] = []
    for raw in items:
        attrs = _attributes(raw.get("attributes", []))
        links.append(
            Link(
                trace_id=str(raw.get("traceId", "")),
                span_id=str(raw.get("spanId", "")),
                relationship=str(attrs.get("gen_ai.relationship.type", "link")),
            )
        )
    return tuple(links)


def load_otlp(path: str | Path) -> list[Span]:
    source = Path(path)
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TraceInputError(f"cannot read {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise TraceInputError(f"invalid JSON in {source}: {exc}") from exc

    resources = document.get("resourceSpans") if isinstance(document, dict) else None
    if not isinstance(resources, list) or not resources:
        raise TraceInputError("OTLP JSON requires a non-empty resourceSpans list")

    spans: list[Span] = []
    seen: set[tuple[str, str]] = set()
    for resource in resources:
        resource_attrs = _attributes(resource.get("resource", {}).get("attributes", []))
        scopes = resource.get("scopeSpans", [])
        if not isinstance(scopes, list):
            raise TraceInputError("scopeSpans must be a list")
        for scope in scopes:
            scope_attrs = _attributes(scope.get("scope", {}).get("attributes", []))
            for raw in scope.get("spans", []):
                trace_id = str(raw.get("traceId", ""))
                span_id = str(raw.get("spanId", ""))
                if not trace_id or not span_id:
                    raise TraceInputError("every span requires traceId and spanId")
                key = (trace_id, span_id)
                if key in seen:
                    raise TraceInputError(f"duplicate span identity: {trace_id}/{span_id}")
                seen.add(key)
                attrs = dict(resource_attrs)
                attrs.update(scope_attrs)
                attrs.update(_attributes(raw.get("attributes", [])))
                status = raw.get("status", {})
                status_code = str(status.get("code", "STATUS_CODE_UNSET"))
                spans.append(
                    Span(
                        trace_id=trace_id,
                        span_id=span_id,
                        parent_span_id=str(raw.get("parentSpanId", "")),
                        name=str(raw.get("name", "")),
                        start_ns=_integer(raw.get("startTimeUnixNano", 0), "startTimeUnixNano"),
                        end_ns=_integer(raw.get("endTimeUnixNano", 0), "endTimeUnixNano"),
                        status=status_code,
                        attributes=attrs,
                        links=_links(raw.get("links", [])),
                    )
                )
    if not spans:
        raise TraceInputError("OTLP JSON contains no spans")
    return spans
