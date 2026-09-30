# Devlog 0008: SQL DML and DDL Dependency Semantics

---

**Date:** 2026-09-30  
**Status:** Complete

## Goal

To extend SQL dependency extraction beyond the basic `SELECT` and `INSERT ... SELECT` statements.

The objective was to add deterministic table level dependency semantics for CRUD statements such as:

```text
UPDATE
DELETE
CREATE TABLE
CREATE TABLE AS SELECT
```

while preserving the existing handling of CTEs, qualification, provenance, and deterministic observations.

## Implemented

The SQL dependency extractor now supports the following semantics:

| Statement | Read dependencies | Write dependencies |
|---|---|---|
| `UPDATE target ...` | target | target |
| `UPDATE target ... FROM source` | target, source | target |
| `DELETE FROM target ...` | target | target |
| `DELETE FROM target USING source ...` | target, source | target |
| `CREATE TABLE target (...)` | none | target |
| `CREATE TABLE target AS SELECT ... FROM source` | source | target |

CTEs continue to be treated as query local relations rather than physical external dependencies.

For example:

```sql
CREATE TABLE customer_archive AS
WITH eligible AS (
    SELECT *
    FROM customer
)
SELECT *
FROM eligible;
```

produces:

```text
READS_FROM customer
WRITES_TO customer_archive
```

and does not create a physical dependency on `eligible`.

## Statement Specific Semantics

Earlier extraction relied heavily on generic table discovery.

This slice introduced a stronger model:

```text
statement type
      ↓
semantic rule
      ↓
relevant AST regions
      ↓
dependency observations
```

The extractor now distinguishes between statement targets and source relations rather than assuming all table shaped syntax has equivalent meaning.

## UPDATE Semantics

An `UPDATE` is represented as both reading and writing its target.

For example:

```sql
UPDATE customer
SET status = 'INACTIVE'
WHERE last_order_date < CURRENT_DATE;
```

produces:

```text
READS_FROM customer
WRITES_TO customer
```

This reflects the fact that existing rows are inspected in order to determine and perform the update.

Additional `FROM` relations are represented as read dependencies.

## DELETE Semantics

A `DELETE` similarly reads and writes its target.

For example:

```sql
DELETE FROM customer
WHERE is_duplicate = TRUE;
```

produces:

```text
READS_FROM customer
WRITES_TO customer
```

Additional relations supplied through PostgreSQL `USING` clauses are represented as read dependencies.

## CREATE TABLE Semantics

A plain table creation:

```sql
CREATE TABLE customer_archive (
    customer_id INTEGER
);
```

produces only:

```text
WRITES_TO customer_archive
```

because no source relation is read.

A `CREATE TABLE AS SELECT` statement contains both a write target and query sources.

For example:

```sql
CREATE TABLE customer_archive AS
SELECT *
FROM customer;
```

produces:

```text
READS_FROM customer
WRITES_TO customer_archive
```

## Problem Encountered

The initial implementation assumed that generic scope aware table discovery would identify the additional source relations used by:

```sql
UPDATE ... FROM ...
```

and:

```sql
DELETE ... USING ...
```

The tests demonstrated that this assumption did not hold for the installed SQLGlot behaviour.

The resulting failures were:

```text
UPDATE ... FROM staging
```

missing:

```text
READS_FROM staging
```

and:

```text
DELETE ... USING duplicate_customer
```

missing:

```text
READS_FROM duplicate_customer
```

The write targets and target table reads were correctly detected.

## Investigation

Inspection of the parsed AST showed that these PostgreSQL constructs store their additional source relations in statement specific fields.

Conceptually:

```text
Update
├── this       → target
├── from_      → additional source
└── where      → predicate
```

and:

```text
Delete
├── this       → target
├── using      → additional sources
└── where      → predicate
```

The extractor was therefore changed to interpret these fields explicitly rather than relying entirely on generic table traversal.

## Resolution

Dedicated handling was added for:

```text
Update.args["from_"]
Delete.args["using"]
```

Physical tables are extracted from these clauses while filtering query local CTE aliases.

The existing tests were retained unchanged because their expected semantics were correct.

After the fix, the entire test suite passed.

## Verification

The following commands passed:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The project test suite now verifies SQL dependency behaviour across basic queries, joins, inserts, updates, deletes, table creation, CTAS, CTEs, qualification, multiple statements, and provenance.


## Current State

Palimpsest can deterministically reconstruct table level read and write dependencies for a meaningful subset of SQL pipeline behaviour.

The evidence flow is now:

```text
SQL source
    ↓
parser
    ↓
AST
    ↓
statement-specific static analysis
    ↓
Observation
```

## Next Step

Move upward in the epistemic model from Observations to Claims.

Observations intend to represent what individual analysers detected from specific evidence.

Claims will represent normalized propositions about the investigated system.

Multiple Observations may support the same Claim while remaining individually traceable to their originating evidence.

---