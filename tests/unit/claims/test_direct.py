from uuid import UUID

from palimpsest.claims.direct import build_direct_claims
from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind
from palimpsest.domain.claim import DirectClaim
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


def test_one_observation_creates_one_direct_claim() -> None:
    observation = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
        artifact_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    claims: tuple[DirectClaim, ...] = build_direct_claims(observations=[observation])

    assert len(claims) == 1
    assert claims[0].claim.subject == SCRIPT
    assert claims[0].claim.predicate is Predicate.READS_FROM
    assert claims[0].claim.object == STAGING
    assert claims[0].observations == frozenset({observation})


def test_multiple_observations_support_same_claim() -> None:
    first = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
        artifact_id=UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    second = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
        artifact_id=UUID(hex="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    claims: tuple[DirectClaim, ...] = build_direct_claims(
        observations=[
            first,
            second,
        ]
    )

    assert len(claims) == 1
    assert claims[0].observations == frozenset(
        {
            first,
            second,
        }
    )


def test_different_propositions_create_different_claims() -> None:
    read = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
        artifact_id=UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    write = Observation(
        subject=SCRIPT,
        predicate=Predicate.WRITES_TO,
        object=CUSTOMER,
        artifact_id=UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    claims: tuple[DirectClaim, ...] = build_direct_claims(
        observations=[
            read,
            write,
        ]
    )

    assert len(claims) == 2


def test_duplicate_observation_does_not_add_support() -> None:
    observation = Observation(
        subject=SCRIPT,
        predicate=Predicate.READS_FROM,
        object=STAGING,
        artifact_id=UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        extractor="SqlDependencyExtractor",
        location="statement 1",
    )

    claims: tuple[DirectClaim, ...] = build_direct_claims(
        observations=[
            observation,
            observation,
        ]
    )

    assert len(claims) == 1
    assert len(claims[0].observations) == 1


def test_no_observations_produces_no_claims() -> None:
    assert build_direct_claims(observations=[]) == ()
