# Devlog 0002: Scan Domain Model

---

**Date:** 2026-09-29
**Status:** Complete

## Goal

Introduce the concept of a scan as one distinct Palimpsest investigation run.

## Implemented

- `Scan`
- `ScanStatus`
- timezone aware timestamps
- immutable lifecycle transitions
- completion and failure states
- validation of temporal invariants
- unit tests for valid and invalid lifecycle states

## Design Decisions

Unlike Asset identity, Scan identity represents a unique event.

A UUID was therefore appropriate for a Scan object because two investigations of the
same system are intentionally different entities.

Scan state is represented immutably. Completing or failing a Scan produces a
new representation with the same `scan_id` rather than mutating the original
object. This is to preserve data provenance. 

The domain model does not generate UUIDs or read the system clock itself.
Those operational concerns will belong to a later application layer.

## Verification

The following passed:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Next Step

Introduce the concept of an "artifact", representing the actual contexual evidence from a data Asset during a specific Scan.