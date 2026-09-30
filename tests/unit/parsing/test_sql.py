import pytest
from sqlglot import exp

from palimpsest.parsing.sql import SqlParseError, parse_sql


def test_parses_single_statement() -> None:
    statements = parse_sql("SELECT customer_id FROM customer")

    assert len(statements) == 1
    assert isinstance(statements[0], exp.Select)


def test_parses_multiple_statements() -> None:
    sql = """
    SELECT * FROM customer;
    SELECT * FROM meter;
    """

    statements = parse_sql(sql)

    assert len(statements) == 2
    assert all(isinstance(statement, exp.Select) for statement in statements)


def test_parse_tree_contains_structural_nodes() -> None:
    statements = parse_sql(
        """
        SELECT c.customer_id
        FROM customer AS c
        JOIN meter AS m
            ON c.customer_id = m.customer_id
        """
    )

    statement = statements[0]

    tables = {table.name for table in statement.find_all(exp.Table)}

    assert tables == {
        "customer",
        "meter",
    }


def test_empty_sql_produces_no_statements() -> None:
    statements = parse_sql("")

    assert statements == ()


def test_invalid_sql_raises_palimpsest_error() -> None:
    sql = "SELECT foo FROM (SELECT baz FROM t"

    with pytest.raises(expected_exception=SqlParseError):
        parse_sql(sql)
