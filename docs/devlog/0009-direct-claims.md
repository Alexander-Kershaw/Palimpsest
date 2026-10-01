# Devlog 0009: Direct Claims

---

**Date:** 2026-10-01  
**Status:** Complete

## Goal

Introduce a claim layer where bservations represent what individual analysers directly detected from specific evidence.

Claims represent normalized propositions about the investigated system such as a SQL script in this case.

The objective of this section of the project was to transform evidence specific Observations into stable Direct Claims while preserving every supporting Observation.

## Implemented

- `Claim` as an immutable normalized proposition
- `DirectClaim` as a Claim supported by one or more Observations
- validation that supporting Observations actually match the Claim
- aggregation of multiple Observations supporting the same proposition
- deduplication of repeated identical Observations
- deterministic ordering of generated Direct Claims

## Epistemic Model

Palimpsest now distinguishes:

```text
Observation:
    This analyser detected this relationship
    from this Artifact at this location.

Claim:
    holds this normalized proposition
    about the investigated system.
```

For example:

```text
Observation A ─────┐
                   │
Observation B ─────┼──► Claim:
                   │
Observation C ─────┘    load_customer.sql
                        READS_FROM
                        stg_customer
```

The supporting evidence remains individually traceable.

## Claim Identity

A Claim is determined by:

```text
subject
predicate
object
```

Supporting evidence is deliberately excluded from Claim identity.

This means that adding another supporting Observation strengthens the evidence available for a proposition without changing which proposition the Claim represents.

## Evidence Support

A `DirectClaim` requires at least one supporting Observation.

Every supporting Observation must match the Claim:

```text
subject
predicate
object
```

An unrelated Observation cannot be attached to a Claim.

## Deduplication

Supporting Observations are stored as a `frozenset` making Observations immutable, and unique evidence of a syntatic relationship.

Running the same deterministic extractor repeatedly against the same Artifact does not create artificial additional evidence.

For example:

```text
Observation A
Observation A
Observation A
```

still provides one unique support item.

However:

```text
Observation from Artifact A
Observation from Artifact B
```

can provide two distinct pieces of evidence for the same Claim depending on the Artifact contents.

## Confidence

No numeric confidence score has been introduced at this stage.

The issue is with meaning. For example, a value such as:

```text
confidence = 0.87
```

would have no rigorous meaning without defining what probability or reliability model it actually represents.

Instead I currently preserves concrete evidence instead:

```text
Claim
    supported by
        Observation A
        Observation B
```

A future confidence model may consider evidence independence, runtime confirmation, extractor reliability, conflicting evidence, and human attestation, but this current structure is sufficient for now.

## Verification

The complete test suite passed together with:

```bash
uv run ruff check .
uv run ruff format --check .
```

Tests verify Claim construction, evidence validation, observation aggregation, proposition separation, duplicate evidence handling, and empty input behaviour.

## Current State

Palimpsest has now implemented the foundational chain:

```text
Source
  ↓
Asset
  ↓
Artifact
  ↓
Observation
  ↓
Claim
```

The system can discover evidence, collect it, parse SQL, extract deterministic dependency Observations, and normalize those Observations into directly supported Claims.

## Next Step

Introduce SQLite persistence so evidence is preserved.

The first persistence slice will establish the database schema, referential integrity rules, canonical Asset uniqueness, database connection handling, and tests.

Repository implementations will then map domain objects onto that storage model.

---