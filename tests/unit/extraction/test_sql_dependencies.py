from uuid import UUID

import pytest
from sqlglot.expressions.core import Expression

from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind
from palimpsest.domain.observation import Observation
from palimpsest.domain.predicates import Predicate
from palimpsest.extraction.sql_dependencies import (
    SqlDependencyExtractor,
)
from palimpsest.parsing.sql import parse_sql

ARTIFACT_ID = UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

SCRIPT = Asset(
    identity=AssetIdentity(
        kind=AssetKind.SQL_SCRIPT,
        source_namespace="filesystem:merewell",
        locator="sql/example.sql",
    )
)

RELATION_NAMESPACE = "database:merewell"


def test_select_extracts_read_dependency() -> None:
    statements: tuple[Expression, ...] = parse_sql(sql="SELECT * FROM customer")

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    assert len(observations) == 1

    observation: Observation = observations[0]

    assert observation.predicate is Predicate.READS_FROM
    assert observation.object.identity.locator == "customer"
    assert observation.location == "statement 1"


def test_join_extracts_all_physical_read_dependencies() -> None:
    statements: tuple[Expression, ...] = parse_sql(
        """
        SELECT *
        FROM customer AS c
        JOIN meter AS m
            ON c.customer_id = m.customer_id
        """
    )

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    reads: set[str] = {
        observation.object.identity.locator
        for observation in observations
        if observation.predicate is Predicate.READS_FROM
    }

    assert reads == {
        "customer",
        "meter",
    }


def test_schema_qualified_table_preserves_qualification() -> None:
    statements: tuple[Expression, ...] = parse_sql(
        sql="SELECT * FROM warehouse.customer"
    )

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    assert observations[0].object.identity.locator == ("warehouse.customer")


def test_insert_select_extracts_read_and_write() -> None:
    statements: tuple[Expression, ...] = parse_sql(
        """
        INSERT INTO customer
        SELECT *
        FROM stg_customer
        """
    )

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    relationships: set[tuple[Predicate, str]] = {
        (
            observation.predicate,
            observation.object.identity.locator,
        )
        for observation in observations
    }

    assert relationships == {
        (
            Predicate.READS_FROM,
            "stg_customer",
        ),
        (
            Predicate.WRITES_TO,
            "customer",
        ),
    }


def test_cte_name_is_not_treated_as_physical_table() -> None:
    statements: tuple[Expression, ...] = parse_sql(
        sql="""
        WITH active_customer AS (
            SELECT *
            FROM customer
            WHERE is_active = TRUE
        )
        SELECT *
        FROM active_customer
        """
    )

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    reads: set[str] = {
        observation.object.identity.locator
        for observation in observations
        if observation.predicate is Predicate.READS_FROM
    }

    assert reads == {"customer"}


def test_multiple_statements_preserve_statement_location() -> None:
    statements: tuple[Expression, ...] = parse_sql(
        sql="""
        SELECT * FROM customer;
        SELECT * FROM meter;
        """
    )

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    locations: set[tuple[str, str | None]] = {
        (
            observation.object.identity.locator,
            observation.location,
        )
        for observation in observations
    }

    assert locations == {
        ("customer", "statement 1"),
        ("meter", "statement 2"),
    }


def test_repeated_table_reference_produces_one_observation() -> None:
    statements: tuple[Expression, ...] = parse_sql(
        sql="""
        SELECT child.customer_id
        FROM customer AS child
        JOIN customer AS parent
            ON child.parent_id = parent.customer_id
        """
    )

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    assert len(observations) == 1
    assert observations[0].object.identity.locator == "customer"


def test_select_literal_produces_no_dependency() -> None:
    statements: tuple[Expression, ...] = parse_sql(sql="SELECT 1")

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    assert observations == ()


def test_rejects_non_sql_subject() -> None:
    python_asset = Asset(
        identity=AssetIdentity(
            kind=AssetKind.PYTHON_SCRIPT,
            source_namespace="filesystem:merewell",
            locator="python/ingest.py",
        )
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="requires a SQL_SCRIPT",
    ):
        SqlDependencyExtractor().extract(
            statements=parse_sql(sql="SELECT * FROM customer"),
            subject=python_asset,
            artifact_id=ARTIFACT_ID,
            relation_namespace=RELATION_NAMESPACE,
        )


def test_insert_can_read_and_write_same_table() -> None:
    statements: tuple[Expression, ...] = parse_sql(
        sql="""
        INSERT INTO customer
        SELECT *
        FROM customer
        """
    )

    observations: tuple[Observation, ...] = SqlDependencyExtractor().extract(
        statements=statements,
        subject=SCRIPT,
        artifact_id=ARTIFACT_ID,
        relation_namespace=RELATION_NAMESPACE,
    )

    relationships: set[Predicate] = {
        observation.predicate
        for observation in observations
        if observation.object.identity.locator == "customer"
    }

    assert relationships == {
        Predicate.READS_FROM,
        Predicate.WRITES_TO,
    }
