import pytest

from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind


def test_same_identity_represents_same_conceptual_asset() -> None:
    first_scan_asset = Asset(
        identity=AssetIdentity(
            kind=AssetKind.TABLE,
            source_namespace="database:merewell",
            locator="warehouse.customer",
        )
    )

    second_scan_asset = Asset(
        identity=AssetIdentity(
            kind=AssetKind.TABLE,
            source_namespace="database:merewell",
            locator="warehouse.customer",
        )
    )

    assert first_scan_asset == second_scan_asset
    assert len({first_scan_asset, second_scan_asset}) == 1


@pytest.mark.parametrize(
    argnames="different_identity",
    argvalues=[
        AssetIdentity(
            kind=AssetKind.VIEW,
            source_namespace="database:merewell",
            locator="warehouse.customer",
        ),
        AssetIdentity(
            kind=AssetKind.TABLE,
            source_namespace="database:another-system",
            locator="warehouse.customer",
        ),
        AssetIdentity(
            kind=AssetKind.TABLE,
            source_namespace="database:merewell",
            locator="archive.customer",
        ),
    ],
)
def test_identity_changes_when_any_identity_coordinate_changes(
    different_identity: AssetIdentity,
) -> None:
    original = AssetIdentity(
        kind=AssetKind.TABLE,
        source_namespace="database:merewell",
        locator="warehouse.customer",
    )

    assert original != different_identity


@pytest.mark.parametrize(
    argnames=("source_namespace", "locator"),
    argvalues=[
        ("", "warehouse.customer"),
        ("   ", "warehouse.customer"),
        ("database:merewell", ""),
        ("database:merewell", "   "),
    ],
)
def test_identity_rejects_blank_components(
    source_namespace: str,
    locator: str,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        AssetIdentity(
            kind=AssetKind.TABLE,
            source_namespace=source_namespace,
            locator=locator,
        )


@pytest.mark.parametrize(
    argnames=("source_namespace", "locator"),
    argvalues=[
        (" database:merewell", "warehouse.customer"),
        ("database:merewell ", "warehouse.customer"),
        ("database:merewell", " warehouse.customer"),
        ("database:merewell", "warehouse.customer "),
    ],
)
def test_identity_rejects_untrimmed_components(
    source_namespace: str,
    locator: str,
) -> None:
    with pytest.raises(expected_exception=ValueError):
        AssetIdentity(
            kind=AssetKind.TABLE,
            source_namespace=source_namespace,
            locator=locator,
        )
