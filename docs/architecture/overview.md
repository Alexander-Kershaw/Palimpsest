# Palimpsest Architecture Overview

## Purpose

Palimpsest is designed as an evidence enforced data archaeology and context engineering system for legacy data platforms.

Its purpose is to reconstruct what an unfamiliar system contains, how its components relate, what evidence supports those conclusions, and what remains uncertain.

Palimpsest does not initially modernize or replace the systems it investigates. Its intended as an intermediate supportive layer between ambiguous legacy systems, and AI agents supporting the migration and modernization of said legacy system.

## Architectural Principle

The foundational engineering rule being enforced throughout development is:

> Deterministic where realistically possible, probabilistic where its necessary, provenance is required everywhere.

Facts that can be established through deterministic techniques such as parsing, metadata inspection, or runtime evidence should not be delegated to probabilistic AI systems.

AI capabilities will eventually operate on top of collected and structured evidence rather than replace that evidence.

## Epistemic Model

Palimpsest distinguishes between several distinct layers of knowledge:

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
  ↓
System Model
  ↓
Graph Projection
  ↓
Queries / Context
```

These layers are not collapsed merely for implementation convenience. 

An observation records what an analyser detected.

A claim represents a normalized proposition supported by evidence.

A graph relationship is a projection of accepted claims for efficient traversal and analysis.

The graph itself is therefore not Palimpsest's source of truth.

## Initial Architectural Style

Palimpsest will have its genesis as a modular monolith.

The initial high level modules are:

```text
domain
collection
parsing
extraction
claims
graph
storage
application
interfaces
```

Responsibilities remain separated:

- collectors acquire evidence
- parsers turn syntax into structural representations
- extractors generate Palimpsest observations
- claim logic normalizes and reconciles propositions
- graph components project and traverse relationships
- storage persists evidence oriented states
- application services coordinate use cases
- interfaces expose application services to users and external systems

## Dependency Direction

The domain layer contains Pamimpsest's core concepts and should remain independent of infrastructure technologies.

In particular, the domain model should not depend directly on technologies such as:

- SQLGlot
- NetworkX
- SQLite
- Typer
- FastAPI
- LLM provider SDKs

Infrastructure implements capabilities required by the core rather than define the core model itself.

## Milestone 1

Milestone 1 will demonstrate that Palimpsest can analyse a directory containing:

- SQL
- Python data pipeline code
- CSV inputs
- simple scheduler definitions

and reconstruct evidence backed table level dependencies with provenance.

Milestone 1 intentionally excludes:

- column level lineage
- LLM reasoning
- semantic business rule extraction
- contradiction detection
- runtime reconciliation
- Neo4j
- PostgreSQL
- MCP
- REST APIs
- frontend development
- autonomous agents

## Current State

Palimpsest is currently in repository bootstrap and domain model design.

The next architectural problem is stable asset identity.

---