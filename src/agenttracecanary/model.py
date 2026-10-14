from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class TraceInputError(ValueError):
    """Raised when an OTLP document cannot be audited safely."""


@dataclass(frozen=True)
class Link:
    trace_id: str
    span_id: str
    relationship: str


@dataclass(frozen=True)
class Span:
    trace_id: str
    span_id: str
    parent_span_id: str
    name: str
    start_ns: int
    end_ns: int
    status: str
    attributes: dict[str, Any] = field(default_factory=dict)
    links: tuple[Link, ...] = ()

    @property
    def operation(self) -> str:
        return str(self.attributes.get("gen_ai.operation.name", ""))

    @property
    def role(self) -> str:
        operation = self.operation or "span"
        if operation == "invoke_agent":
            identity = self.attributes.get("gen_ai.agent.name", self.name)
        elif operation == "invoke_workflow":
            identity = self.attributes.get("gen_ai.workflow.name", self.name)
        elif operation == "execute_tool":
            identity = self.attributes.get("gen_ai.tool.name", self.name)
        else:
            identity = self.attributes.get("openinference.span.kind", self.name)
        return f"{operation}:{identity}"

    @property
    def case_id(self) -> str | None:
        value = self.attributes.get("agenttrace.case.id")
        return None if value is None else str(value)


@dataclass(frozen=True)
class Finding:
    code: str
    case_id: str
    message: str
    baseline: str | None = None
    candidate: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "case_id": self.case_id,
            "message": self.message,
            "baseline": self.baseline,
            "candidate": self.candidate,
        }
