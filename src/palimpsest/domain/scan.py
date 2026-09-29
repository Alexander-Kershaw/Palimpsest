from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID


class ScanStatus(StrEnum):

    # A scan can take these 3 states
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Scan:
    
    """
    ==================================================================================================
    
    A scan has the following attributes:

    - scan_id: the unique identifier of the scan run
    - started_at: when a scan was initiated
    - status: the state of the scan
    - completed_at: when a scan was concluded

    a scan state is not static, it changes, however each individual state representation is 
    immutable. With Palimpsest, I care a lot about data history, provenance, and reproducibility
    so mutating states is not ideal as its bascially and overwrite.

    Instead using this general idea:

    RUNNING Scan --> complete() --> COMPLETED scan

    where complete() returns a new representation of the same scan identity:

    Scan abc123
    │
    ├── state 1: RUNNING
    │
    └── state 2: COMPLETED

    ==================================================================================================
    """

    scan_id: UUID
    started_at: datetime
    status: ScanStatus = ScanStatus.RUNNING
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        # Validate lifecycle and timestamp invariants
        self._require_timezone_aware(
            value=self.started_at,
            field_name="started_at",
        )

        if self.completed_at is not None:
            self._require_timezone_aware(
                value=self.completed_at,
                field_name="completed_at",
            )

            if self.completed_at < self.started_at:
                raise ValueError(
                    "completed_at cannot be earlier than started_at"
                )

        if self.status is ScanStatus.RUNNING and self.completed_at is not None:
            raise ValueError(
                "a running scan cannot have completed_at set"
            )

        if self.status is not ScanStatus.RUNNING and self.completed_at is None:
            raise ValueError(
                "a finished scan must have completed_at set"
            )

    def complete(self, *, at: datetime) -> Self:
        # The completed state of a scan
        return self._finish(
            status=ScanStatus.COMPLETED,
            at=at,
        )

    def fail(self, *, at: datetime) -> Self:
        # the failed state of a scan
        return self._finish(
            status=ScanStatus.FAILED,
            at=at,
        )

    def _finish(
        self,
        *,
        status: ScanStatus,
        at: datetime,
    ) -> Self:
        # State of a running scan
        if self.status is not ScanStatus.RUNNING:
            raise ValueError("scan has already finished")
        # replace used here used to construct another can with different status
        return replace(
            self,
            status=status,
            completed_at=at,
        )

    @staticmethod
    def _require_timezone_aware(
        *,
        value: datetime,
        field_name: str,
    ) -> None:
        """
        Require a datetime containing timezone information.

        Dont' want timezone drift (naive datetime), so temporal context is
        not ambiguous. Ambiguity would hurt data prevenance.

        Furthermore, Palimpsest eventually could investigate systems distributed
        across: servers, databases, repos, regions, etc...

        Not UTC specifically, I can standardize that later
        
        """
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone aware")