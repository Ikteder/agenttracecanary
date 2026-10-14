# AgentTrace Canary 0.1 verification

Date: 2026-10-13 America/Denver

Environment: Windows, Python 3.15.0 for the final local run. Public CI is configured for Python 3.10, 3.12, and 3.14.

## Commands and results

| Check | Result |
|---|---|
| `python -m pytest` | 6 passed in 0.43 seconds |
| `python -m ruff check .` | Passed |
| `python -m ruff format --check .` | 16 files already formatted |
| `python -m compileall -q src scripts tests` | Passed |
| `python -m pip check` | No broken requirements |
| `python scripts/generate_corpus.py` | Baseline and candidate hashes unchanged |
| `python scripts/verify_evidence.py` | Mutation exit 1, safe exit 0, assertions passed |
| `python -m build` | Wheel and source distribution built successfully |
| Clean wheel install with `--no-deps` | Version 0.1.0 imported; mutation exit 1; safe exit 0; dependency check passed |
| SVG XML parse | Passed |
| README style | Zero em dash characters |

Final build artifacts:

- wheel: 14,088 bytes, SHA-256 `0D7E02FAE10236C8EFFFC44AF52FA888F8406049295EE88ECFCAD9784495D976`;
- source distribution: 17,514 bytes, SHA-256 `E6E481315BBEB4DA00D802810D4730818EC4FFE935E413FBB8201DB354832427`.

## Baseline comparison

Seed: `20261013`.

Cases: 10 authored synthetic baseline/candidate pairs.

| Method | Detected cases | Notes |
|---|---:|---|
| Aggregate-only baseline | 0 / 10 | Role multisets and total status counts remained equal |
| AgentTrace Canary | 10 / 10 | Nine canonical tree changes plus local invariant findings |

The mutation report contains 14 findings across all ten candidate cases. The safe baseline-versus-baseline control contains zero findings. The mutation JSON evidence digest is `55a30dc4a24d3c856ec12d7bbc96d1865c8181e84a6d68508782a95f2e05433e`.

## Browser and visual QA

The standalone report was served over loopback and inspected in the Codex in-app Chromium browser.

- Default viewport: 1280 by 720, four metric cards, 14 finding rows, document width 1265, table client and scroll width both 1038, no page-level horizontal overflow.
- Narrow viewport: 390 by 844, four metric cards in two columns, 14 finding rows, document width 375, table client width 334 and scroll width 650. The table scrolls internally without page-level horizontal overflow.
- The report produced zero browser console warnings or errors before navigating away.
- Visual inspection found an SVG label-to-bar collision. Bar geometry and wording were corrected, regenerated, parsed as XML, and visually rechecked. The corrected 760 by 300 SVG rendered all labels and both bars without overlap.

## Failure-path coverage

Tests cover duplicate attributes, duplicate span identities, distinct input/output enforcement, mutation exit 1, and safe exit 0. The fixture suite also exercises missing parents, duplicate tool-call IDs, interval violations, wrong parentage, link retargeting, changed order, status movement, and nested-agent flattening.

## Interpretation

This is deterministic regression evidence for an implementation-aligned synthetic corpus. It is not a production accuracy result, false-positive study, compatibility matrix, or assurance that an exported trace is complete.
