# ADR 0001: Stable Asset Identity

---

**Status:** Accepted  
**Date:** 2026-09-29

## Context

I found that Palimpsest must reconstruct systems across repeated scans.

Assets therefore require identities that are stable enough for observations from
different scans to refer to the same conceptual system component.

Names alone are insufficient because multiple assets may share the same local
name causing collisions.

Random identifiers are also insufficient because independently discovering the
same asset in multiple scans would produce unrelated identifiers.

Furthermore, content hashes cannot define asset identity because an asset may change contents
while remaining the same conceptual system component.

## Decision

The initial Palimpsest asset identity consists of:

1. asset kind
2. source namespace
3. locator within that namespace

Conceptually:

```text
AssetIdentity = (kind, source_namespace, locator)
```

For example:

```text
(TABLE, database:merewell, warehouse.customer)

(SQL_SCRIPT, filesystem:merewell, sql/10_merge_customers.sql)
```

Note that the scan identifier is intentionally excluded from the asset identity.

Moreover, source specific normalization is also excluded from the domain model. The collectors and parsers are intented to be responsible for producing any canonical source coordinate before constructing the AssetIdentity object.

I have considered the edge case concerning renaming of locators within the source namespace. I have initially not implemented any automatic rename detection. Therefore a locator change creates a different identity unless later evidence supports explicity reconciliation, and the renamed asset superseds the previous version.

## Alternative Considerations

**Local name only** was rejected because names of entities such as `customer` are not globally unique and therefore does not make viable identifiers.

**Random UUID** rejected as the canonical entity because repeated discovery would generate a new identifier for the same conceptual asset in this case.

**content hash** also rejected because content represents a particular artifact state, rather than the overarching conceptual asset. For instance, two different assets may contain identical content, and one of these assets may change between scans.

**Absolute filesystem path** rejected as the core identity since absolute paths are environment dependent and would make identities unstable across different machines

## Consequences

Overall, Asset identity is deterministic when the same canonical coordinates are provided. Collectors are to establish stable source namespaces and canonical locators.

Renames are initially going to represented as distinct assets.

Future reconciliation mechanisms may be used to link or merge identities when additional evidence supports these operations.

---