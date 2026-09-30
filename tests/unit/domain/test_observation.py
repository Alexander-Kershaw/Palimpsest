from uuid import UUID

import pytest

from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind
from palimpsest.domain.observation import Observation
from palimpsest.domain.predicates import Predicate

ARTIFACT_ID = UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

SCRIPT = Asset(
    identity=AssetIdentity(
        kind=AssetKind.SQL_SCRIPT,
        source_namespace="filesystem:merewell",
        locator="sql/10_merge_customers.sql",
    )
)

TABLE = Asset(
    identity=AssetIdentity(
        kind=AssetKind.TABLE,
        source_namespace="database:merewell",
        locator="stg_customer",
    )
)


def test_observation_records_detected_relationship() -> None:
    observation = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=TABLE,
        artifact_id=ARTIFACT_ID,
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    assert observation.subject == SCRIPT
    assert observation.predicate is Predicate.READS_FROM
    assert observation.object == TABLE
    assert observation.artifact_id == ARTIFACT_ID
    assert observation.extractor == "SqlDependencyExtractor"
    assert observation.location == "statement 1"


def test_same_evidence_produces_equal_observation() -> None:
    first = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=TABLE,
        artifact_id=ARTIFACT_ID,
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    second = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=TABLE,
        artifact_id=ARTIFACT_ID,
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    assert first == second
    assert len({first, second}) == 1


def test_different_artifact_means_different_observation() -> None:
    first = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=TABLE,
        artifact_id=ARTIFACT_ID,
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    second = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=TABLE,
        artifact_id=UUID(hex="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    assert first != second


def test_different_location_means_different_observation() -> None:
    first = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=TABLE,
        artifact_id=ARTIFACT_ID,
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    second = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=TABLE,
        artifact_id=ARTIFACT_ID,
        extractor="SqlDependencyExtractor",
        location="statement 2",
    )

    assert first != second


@pytest.mark.parametrize(
    argnames="extractor",
    argvalues=[
        "",
        "   ",
    ],
)
def test_observation_rejects_blank_extractor(
    extractor: str,
) -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="extractor cannot be blank",
    ):
        Observation(
            subject=SCRIPT,
            predicate=Predicate.READS_FROM,
            object=TABLE,
            artifact_id=ARTIFACT_ID,
            extractor=extractor,
        )


@pytest.mark.parametrize(
    argnames="location",
    argvalues=[
        "",
        "   ",
    ],
)
def test_observation_rejects_blank_location(
    location: str,
) -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="location cannot be blank",
    ):
        Observation(
            subject=SCRIPT,
            predicate=Predicate.READS_FROM,
            object=TABLE,
            artifact_id=ARTIFACT_ID,
            extractor="SqlDependencyExtractor",
            location=location,
        )
