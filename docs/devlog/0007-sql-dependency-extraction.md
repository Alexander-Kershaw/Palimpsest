# Devlog 0007: Initial SQL Dependency Extraction

---

**Date:** 2026-09-30  
**Status:** Complete

## Goal

Introduce the first deterministic static analysis capability by converting parsed SQL syntax trees into evidence table dependency Observations.

## Implemented

The initial `SqlDependencyExtractor` supports:

- `SELECT ... FROM` read dependencies
- joined table read dependencies
- `INSERT ... SELECT` read and write dependencies
- schema qualified table names
- CTE aware dependency discovery
- multiple SQL statements
- statement level provenance
- deduplication of repeated table references
- validation that extraction is performed against a SQL Script Asset
- explicit relation namespaces supplied by investigation context

The extractor produces `Observation` objects using the controlled predicates:

```text
READS_FROM
WRITES_TO
```

## Processing Flow

The deterministic analysis path is:

```text
SQL Artifact
     ↓
decoded SQL text
     ↓
SQL parser
     ↓
SQLGlot syntax tree
     ↓
SqlDependencyExtractor
     ↓
Observation
```

The parser determines SQL structure.

The extractor interprets that structure in terms of Palimpsest's relationship vocabulary.

## CTE Handling

Raw traversal of every SQL `Table` node is insufficient because a Common Table Expression (CTE) can appear syntactically like a table reference without representing a physical external relation.

For example:

```sql
WITH active_customer AS (
    SELECT *
    FROM customer
)
SELECT *
FROM active_customer;
```

The correct external dependency is:

```text
customer
```

rather than:

```text
customer
active_customer
```

The extractor therefore uses SQLGlot's scope aware table discovery rather than treating every table shaped syntax node as a physical dependency.

## Relation Identity

SQL syntax can establish relation names such as:

```text
customer
warehouse.customer
merewell.warehouse.customer
```

but it cannot necessarily establish the logical Palimpsest source namespace in which those relations exist.

The relation namespace is therefore supplied explicitly to the extractor.

This preserves the distinction between:

```text
syntax derived evidence
```

and:

```text
investigation/environment context
```

## Deterministic Output

Repeated references to the same physical table within one statement produce one table level Observation.

For example:

```sql
SELECT *
FROM customer AS child
JOIN customer AS parent
    ON child.parent_id = parent.customer_id;
```

produces one table level:

```text
READS_FROM customer
```

Observation.

Palimpsest is currently reconstructing table level dependencies rather than alias level access paths.

## Provenance

Every extracted relationship preserves:

- the SQL Script Asset
- the relationship predicate
- the referenced relation Asset
- the originating Artifact
- the extractor responsible
- the statement location

These serve as evidence coordinates.

## Verification

The following passed:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Tests demonstrate:

- single table reads
- joined reads
- schema qualified relations
- read and write extraction from `INSERT ... SELECT`
- CTE filtering
- statement level provenance
- repeated reference deduplication
- statements with no table dependency
- rejection of non-SQL subjects
- preservation of distinct read and write relationships against the same table

## Current State

Palimpsest can now execute the following conceptual pipeline:

```text
legacy filesystem
      ↓
Asset discovery
      ↓
Artifact collection
      ↓
SQL parsing
      ↓
AST analysis
      ↓
Observation
```

This represents a complete evidence supported static analysis path in the project.

## Next Step

Extend SQL dependency extraction one statement type at a time.

The next semantic cases are:

```text
UPDATE
DELETE
CREATE TABLE
CREATE TABLE AS SELECT
```

These operations require explicit reasoning about whether the target relation is read, written, or both.

---