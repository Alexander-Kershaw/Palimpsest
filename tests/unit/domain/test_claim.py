from uuid import UUID

import pytest

from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind
from palimpsest.domain.claim import Claim, DirectClaim
from palimpsest.domain.observation import Observation
from palimpsest.domain.predicates import Predicate

SCRIPT = Asset(
    identity=AssetIdentity(
        kind=AssetKind.SQL_SCRIPT,
        source_namespace="filesystem:merewell",
        locator="sql/load_customer.sql",
    )
)

STAGING = Asset(
    identity=AssetIdentity(
        kind=AssetKind.TABLE,
        source_namespace="database:merewell",
        locator="stg_customer",
    )
)

CUSTOMER = Asset(
    identity=AssetIdentity(
        kind=AssetKind.TABLE,
        source_namespace="database:merewell",
        locator="customer",
    )
)


def test_direct_claim_requires_support() -> None:
    claim = Claim(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="requires at least one observation",
    ):
        DirectClaim(
            claim=claim,
            observations=frozenset(),
        )


def test_direct_claim_accepts_matching_observation() -> None:
    observation = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
        artifact_id=UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    claim = Claim(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
    )

    direct = DirectClaim(
        claim=claim,
        observations=frozenset({observation}),
    )

    assert observation in direct.observations


def test_direct_claim_rejects_unrelated_observation() -> None:
    observation = Observation(
        subject=SCRIPT,
        predicate=Predicate.WRITES_TO,
        object=CUSTOMER,
        artifact_id=UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    claim = Claim(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="does not support",
    ):
        DirectClaim(
            claim=claim,
            observations=frozenset({observation}),
        )
