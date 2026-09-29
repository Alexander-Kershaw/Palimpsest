from pathlib import Path

import pytest

from palimpsest.collection.filesystem import FilesystemCollector
from palimpsest.domain.asset import Asset, AssetKind


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
