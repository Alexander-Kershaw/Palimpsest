# Devlog 0004: Filesystem Discovery

---

**Date:** 2026-09-29  
**Status:** Complete

## Goal

Enable Palimpsest to deterministically discover supported filesystem assets beneath an investigation root.

## Implemented

- `FilesystemCollector`
- recursive filesystem discovery
- deterministic discovery ordering
- classification of supported file types
- root relative canonical locators
- support for:
  - SQL scripts
  - Python scripts
  - CSV data files
  - Markdown documentation
  - scheduler definition files
- validation of collection roots
- unit tests using temporary synthetic filesystem structures

The Asset vocabulary was extended with `SCHEDULER_DEFINITION` to distinguish a scheduler configuration file from the scheduled jobs that may later be extracted from it.

## Design Notes

Filesystem paths are converted to root relative POSIX style locators before becoming Asset identities.

This prevents machine specific absolute paths and operating system path separators from becoming part of canonical Asset identity.

Unsupported files are currently ignored rather than represented as unknown assets.

This means:

```text
unsupported != nonexistent
```

I simply have not modelled those files during this milestone.

## Verification

The following passed:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Tests demonstrate that:

- supported assets are discovered
- unsupported extensions are ignored
- locators are relative to the investigation root
- equivalent logical files under different physical roots receive the same Asset identity
- invalid collection roots are rejected

## Lessons

Asset identity normalization belongs at the collection/source boundary rather than inside the domain model.

Deterministic ordering is valuable even when ordering has no semantic meaning because it makes tests, debugging, and future CLI output reproducible.

A scheduler definition file and the scheduled jobs described inside it are different domain concepts.

## Problems Encountered

None during this slice.

## Next Step

Extend the filesystem collector from discovery into evidence acquisition by reading the exact bytes represented by a discovered Asset and producing an Artifact tied to a Scan.