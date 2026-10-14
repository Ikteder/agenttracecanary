from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def write_json(report: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_html(report: dict[str, Any], path: str | Path) -> None:
    summary = report["summary"]
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['case_id'])}</td>"
        f"<td><code>{html.escape(item['code'])}</code></td>"
        f"<td>{html.escape(item['message'])}</td>"
        "</tr>"
        for item in report["findings"]
    )
    if not rows:
        rows = '<tr><td colspan="3">No structural regression found.</td></tr>'
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgentTrace Canary report</title><style>
:root{{--ink:#15202b;--muted:#5e6b78;--paper:#f4f7f4;--card:#fff;--accent:#0b7a75;--bad:#b42318}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1080px;margin:auto;padding:32px 20px}}h1{{font-size:clamp(2rem,6vw,4rem);line-height:1;margin:.2em 0}}
.eyebrow{{color:var(--accent);font-weight:800;letter-spacing:.08em;text-transform:uppercase}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}
.card{{background:var(--card);border:1px solid #dce5df;border-radius:14px;padding:18px}}.number{{font-size:2rem;font-weight:800}}
.bad{{color:var(--bad)}}.table-wrap{{overflow:auto;background:var(--card);border:1px solid #dce5df;border-radius:14px}}
table{{border-collapse:collapse;width:100%;min-width:650px}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #e6ece8;vertical-align:top}}
code{{font-size:.85em}}footer{{color:var(--muted);margin-top:24px;overflow-wrap:anywhere}}@media(max-width:700px){{.grid{{grid-template-columns:1fr 1fr}}}}
</style></head><body><main><div class="eyebrow">Offline OTLP structural audit</div><h1>{html.escape(report["verdict"]).title()}</h1>
<p>Span IDs and absolute timestamps are ignored. Parentage, ordered roles, status placement, optional typed links, and local trace invariants are compared.</p>
<section class="grid"><div class="card"><div class="number">{summary["baseline_cases"]}</div>baseline cases</div>
<div class="card"><div class="number">{summary["candidate_cases"]}</div>candidate cases</div>
<div class="card"><div class="number bad">{summary["structural_changed_cases"]}</div>changed shapes</div>
<div class="card"><div class="number bad">{summary["finding_count"]}</div>findings</div></section>
<div class="table-wrap"><table><thead><tr><th>Case</th><th>Finding</th><th>Explanation</th></tr></thead><tbody>{rows}</tbody></table></div>
<footer>Evidence digest: <code>{html.escape(report["evidence_digest"])}</code></footer></main></body></html>"""
    Path(path).write_text(document, encoding="utf-8")


def write_svg(report: dict[str, Any], path: str | Path) -> None:
    summary = report["summary"]
    total = max(summary["candidate_cases"], 1)
    aggregate = summary["aggregate_changed_cases"]
    structural = summary["detected_cases"]
    scale = 480 / total
    document = f"""<svg xmlns="http://www.w3.org/2000/svg" width="760" height="300" viewBox="0 0 760 300" role="img" aria-labelledby="title desc">
<title id="title">Structural comparison catches regressions hidden from aggregate counts</title>
<desc id="desc">Aggregate-only comparison flags {aggregate} of {total} cases. AgentTrace Canary flags {structural} of {total} cases.</desc>
<rect width="760" height="300" rx="24" fill="#f4f7f4"/><text x="44" y="52" font-family="system-ui,sans-serif" font-size="25" font-weight="700" fill="#15202b">Same counts can hide a changed causal trace</text>
<text x="44" y="104" font-family="system-ui,sans-serif" font-size="16" fill="#465461">Aggregate baseline</text><rect x="230" y="82" width="480" height="30" rx="8" fill="#dce5df"/><rect x="230" y="82" width="{aggregate * scale:.1f}" height="30" rx="8" fill="#8a99a6"/><text x="720" y="104" text-anchor="end" font-family="system-ui,sans-serif" font-weight="700" fill="#15202b">{aggregate}/{total}</text>
<text x="44" y="170" font-family="system-ui,sans-serif" font-size="16" fill="#465461">Causal audit</text><rect x="230" y="148" width="480" height="30" rx="8" fill="#dce5df"/><rect x="230" y="148" width="{structural * scale:.1f}" height="30" rx="8" fill="#0b7a75"/><text x="720" y="170" text-anchor="end" font-family="system-ui,sans-serif" font-weight="700" fill="#15202b">{structural}/{total}</text>
<text x="44" y="230" font-family="system-ui,sans-serif" font-size="14" fill="#5e6b78">Synthetic mutation corpus, seed 20261013. This is regression evidence, not product accuracy.</text>
<text x="44" y="258" font-family="system-ui,sans-serif" font-size="14" fill="#5e6b78">Compared: parent edges, ordered roles, status placement, links, and tool-call invariants.</text></svg>"""
    Path(path).write_text(document, encoding="utf-8")
