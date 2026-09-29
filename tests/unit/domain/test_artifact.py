from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

import pytest

from palimpsest.domain.artifact import Artifact
from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind

ARTIFACT_ID = UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SCAN_ID = UUID(hex="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

COLLECTED_AT = datetime(
    year=2026,
    month=9,
    day=29,
    hour=12,
    minute=0,
    tzinfo=UTC,
)

# Example test Asset
ASSET = Asset(
    identity=AssetIdentity(
        kind=AssetKind.SQL_SCRIPT,
        source_namespace="filesystem:merewell",
        locator="sql/10_merge_customers.sql",
    )
)


def test_artifact_records_scan_and_asset() -> None:
    artifact = Artifact(
        artifact_id=ARTIFACT_ID,
        scan_id=SCAN_ID,
        asset=ASSET,
        collected_at=COLLECTED_AT,
        content_type="text/x-sql",
        content=b"SELECT * FROM stg_customer;",
    )

    assert artifact.artifact_id == ARTIFACT_ID
    assert artifact.scan_id == SCAN_ID
    assert artifact.asset == ASSET


def test_artifact_calculates_sha256_from_content() -> None:
    content = b"SELECT * FROM stg_customer;"

    artifact = Artifact(
        artifact_id=ARTIFACT_ID,
        scan_id=SCAN_ID,
        asset=ASSET,
        collected_at=COLLECTED_AT,
        content_type="text/x-sql",
        content=content,
    )

    assert artifact.content_hash == sha256(content).hexdigest()


def test_same_content_produces_same_content_hash() -> None:
    content = b"SELECT * FROM stg_customer;"

    first = Artifact(
        artifact_id=UUID(hex="11111111-1111-1111-1111-111111111111"),
        scan_id=UUID(hex="22222222-2222-2222-2222-222222222222"),
        asset=ASSET,
        collected_at=COLLECTED_AT,
        content_type="text/x-sql",
        content=content,
    )

    second = Artifact(
        artifact_id=UUID(hex="33333333-3333-3333-3333-333333333333"),
        scan_id=UUID(hex="44444444-4444-4444-4444-444444444444"),
        asset=ASSET,
        collected_at=COLLECTED_AT,
        content_type="text/x-sql",
        content=content,
    )

    assert first != second  # different Artifact ID
    assert first.content_hash == second.content_hash  # Same content hash


def test_changed_content_changes_content_hash() -> None:
    first = Artifact(
        artifact_id=UUID(hex="11111111-1111-1111-1111-111111111111"),
        scan_id=SCAN_ID,
        asset=ASSET,
        collected_at=COLLECTED_AT,
        content_type="text/x-sql",
        content=b"SELECT * FROM stg_customer;",
    )

    second = Artifact(
        artifact_id=UUID(hex="22222222-2222-2222-2222-222222222222"),
        scan_id=SCAN_ID,
        asset=ASSET,
        collected_at=COLLECTED_AT,
        content_type="text/x-sql",
        content=b"SELECT customer_id FROM stg_customer;",
    )

    assert first.asset == second.asset  # Same Asset
    assert first.content_hash != second.content_hash  # Different content hash


def test_empty_content_is_valid() -> None:
    artifact = Artifact(
        artifact_id=ARTIFACT_ID,
        scan_id=SCAN_ID,
        asset=ASSET,
        collected_at=COLLECTED_AT,
        content_type="text/plain",
        content=b"",
    )

    assert artifact.content_hash == sha256(b"").hexdigest()


def test_artifact_rejects_naive_collection_timestamp() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="collected_at must be timezone aware",
    ):
        Artifact(
            artifact_id=ARTIFACT_ID,
            scan_id=SCAN_ID,
            asset=ASSET,
            collected_at=datetime(year=2026, month=9, day=29, hour=12, minute=0),
            content_type="text/x-sql",
            content=b"SELECT 1;",
        )


@pytest.mark.parametrize(
    argnames="content_type",
    argvalues=[
        "",
        "   ",
    ],
)
def test_artifact_rejects_blank_content_type(
    content_type: str,
) -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="content_type cannot be blank",
    ):
        Artifact(
            artifact_id=ARTIFACT_ID,
            scan_id=SCAN_ID,
            asset=ASSET,
            collected_at=COLLECTED_AT,
            content_type=content_type,
            content=b"SELECT 1;",
        )


@pytest.mark.parametrize(
    argnames="content_type",
    argvalues=[
        " text/x-sql",
        "text/x-sql ",
    ],
)
def test_artifact_rejects_untrimmed_content_type(
    content_type: str,
) -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="content_type cannot contain",
    ):
        Artifact(
            artifact_id=ARTIFACT_ID,
            scan_id=SCAN_ID,
            asset=ASSET,
            collected_at=COLLECTED_AT,
            content_type=content_type,
            content=b"SELECT 1;",
        )
