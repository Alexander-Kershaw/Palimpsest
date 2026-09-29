from datetime import datetime
from pathlib import Path
from uuid import UUID

from palimpsest.domain.artifact import Artifact
from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind

"""
===================================================================================================

FILESYSTEM COLLECTOR

===================================================================================================

The collector serves to aquire evidence for later Palimpsest judgements.

It is not responsible for understanding any encountered syntax or deriving observations, those
tasks will be reserved for the parser and extractor constructs.

For now, the collector searches data estate directories for supported AssetKind instances such 
as SQL, data files like CSV, documentation, and Python scripts, and scheduling files for now.

Unsupported file types as of now are considered None, this is not saying they dont exist, just
that they currently do not have a model within Palimpsest

---------------------------------------------------------------------------------------------------

The filesystem discovery and collection are fundamental for supporting the establishment of 
determinsitic evidence paths. The structure currently enables by this script is as follows:

       REAL LEGACY ESTATE
               │
               ▼
      Filesystem discovery
               │
               ▼
             Asset
               │
               ▼
      Filesystem acquisition
               │
               ▼
            Artifact
               │
        ┌──────┼──────┐
        ▼      ▼      ▼
      Scan   bytes   SHA-256

===================================================================================================
"""


class FilesystemCollector:
    def discover_assets(
        self,
        *,
        root: Path,
        source_namespace: str,
    ) -> tuple[Asset, ...]:

        self._validate_root(root=root)

        assets: list[Asset] = []

        # using recursive glob to find descendants (determinstic discovery ordering)
        for path in sorted(root.rglob(pattern="*")):
            if not path.is_file():  # Filter out directories as these are not assets
                continue

            kind: AssetKind | None = self._classify(path)

            if kind is None:
                continue

            locator: str = path.relative_to(root).as_posix()

            assets.append(
                Asset(
                    identity=AssetIdentity(
                        kind=kind, source_namespace=source_namespace, locator=locator
                    )
                )
            )

        return tuple(assets)

    def collect_artifact(
        self,
        *,
        root: Path,
        source_namespace: str,
        asset: Asset,
        scan_id: UUID,
        artifact_id: UUID,
        collected_at: datetime,
    ) -> Artifact:

        self._validate_root(root)

        if asset.identity.source_namespace != source_namespace:
            raise ValueError(
                "asset source namespace does not match the collection namespace"
            )

        path: Path = self._resolve_asset_path(root=root, locator=asset.identity.locator)

        actual_kind: AssetKind | None = self._classify(path=path)

        if actual_kind is None:
            raise ValueError(
                f"asset locator references an unsupported file: {asset.identity.locator}"
            )

        if actual_kind is not asset.identity.kind:
            raise ValueError("asset kind does not match filesystem configuration")

        return Artifact(
            artifact_id=artifact_id,
            scan_id=scan_id,
            asset=asset,
            collected_at=collected_at,
            content_type=self._content_type(path),
            content=path.read_bytes(),
        )

    @staticmethod
    def _classify(path: Path) -> AssetKind | None:

        if path.name == "crontab.txt":
            return AssetKind.SCHEDULER_DEFINITION

        match path.suffix.lower():
            case ".sql":
                return AssetKind.SQL_SCRIPT
            case ".py":
                return AssetKind.PYTHON_SCRIPT
            case ".csv":
                return AssetKind.DATA_FILE
            case ".md":
                return AssetKind.DOCUMENT
            case _:
                return None

    @staticmethod
    def _validate_root(root: Path) -> None:

        if not root.exists():
            raise ValueError(f"root does not exist: {root}")

        if not root.is_dir():
            raise ValueError(f"root must be a directory: {root}")

    @staticmethod
    def _resolve_asset_path(*, root: Path, locator: str) -> Path:

        resolved_root: Path = root.resolve()
        resolved_path: Path = (resolved_root / locator).resolve()

        try:
            resolved_path.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(
                f"asset locator escapes collection root: {locator}"
            ) from exc

        if not resolved_path.exists():
            raise ValueError(f"asset no longer exists in resolved path: {locator}")

        if not resolved_path.is_file():
            raise ValueError(f"asset locator is not a file: {locator}")

        return resolved_path

    @staticmethod
    def _content_type(path: Path) -> str:

        if path.name == "crontab.txt":
            return "text/plain"

        match path.suffix.lower():
            case ".sql":
                return "text/x-sql"
            case ".py":
                return "text/x-python"
            case ".csv":
                return "text/csv"
            case ".md":
                return "text/markdown"
            case _:
                raise ValueError(f"unsupported artifact content type: {path}")
