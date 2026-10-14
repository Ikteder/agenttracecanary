# AgentTrace Canary 0.1 specification

Date: 2026-10-13 America/Denver

Status: approved for completion by the designated automation run. The gap and acceptance boundary were fixed before the implementation slice was completed. An initial local parser prototype preceded this durable file; no benchmark or publication decision was made before the specification was saved.

## User and problem

Agent platform maintainers compare evaluation scores, counts, latency, and token totals when changing instrumentation or orchestration code. Those aggregates can remain equal when a tool span moves under the wrong agent, a nested agent is flattened, an error is attached to the wrong step, or a tool execution loses its parent. The trace still looks complete, but causal debugging evidence has regressed.

## Evidence and selected gap

OpenTelemetry GenAI conventions define development-stage agent, workflow, and tool spans. OpenTelemetry issue 3575 says current backends must guess causal grouping when explicit relationships are absent. Langfuse issue 9293 reports a real tool span captured in the wrong position after instrumentation. OpenInference defines interoperable AI span kinds and tool-call identifiers, while issue 3164 shows aggregate interpretation can double-count nested usage.

Existing systems collect and visualize traces. This slice audits a narrower boundary: whether the causal shape of a known case changed between two OTLP JSON exports.

## Scope

1. Parse standard OTLP JSON `resourceSpans`, attributes, status, and links without a runtime dependency.
2. Pair baseline and candidate traces using an explicit authored `agenttrace.case.id` attribute.
3. Canonicalize each trace while ignoring trace IDs, span IDs, and absolute timestamp offsets.
4. Compare ordered roles, parentage, status placement, and optional typed links.
5. Check local invariants for one root, valid parents, acyclic ancestry, parent time containment, tool ancestry, and duplicate tool-call IDs.
6. Emit deterministic JSON plus standalone HTML and SVG evidence.
7. Evaluate a ten-case synthetic structural mutation corpus against a documented aggregate-only baseline.

## Acceptance criteria

- A safe candidate with different trace IDs, span IDs, and absolute times produces `match` and exit code 0.
- Every authored mutation case produces at least one finding and exit code 1.
- The aggregate-only baseline sees zero changed cases because operation-role counts and status totals are preserved.
- Malformed attributes, duplicate span identities, missing case identity, and input/output path collisions fail explicitly with exit code 2.
- Unit, CLI, lint, format, build, clean-wheel, evidence regeneration, SVG XML, README style, and browser layout checks pass.

## Comparison baseline

The baseline compares only the multiset of semantic roles plus total status counts. It approximates a dashboard that shows the same number of agents, tools, model spans, successes, and failures without checking where they occurred. The proposed method adds causal shape and local invariants. This is an intentionally weak but explicit baseline, not a claim about any named product.

## Risks and controls

- Instrumentation conventions remain in development. The parser uses published OTLP fields and a small set of GenAI attributes, then records unsupported boundaries.
- Relative start order can change under legitimate concurrency. Version 0.1 is intended for deterministic evaluation fixtures, not free-running production traces.
- A trace can omit unsampled work. The tool never claims coverage or execution completeness.
- Typed relationship links are experimental. They are compared only when already present.
- Trace content can be sensitive. Processing is local and reports omit raw span attributes.

## Publication plan

Publish as an independent MIT project named `agenttracecanary`. Do not copy upstream source or claim official OpenTelemetry, OpenInference, or Langfuse affiliation. No upstream pull request is appropriate because this is a cross-system offline evaluation tool and OpenInference currently discourages unsolicited feature work.

## Non-goals

Version 0.1 does not collect traces, evaluate answer quality, reconstruct missing spans, prove tool execution, compare payload contents, assign blame, certify standards compliance, or replace a tracing backend.
