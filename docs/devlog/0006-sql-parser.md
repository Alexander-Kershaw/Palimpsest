# Devlog 0006: SQL Parser

---

**Date:** 2026-09-30  
**Status:** Complete

## Goal

Introduce the first syntax parsing capability by converting SQL source text into structured syntax trees (ASTs).

The parser layer should understand SQL structure without yet assigning specific Palimpsest dependency semantics such as `READS_FROM` or `WRITES_TO`.

## Implemented

SQLGlot was introduced as the first specialist runtime dependency.

A Palimpsest SQL parser wrapper now:

- accepts SQL source text
- optionally accepts a SQL dialect
- parses one or more SQL statements
- returns SQLGlot expression trees
- returns an empty result for empty SQL
- converts SQLGlot parser failures into a `SqlParseError`

Tests verify:

- parsing a single statement
- parsing multiple statements from one source
- structural table nodes appearing in the resulting syntax tree
- empty SQL handling
- error handling for invalid SQL

## Architectural Boundary

The parser just collects the SQL structure. It does not infer any SQL logic as of yet.

The intended processing boundary is:

```text
SQL source
    ↓
SqlParser
    ↓
SQLGlot AST
    ↓
SqlDependencyExtractor
    ↓
Observation
```

SQLGlot therefore belongs to the parsing and extraction layers and does not enter the core domain model.

## Multi Statement SQL

The parser uses SQLGlot's multi statement parsing behaviour rather than assuming that one SQL file contains exactly one SQL statement.

Conceptually:

```text
Artifact
   ↓
SQL file
   ├── statement 1 AST
   ├── statement 2 AST
   └── statement 3 AST
```

This will later allow observations to preserve statement level provenance.

## Dialects

The parser accepts an optional SQL dialect rather than assuming all SQL uses identical syntax.

Dialect selection is not currently inferred automatically.

A future application or source configuration should provide dialect information when it is known.

## Problems Encountered

None encountered.

## Verification

The following commands passed:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```


## Current State

Palimpsest can now:

```text
legacy filesystem
      ↓
discover Asset
      ↓
collect Artifact
      ↓
obtain SQL text
      ↓
parse SQL
      ↓
structured syntax tree
```

## Next Step

Introduce controlled predicate vocabulary and Observation domain model.

This gives dependency extractors a stable evidence oriented result type before SQL dependency extraction begins.

---