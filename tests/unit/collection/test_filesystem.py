from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import UUID

import pytest

from palimpsest.collection.filesystem import FilesystemCollector
from palimpsest.domain.artifact import Artifact
from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind

SCAN_ID = UUID(hex="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ARTIFACT_ID = UUID(hex="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

COLLECTED_AT = datetime(
    year=2026,
    month=9,
    day=29,
    hour=13,
    minute=0,
    tzinfo=UTC,
)


# Temporary dummy paths / assets
def test_discovers_supported_assets(tmp_path: Path) -> None:
    (tmp_path / "sql").mkdir()
    (tmp_path / "python").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "scheduler").mkdir()

    (tmp_path / "sql" / "load.sql").write_text(
        data="SELECT 1;",
        encoding="utf-8",
    )
    (tmp_path / "python" / "ingest.py").write_text(
        data="print('hello')",
        encoding="utf-8",
    )
    (tmp_path / "data" / "customers.csv").write_text(
        data="customer_id\n1\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "overview.md").write_text(
        data="# Overview",
        encoding="utf-8",
    )
    (tmp_path / "scheduler" / "crontab.txt").write_text(
        data="0 1 * * * python ingest.py",
        encoding="utf-8",
    )

    collector = FilesystemCollector()

    assets: tuple[Asset, ...] = collector.discover_assets(
        root=tmp_path,
        source_namespace="filesystem:merewell",
    )

    discovered: set[tuple[AssetKind, str]] = {
        (asset.identity.kind, asset.identity.locator) for asset in assets
    }

    assert discovered == {
        (AssetKind.SQL_SCRIPT, "sql/load.sql"),
        (AssetKind.PYTHON_SCRIPT, "python/ingest.py"),
        (AssetKind.DATA_FILE, "data/customers.csv"),
        (AssetKind.DOCUMENT, "docs/overview.md"),
        (
            AssetKind.SCHEDULER_DEFINITION,
            "scheduler/crontab.txt",
        ),
    }


def test_ignores_unsupported_files(tmp_path: Path) -> None:
    (tmp_path / "supported.sql").write_text(
        data="SELECT 1;",
        encoding="utf-8",
    )
    (tmp_path / "unsupported.bin").write_bytes(data=b"\x00\x01")

    collector = FilesystemCollector()

    assets: tuple[Asset, ...] = collector.discover_assets(
        root=tmp_path,
        source_namespace="filesystem:merewell",
    )

    assert len(assets) == 1
    assert assets[0].identity.locator == "supported.sql"


def test_locator_is_relative_to_collection_root(
    tmp_path: Path,
) -> None:
    nested: Path = tmp_path / "some" / "deep" / "directory"
    nested.mkdir(parents=True)

    (nested / "query.sql").write_text(
        data="SELECT 1;",
        encoding="utf-8",
    )

    collector = FilesystemCollector()

    assets: tuple[Asset, ...] = collector.discover_assets(
        root=tmp_path,
        source_namespace="filesystem:merewell",
    )

    assert assets[0].identity.locator == ("some/deep/directory/query.sql")


def test_same_relative_path_and_namespace_give_same_identity(
    tmp_path: Path,
) -> None:
    first_root: Path = tmp_path / "machine-a"
    second_root: Path = tmp_path / "machine-b"

    first_root.mkdir()
    second_root.mkdir()

    (first_root / "load.sql").write_text(
        data="SELECT 1;",
        encoding="utf-8",
    )
    (second_root / "load.sql").write_text(
        data="SELECT 2;",
        encoding="utf-8",
    )

    collector = FilesystemCollector()

    first: tuple[Asset, ...] = collector.discover_assets(
        root=first_root,
        source_namespace="filesystem:merewell",
    )

    second: tuple[Asset, ...] = collector.discover_assets(
        root=second_root,
        source_namespace="filesystem:merewell",
    )

    assert first[0].identity == second[0].identity


def test_rejects_missing_root(tmp_path: Path) -> None:
    collector = FilesystemCollector()

    with pytest.raises(
        expected_exception=ValueError,
        match="root does not exist",
    ):
        collector.discover_assets(
            root=tmp_path / "missing",
            source_namespace="filesystem:merewell",
        )


def test_rejects_file_as_root(tmp_path: Path) -> None:
    file_path: Path = tmp_path / "not-a-directory.sql"
    file_path.write_text(data="SELECT 1;", encoding="utf-8")

    collector = FilesystemCollector()

    with pytest.raises(
        expected_exception=ValueError,
        match="root must be a directory",
    ):
        collector.discover_assets(
            root=file_path,
            source_namespace="filesystem:merewell",
        )


def test_collects_exact_file_bytes(tmp_path: Path) -> None:
    content = b"SELECT * FROM stg_customer;\n"

    (tmp_path / "load.sql").write_bytes(data=content)

    collector = FilesystemCollector()

    assets: tuple[Asset, ...] = collector.discover_assets(
        root=tmp_path,
        source_namespace="filesystem:merewell",
    )

    artifact: Artifact = collector.collect_artifact(
        root=tmp_path,
        source_namespace="filesystem:merewell",
        asset=assets[0],
        scan_id=SCAN_ID,
        artifact_id=ARTIFACT_ID,
        collected_at=COLLECTED_AT,
    )

    assert artifact.content == content
    assert artifact.content_hash == sha256(content).hexdigest()


def test_collected_artifact_preserves_provenance(
    tmp_path: Path,
) -> None:
    (tmp_path / "load.sql").write_text(
        data="SELECT 1;",
        encoding="utf-8",
    )

    collector = FilesystemCollector()

    asset: Asset = collector.discover_assets(
        root=tmp_path,
        source_namespace="filesystem:merewell",
    )[0]

    artifact: Artifact = collector.collect_artifact(
        root=tmp_path,
        source_namespace="filesystem:merewell",
        asset=asset,
        scan_id=SCAN_ID,
        artifact_id=ARTIFACT_ID,
        collected_at=COLLECTED_AT,
    )

    assert artifact.asset == asset
    assert artifact.scan_id == SCAN_ID
    assert artifact.artifact_id == ARTIFACT_ID
    assert artifact.collected_at == COLLECTED_AT
    assert artifact.content_type == "text/x-sql"


def test_collects_empty_file_as_valid_evidence(
    tmp_path: Path,
) -> None:
    (tmp_path / "empty.sql").write_bytes(data=b"")

    collector = FilesystemCollector()

    asset: Asset = collector.discover_assets(
        root=tmp_path,
        source_namespace="filesystem:merewell",
    )[0]

    artifact: Artifact = collector.collect_artifact(
        root=tmp_path,
        source_namespace="filesystem:merewell",
        asset=asset,
        scan_id=SCAN_ID,
        artifact_id=ARTIFACT_ID,
        collected_at=COLLECTED_AT,
    )

    assert artifact.content == b""


def test_recollection_detects_changed_content(
    tmp_path: Path,
) -> None:
    path: Path = tmp_path / "load.sql"
    path.write_text(
        data="SELECT 1;",
        encoding="utf-8",
    )

    collector = FilesystemCollector()

    asset: Asset = collector.discover_assets(
        root=tmp_path,
        source_namespace="filesystem:merewell",
    )[0]

    first: Artifact = collector.collect_artifact(
        root=tmp_path,
        source_namespace="filesystem:merewell",
        asset=asset,
        scan_id=UUID(hex="11111111-1111-1111-1111-111111111111"),
        artifact_id=UUID(hex="22222222-2222-2222-2222-222222222222"),
        collected_at=COLLECTED_AT,
    )

    path.write_text(
        data="SELECT customer_id FROM customer;",
        encoding="utf-8",
    )

    second: Artifact = collector.collect_artifact(
        root=tmp_path,
        source_namespace="filesystem:merewell",
        asset=asset,
        scan_id=UUID(hex="33333333-3333-3333-3333-333333333333"),
        artifact_id=UUID(hex="44444444-4444-4444-4444-444444444444"),
        collected_at=COLLECTED_AT,
    )

    assert first.asset == second.asset
    assert first.content_hash != second.content_hash


def test_rejects_asset_from_different_namespace(
    tmp_path: Path,
) -> None:
    (tmp_path / "load.sql").write_text(
        data="SELECT 1;",
        encoding="utf-8",
    )

    collector = FilesystemCollector()

    asset: Asset = collector.discover_assets(
        root=tmp_path,
        source_namespace="filesystem:merewell",
    )[0]

    with pytest.raises(
        expected_exception=ValueError,
        match="source namespace does not match",
    ):
        collector.collect_artifact(
            root=tmp_path,
            source_namespace="filesystem:another-system",
            asset=asset,
            scan_id=SCAN_ID,
            artifact_id=ARTIFACT_ID,
            collected_at=COLLECTED_AT,
        )


def test_rejects_asset_kind_that_disagrees_with_file(
    tmp_path: Path,
) -> None:
    (tmp_path / "ingest.py").write_text(
        data="print('hello')",
        encoding="utf-8",
    )

    incorrect_asset = Asset(
        identity=AssetIdentity(
            kind=AssetKind.SQL_SCRIPT,
            source_namespace="filesystem:merewell",
            locator="ingest.py",
        )
    )

    collector = FilesystemCollector()

    with pytest.raises(
        expected_exception=ValueError,
        match="asset kind does not match",
    ):
        collector.collect_artifact(
            root=tmp_path,
            source_namespace="filesystem:merewell",
            asset=incorrect_asset,
            scan_id=SCAN_ID,
            artifact_id=ARTIFACT_ID,
            collected_at=COLLECTED_AT,
        )


def test_rejects_locator_that_escapes_collection_root(
    tmp_path: Path,
) -> None:
    outside: Path = tmp_path.parent / "outside.sql"
    outside.write_text(
        data="SELECT secret;",
        encoding="utf-8",
    )

    asset = Asset(
        identity=AssetIdentity(
            kind=AssetKind.SQL_SCRIPT,
            source_namespace="filesystem:merewell",
            locator="../outside.sql",
        )
    )

    collector = FilesystemCollector()

    with pytest.raises(
        expected_exception=ValueError,
        match="escapes collection root",
    ):
        collector.collect_artifact(
            root=tmp_path,
            source_namespace="filesystem:merewell",
            asset=asset,
            scan_id=SCAN_ID,
            artifact_id=ARTIFACT_ID,
            collected_at=COLLECTED_AT,
        )
