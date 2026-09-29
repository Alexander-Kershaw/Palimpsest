from pathlib import Path

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


===================================================================================================
"""


class FilesystemCollector:
    def discover_assets(
        self,
        *,
        root: Path,
        source_namespace: str,
    ) -> tuple[Asset, ...]:

        if not root.exists():
            raise ValueError(f"root does not exist: {root}")

        if not root.is_dir():
            raise ValueError(f"root must be a directory: {root}")

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
