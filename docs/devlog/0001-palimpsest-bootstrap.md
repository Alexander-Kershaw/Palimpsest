# Devlog 0001: Palimpsest Bootstrap

---

**Date:** 2026-09-29  
**Status:** Complete

## Goal

Establish an initial minimal, reproducible Python development environment for Palimpsest before implementing any domain behaviour.

## Work

The bootstrap establishes:

- Python 3.12;
- `uv` project and dependency management;
- a packaged `src/` layout;
- pytest;
- Ruff;
- the initial testing structure;
- the initial documentation structure;
- Git based incremental development.

## Design Notes

Palimpsest has been initialized as a Python library rather than a CLI dominant application.

This reflects the intended architecture in which application behaviour is reusable independently of its interfaces. Future interfaces such as CLI, REST, and MCP will call the same application services rather than contain Palimpsest's core behaviour themselves.

No parser, database, graph technology, or AI dependency has been introduced during bootstrap, these are intended to come later once a solid foundation is found.

## Verification

Bootstrap is complete when all of the following succeed:

```bash
uv run python --version
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The Python version should be Python 3.12.x.

The test suite should pass.

Ruff should report no linting or formatting failures.

## Lessons

- Palimpsest begins as a Python library rather than an interface first application.
- The `src/` layout ensures the package is tested as an installed distribution.
- Asset identity and artifact state are different concepts.
- Stable asset identity is based on meaningful source coordinates rather than
  random UUIDs or content hashes.
- Source specific normalization belongs outside the domain model.
- Immutable value objects are useful for concepts whose meaning is entirely determined by their values.

## Problems Encountered

None during the initial bootstrap and Asset identity implementation.

## Next Step

Introduce the `Scan` domain model so I can represent individual
investigation runs independently of the assets being investigated.