from sqlglot import exp, parse
from sqlglot.errors import ParseError

"""
========================================================================================================

SQL PARSING

========================================================================================================

Using SQLGlot for SQL parsing.

Initially I am starting with text, this gets tokenized and produces abstract syntax trees via SQLGlot

SQLGlot considers expression hierarchy providing traversal methods such as find_all

Notes:

- using parse() instead of parse_one() so a collection of syntax trees are turned (one syntax tree
for each SQL statement present in an Artifact. So, for a SQL file Asset containing 3 SQL
statements, this general return structure is:

        Artifact
        │
        ▼
        SQL file
        │
        ├── Statement 1 AST
        ├── Statement 2 AST
        └── Statement 3 AST

- the parser accepts str, not an Artifact object. the actual Artifact content are bytes
(Artifact.content -> bytes). The SQL parser requires SQL text warranting declaring a string
The parsers responsibility is just SQL text -> syntax structure, not locating artifacts, verifying
types, decoding bytes, etc... that will be handled with another service.

========================================================================================================
"""


class SqlParseError(ValueError):
    """ValueError raised when SQL cannot be converted to AST"""


def parse_sql(sql: str, *, dialect: str | None = None) -> tuple[exp.Expression, ...]:

    try:
        expressions: list[exp.Expr | None] = parse(sql=sql, read=dialect)

    except ParseError as exc:
        raise SqlParseError(str(exc)) from exc

    return tuple(expression for expression in expressions if expression is not None)
