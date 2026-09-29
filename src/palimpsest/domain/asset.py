from dataclasses import dataclass
from enum import StrEnum


class AssetKind(StrEnum):
    """
    ==================================================================================================

    This class defines the kinds of system assets Palimpsest can reason about

    ==================================================================================================

    AssetKind is a StrEnum. To prevent ontology drift, spellings for each asset kind
    are very much fixed here as an AssetKind object attribute

    Using StrEnum over ordinary Enum since this naturally serializes values as strings e.g

    AssetKind.TABLE.value will return a string "table".

    Controlling vocabulary like this keeps everything controlled and avoids continually
    inventing equivalent concepts e.g "db-table", "database_table" etc... just "table" is fine

    ==================================================================================================
    """

    TABLE = "table"
    VIEW = "view"
    SQL_SCRIPT = "sql_script"
    PYTHON_SCRIPT = "python_script"
    DATA_FILE = "data_file"
    SCHEDULED_JOB = "scheduled_job"
    DOCUMENT = "document"


@dataclass(frozen=True, slots=True)
class AssetIdentity:
    kind: AssetKind
    source_namespace: str
    locator: str

    def __post_init__(self) -> None:

        self._validate_component(
            value=self.source_namespace, field_name="source_namespace"
        )
        self._validate_component(value=self.locator, field_name="locator")

    @staticmethod
    def _validate_component(value: str, field_name: str) -> None:

        if not value.strip():
            raise ValueError(f"{field_name} cannot be blank")

        if value != value.strip():
            raise ValueError(
                f"{field_name} cannot contain leading or trailing whitespace"
            )


@dataclass(frozen=True, slots=True)
class Asset:
    identity: AssetIdentity
