# ADR 0002: Artifacts Represent Collected Evidence

---

**Status:** Accepted  
**Date:** 2026-09-29

## Context

I needed Palimpsest to distinguish a conceptual system asset from the evidence collected about that asset during a particular investigative scan.

An asset may persist across many scans while its contents change over time.

For instance, a SQL script may remain the same conceptual asset even though its source code changes between two scans.

Therefore, Palimpsest requires a scan specific representation of collected evidence.

## Decision

An `Artifact` represents one collected snapshot of an `Asset` during a particular `Scan`.

Each Artifact contains:

- a unique artifact identifier
- the Scan in which the evidence was collected
- the Asset the evidence represents
- a timezone aware collection timestamp
- a content type
- the collected bytes
- a SHA256 hash derived from those bytes

Artifact identity and content identity are deliberately considered separate.

Two Artifacts may contain identical bytes and therefore share the same content hash while remaining distinct evidence records.

The raw collected payload is represented as bytes rather than decoded text. Interpretation and parsing belong exclusively to later processing stages.

The content hash is calculated by the Artifact rather than supplied by callers, preventing disagreement between the recorded content and its fingerprint.

## Alternatives

### Store content directly on Asset

Rejected because an Asset represents the long-lived conceptual system component rather than its state during one particular Scan.

### Use the content hash as Artifact identity

Rejected because identical content may legitimately be collected during multiple different Scans.

A content hash identifies bytes, not an evidence collection event.

### Store text rather than bytes

Rejected for the initial evidence model because decoding requires an interpretation of character encoding.

Raw bytes preserve the collected evidence before parsing or decoding.

### Allow callers to provide the content hash

Rejected because this could allow inconsistent Artifact state in which the supplied hash does not match the collected content.

## Consequences

Now Palimpsest can distinguish:

```text
same Asset
different Scan
same content

same Asset
different Scan
changed content
```

Artifact snapshots can later support:

- change detection
- reproducibility
- parser provenance
- repeated scan comparison
- evidence inspection

Storage strategies may eventually avoid duplicating large byte payloads, but that optimization is deliberately deferred until a real that limitation appears.

---