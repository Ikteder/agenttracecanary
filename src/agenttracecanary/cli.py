from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audit import compare
from .model import TraceInputError
from .otlp import load_otlp
from .render import write_html, write_json, write_svg


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="agenttracecanary",
        description="Compare AI agent OTLP traces by causal structure.",
    )
    result.add_argument("baseline", help="baseline OTLP JSON")
    result.add_argument("candidate", help="candidate OTLP JSON")
    result.add_argument("--output", required=True, help="JSON evidence path")
    result.add_argument("--html", help="optional standalone HTML report")
    result.add_argument("--svg", help="optional SVG evidence visual")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    outputs = [Path(value).resolve() for value in (args.output, args.html, args.svg) if value]
    inputs = [Path(args.baseline).resolve(), Path(args.candidate).resolve()]
    if len(set(outputs)) != len(outputs) or set(outputs) & set(inputs):
        print("error: input and output paths must be distinct", file=sys.stderr)
        return 2
    try:
        report = compare(load_otlp(args.baseline), load_otlp(args.candidate))
        write_json(report, args.output)
        if args.html:
            write_html(report, args.html)
        if args.svg:
            write_svg(report, args.svg)
    except (TraceInputError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        f"{report['verdict']}: {report['summary']['finding_count']} findings across "
        f"{report['summary']['candidate_cases']} candidate cases"
    )
    return 1 if report["verdict"] == "regression" else 0


if __name__ == "__main__":
    raise SystemExit(main())
