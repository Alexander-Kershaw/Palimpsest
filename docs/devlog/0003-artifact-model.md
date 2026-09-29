# Devlog 0003: Artifact Domain Model

---

**Date:** 2026-09-29  
**Status:** Complete

## Goal

Introduce Artifact as the core representation of evidence collected about an Asset during a particular investigative Scan.

## Implemented

The Artifact model now records a unique evidence record, its associated Scan and Asset, its collection timestamp, media type, raw byte content, and a deterministic SHA256 content fingerprint.

Artifact objects are immutable.

Content hashes are derived internally from the collected bytes rather than supplied by callers.

## Verification

The following commands passed:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Tests verify that:

- Artifacts preserve their Scan and Asset relationships
- SHA256 hashes are calculated from the collected bytes
- identical content produces identical content hashes without making two Artifacts identical
- changed content changes the content hash
- empty files remain valid evidence
- collection timestamps must be timezone aware
- malformed content types are rejected

## Lessons

Asset identity and Artifact identity answer different questions.

An Asset answers:

> What conceptual system component is this?

An Artifact answers:

> What evidence did Palimpsest collect about that component during this investigation?

A content hash answers a third question:

> Were these collected bytes identical?

Keeping those questions separate prevents change detection, provenance, and system identity from becoming entangled.

## Problems Encountered

No implementation problems were encountered in this slice.

## Next Step

Implement deterministic filesystem discovery to identify supported assets inside a real investigation target without yet parsing their contents.

---