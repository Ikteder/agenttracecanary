# Decision: compare normalized causal shape

Date: 2026-10-13

## Context

Raw trace IDs, span IDs, and timestamps normally differ across repeated runs. A text or JSON diff therefore produces noise. Aggregate counts remove that noise but also erase parentage, order, status placement, and relationship links.

## Decision

Build a deterministic tree serialization from semantic roles and parent edges. Order siblings by relative start time, include normalized success or error status, and map optional link targets to their semantic roles. Exclude IDs, absolute time values, and raw attributes from the signature. Run local structural invariants separately so duplicate call IDs and interval violations can fail even when the tree signature is unchanged.

## Consequences

The comparison is useful for deterministic evaluation fixtures and privacy-preserving reports. It is intentionally sensitive to sibling order and therefore can flag legitimate scheduling changes in concurrent production traces. Future versions need an explicit partial-order policy before claiming support for nondeterministic concurrency.
