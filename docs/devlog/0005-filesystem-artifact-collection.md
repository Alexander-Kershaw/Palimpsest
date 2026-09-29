# Devlog 0005: Filesystem Artifact Collection

---

**Date:** 2026-09-29  
**Status:** Complete

## Goal

Extend the filesystem discovery into evidence acquisition.

The objective was to allow Palimpsest to take a discovered filesystem `Asset`, read the exact bytes represented by that asset, and produce an `Artifact` tied to a specific `Scan`.

This establishes the first complete deterministic evidence path:

```text
filesystem file
      ↓
    Asset
      ↓
exact collected bytes
      ↓
   Artifact
```

## Implemented

The filesystem collector now supports:

- collecting exact file bytes for a discovered Asset
- creating an Artifact from those bytes
- preserving the associated Asset
- preserving the Scan identifier
- preserving the Artifact identifier
- preserving the collection timestamp
- assigning deterministic content types
- calculating the Artifact content hash through the Artifact domain model
- validating that the Asset belongs to the expected source namespace
- validating that the Asset kind matches the actual filesystem file type
- validating that the target still exists
- validating that the target is a file
- preventing Asset locators from resolving outside the collection root

Shared filesystem root validation was also extracted into a reusable helper so discovery and acquisition rely on the same root invariants.

## Evidence Flow

The implemented flow is now:

```text
Collection root
      │
      ▼
FilesystemCollector
      │
      ├── discover
      │      ↓
      │    Asset
      │
      └── collect
             ↓
          Artifact
             │
        ┌────┼───────────────┐
        ▼    ▼               ▼
      Asset Scan ID      exact bytes
                             │
                             ▼
                         SHA-256
```

The collector does not parse or interpret the file contents.

Its responsibility remains evidence acquisition.

## Design Decisions

### Operational metadata is supplied by the caller

The collector does not generate:

- Scan identifiers
- Artifact identifiers
- collection timestamps

These values are supplied explicitly.

This keeps filesystem acquisition deterministic and avoids hiding calls to system clocks or random UUID generation inside the collector.

A future application service can coordinate those operational concerns.

### Raw bytes are preserved

Artifact content continues to be collected as raw `bytes`.

The collector does not decode SQL, Python, CSV, Markdown, or scheduler definitions into text.

Decoding and syntax interpretation belong to later parsing stages.

This preserves the separation:

```text
collector
    ↓
raw evidence

parser
    ↓
interpreted syntax
```

### Content types are explicit and deterministic

Supported filesystem types are mapped directly to known content types rather than relying on platform dependent MIME detection.

Examples include:

```text
.sql         → text/x-sql
.py          → text/x-python
.csv         → text/csv
.md          → text/markdown
crontab.txt  → text/plain
```

This keeps behaviour reproducible across environments.

### Asset and filesystem state must agree

Before collecting evidence, the collector verifies that the supplied Asset kind agrees with the actual filesystem classification.

For example, an Asset claiming:

```text
kind = SQL_SCRIPT
locator = ingest.py
```

is rejected.

It should not create evidence containing an internal contradiction between the Asset description and the observed file.

### Source namespaces are enforced

An Asset discovered under one logical source namespace cannot silently be collected as though it belonged to another.

This protects provenance boundaries between investigated systems.

### Asset locators cannot escape the collection root

Asset locators are resolved relative to the configured collection root.

The resolved path must remain within that root.

A locator such as:

```text
../outside.sql
```

is rejected.

This prevents malformed or unsafe Asset locators from causing Palimpsest to collect evidence outside the intended investigation target.

## Verification

The following commands passed:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The tests verify that:

- exact file bytes are preserved
- the resulting Artifact hash matches the collected content
- Artifact provenance is preserved
- empty files remain valid evidence
- recollecting changed content produces a different content hash while preserving the same Asset identity
- mismatched source namespaces are rejected
- mismatched Asset kinds are rejected
- Asset locators cannot escape the collection root

## Important Behaviour Demonstrated

A file can remain the same conceptual Asset while its collected evidence changes:

```text
same Asset
   │
   ├── Scan A
   │      ↓
   │   Artifact A
   │   hash = X
   │
   └── Scan B
          ↓
       Artifact B
       hash = Y
```

This proves that:

```text
Asset identity
```

and:

```text
Artifact content state
```

remain correctly separated.

## Lessons

The domain decisions made earlier are now beginning to compose into a more cohesive working evidence system.

Stable Asset identity allows the same conceptual component to survive changes in its contents.

Artifact identity preserves individual evidence collection events.

Content hashes describe the collected byte state without defining either Asset or Artifact identity.

Source normalization and filesystem safety checks belong at the collection boundary rather than inside the core domain model.

The collector should remain deliberately narrow:

> acquire evidence, preserve provenance, and avoid interpreting meaning.

## Problems Encountered

No implementation problems were encountered during this slice.

## Current State

Palimpsest can now:

1. discover supported filesystem assets
2. assign stable Asset identities
3. collect exact file contents
4. associate collected evidence with a Scan
5. preserve Artifact provenance
6. fingerprint collected content deterministically

The first evidence path is therefore operational:

```text
legacy filesystem
      ↓
discovery
      ↓
Asset
      ↓
collection
      ↓
Artifact
```

## Next Step

Introduce the SQL parsing layer.

The next slice will add SQLGlot as the first specialist runtime dependency and establish the boundary:

```text
Artifact bytes
      ↓
decoded SQL text
      ↓
SQL parser
      ↓
syntax tree
```

Parsing will remain separate from dependency extraction.

---