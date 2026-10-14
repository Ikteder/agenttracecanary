# Agent trace mutations v1 dataset card

Date created: 2026-10-13

## Source and license

The ten baseline and candidate traces are authored synthetic OTLP JSON released with the project under MIT. They contain no user data, model output, third-party prompt, or production trace.

## Schema and labels

Each trace contains an authored `agenttrace.case.id` and seven spans representing a workflow, a planner agent, a nested research agent, two model-like steps, and two tools. Candidate cases mutate exactly one structural property:

1. wrong parent;
2. tool order;
3. flattened nested agent;
4. error rebound to a different tool;
5. missing parent;
6. duplicate tool-call ID;
7. child interval outside the parent;
8. typed link retargeting;
9. agent-step order;
10. tool reparenting to the workflow.

All ten preserve the aggregate multiset of semantic roles and total status counts.

## Split and leakage controls

There is no train, validation, or test split because no model is fitted. Tests assert the complete named corpus. The corpus is implementation-aligned regression evidence, so it must not be described as an independent benchmark.

## Quality controls

The generator is deterministic, committed, and rerun during verification. JSON is parsed through the production OTLP reader. Generated evidence records per-case digests, and the SVG is parsed as XML.

## Known mismatch

Fixtures are sequential and fully sampled. Production traces can be concurrent, incomplete, sampled, vendor-extended, and sensitive. The corpus does not estimate real-world frequency or false-positive rates.
