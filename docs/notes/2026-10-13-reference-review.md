# Reference review and impact gate

Date accessed: 2026-10-13 America/Denver

Selection: seed `20261013`; Python `random.Random` mode roll `0.6103322316492847` selected the 35% distinct project or extension branch. The previous three completed scheduled focuses were 5 on October 8, 4 on October 5, and 3 on October 1. Eligible areas were `[1, 2, 6, 7]`; seeded index `1` selected focus 2, evaluation, observability, debugging, regression detection, and reliability. The unfinished October 12 `coldmemory` draft was preserved and was not treated as a completed run. No redraw was used.

## Current primary-source comparison

| Reference | User and capability | Current evidence | Evaluation and integration surface | License and contribution rules | Gap relevant to this project |
|---|---|---|---|---|---|
| [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai) at `4e8a281`, accessed October 13 | Instrumentation and backend authors standardizing agent, workflow, inference, evaluation, and tool telemetry | Repository head was updated October 13. Agent and tool spans remain development status. [Issue 3575](https://github.com/open-telemetry/semantic-conventions/issues/3575) states that grouping is otherwise inferred from order and proposes generic groups plus typed span links. | YAML semantic model, generated documentation, reference scenarios, OTLP attributes such as `gen_ai.operation.name` and `gen_ai.tool.call.id`. | Apache-2.0. Contributions require the OpenTelemetry prerequisites and CLA, generated docs, policy checks, and reference scenarios. | Provides the vocabulary, but its relationship design is still active and it does not ship a baseline-versus-candidate structural regression auditor. |
| [OpenInference](https://github.com/Arize-ai/openinference) at `100ce01`, accessed October 13 | Framework and observability authors using OpenTelemetry instrumentation across Python, JavaScript, Java, and Go | Repository was active on October 13/14 UTC, with current package releases on October 10. [Issue 3164](https://github.com/Arize-ai/openinference/issues/3164) recorded doubled trace token totals when parent and child usage were both aggregated. | Defines Agent, Tool, LLM, Evaluator, and other span kinds, tool-call message identifiers, many framework instrumentors, and OTLP-compatible export. | Apache-2.0 plus CLA. The contribution guide says feature contributions are not actively accepted, nontrivial work needs explicit maintainer alignment, and span changes need trace evidence. | Rich instrumentation and semantics do not by themselves prove that causal placement stayed stable across a code change. Its contribution policy favors an independent compatible tool. |
| [Langfuse](https://github.com/langfuse/langfuse) at `df7df89`, release `v4.58.0` | Teams tracing, evaluating, and comparing LLM and agent applications through a hosted or self-hosted platform | Repository and release were active October 13. [Issue 9293](https://github.com/langfuse/langfuse/issues/9293) reports a LlamaIndex tool function appearing outside the expected agent-loop position even after the tool became visible in the same trace. | OpenTelemetry ingestion, SDK instrumentation, trace UI, evaluations, experiments, and dashboards. | Core is MIT; listed enterprise directories use separate terms. Significant changes should start with an issue, and PRs require lint, type, unused-code, test, and visual checks. | Shows the practical failure: trace completeness can coexist with wrong causal position. The full platform is not a suitable home for a small provider-neutral offline corpus tool. |
| [Google, Data Validation for Machine Learning](https://research.google/pubs/data-validation-for-machine-learning/) found through [Applied ML](https://github.com/eugeneyan/applied-ml) | Production ML teams detecting skew and anomalies across pipeline boundaries | The 2019 paper is the original linked source. It frames validation as explicit constraints and comparisons rather than successful pipeline completion. | Production data validation concepts and research evidence, not an agent tracing library. | Paper/source attribution only; no code was adapted. | The transferable pattern is comparing invariants across two boundaries. Company scale and results are not claimed or reproduced. |

## Relevant commercial behavior

Langfuse offers hosted observability as well as open-source deployment. Its trace and experiment interfaces are valuable for inspection and score comparison. AgentTrace Canary is not a competing platform. It processes two exported files offline and emits a review artifact that can be attached to any CI system.

## Source and issue inspection

- OpenTelemetry `model/gen-ai/spans.yaml` currently recommends `invoke_agent`, `invoke_workflow`, and `execute_tool`; `gen_ai.tool.call.id` is recommended when available.
- OpenInference `spec/traces.md` defines parent-linked spans and AI span kinds, and `spec/llm_spans.md` defines tool result linkage through `message.tool_call_id`.
- Langfuse issue 9293 remained open in the inspected page and documents wrong placement after context propagation improvements.
- Local searches found no structural OTLP diff in `fallbacklens`, `resumeprobe`, or `llm-agent-workflows`. FallbackLens audits routing policy and observed deployment bindings, not general agent causal structure.

## Rejected candidates

- A new tracing dashboard was rejected as a clone of mature systems.
- A semantic-convention PR was rejected because the relationship design is still being discussed and no maintainer invited a patch.
- A generic trace JSON diff was rejected because IDs and timestamps would create noise without testing an agent-specific contract.
- A tool-call payload evaluator was deferred because it would require sensitive-content handling and model-dependent semantics.

## Chosen gap and impact gate

- Real user and problem: agent maintainers need CI evidence when instrumentation or orchestration changes preserve totals but corrupt causal debugging structure.
- Evidence: one active standards proposal and one concrete integration issue show that grouping and placement are unresolved in practice.
- Original value: normalization across dynamic IDs and offline agent-specific invariants improve reliability, interoperability, privacy, and reproducibility.
- Measurable: detect all ten authored structural mutations while the declared aggregate-only baseline detects none; accept equivalent traces with new IDs and shifted clocks.
- Finishable: one OTLP reader, one canonicalizer, one invariant checker, ten fixtures, and three report formats.
- Maintainable: Python standard library only at runtime, typed immutable records, one explicit case attribute, versioned evidence.
- License: independent MIT. No upstream code, fixtures, model outputs, or proprietary traces are copied.

## Claim boundary

The evaluation proves behavior on the included synthetic mutation corpus. It does not measure production defect prevalence, standards compliance, observability product quality, trace completeness, or semantic correctness.
