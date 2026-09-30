# SQL Parsing and ASTs

---

## Why Parsing Exists

In order to effectively interpret legacy data systems, Palimpsest must understand SQL structurally rather than relying on textual
pattern matching.

The transformation is:

```text
source text
    ↓
tokens
    ↓
parser
    ↓
abstract syntax tree (AST)
    ↓
Palimpsest extractor
    ↓
observations
```

The parser is what determines the syntatic architecture. But, it does not in itself decide specific Palimpsest relationships such as `READS_FROM` or `WRITES_TO`.

## Text and Structure

The point of parsing is to extract syntatic structure as an abstract syntax tree, rather than with purely text patterns.

Considering a simple SQL query that could exist in a legacy system (such as some stored procedure):

```sql
SELECT * FROM customer;
```

The word customer is not just a substring (the purely textual context), within a parsed tree it occurs as a table expression within the SQL query FROM structure.

The distinction between textual pattern matching and AST approaches allow for reasoning around syntax while avoiding the error prone implementation of regular expressions or substring approaches.

SQLGlot is used as the SQL parser to allow a AST approach. SQLGlot is what converts SQL text into an expression tree that can be programmatically traversed. Then in Palimpsest, SQLGlot is wrapped, rather than allowing it the enter to core domain layer, it is used for parsing and extraction only.

### Parser and Extractor

The parser is responsible for determining the syntactic architecture a SQL file contains.

Meanwhile, the extractor expresses what observations can deterministically be derived from the parsed structure.

