from dataclasses import dataclass
from uuid import UUID

from palimpsest.domain.asset import Asset
from palimpsest.domain.predicates import Predicate


@dataclass(frozen=True, slots=True)
class Observation:
    subject: Asset
    predicate: Predicate
    object: Asset
    artifact_id: UUID
    extractor: str
    location: str | None = None

    def __post_init__(self) -> None:

        self._validate_text(value=self.extractor, field_name="extractor")

        if self.location is not None:
            self._validate_text(value=self.location, field_name="location")

    @staticmethod
    def _validate_text(*, value: str, field_name: str) -> None:

        if not value.strip():
            raise ValueError(f"{field_name} cannot be blank")

        if value != value.strip():
            raise ValueError(
                f"{field_name} cannot contain leading or trailing whitespace"
            )
