from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from palimpsest.domain.scan import Scan, ScanStatus

SCAN_ID = UUID(hex="12345678-1234-5678-1234-567812345678")
STARTED_AT = datetime(year=2026, month=9, day=29, hour=9, minute=0, tzinfo=UTC)


def test_new_scan_can_be_running() -> None:
    scan = Scan(
        scan_id=SCAN_ID,
        started_at=STARTED_AT,
    )

    assert scan.scan_id == SCAN_ID
    assert scan.status is ScanStatus.RUNNING
    assert scan.completed_at is None


def test_running_scan_can_complete() -> None:
    scan = Scan(
        scan_id=SCAN_ID,
        started_at=STARTED_AT,
    )

    completed_at: datetime = STARTED_AT + timedelta(minutes=5)

    completed: Scan = scan.complete(at=completed_at)

    assert scan.status is ScanStatus.RUNNING
    assert scan.completed_at is None

    assert completed.scan_id == scan.scan_id
    assert completed.status is ScanStatus.COMPLETED
    assert completed.completed_at == completed_at


def test_running_scan_can_fail() -> None:
    scan = Scan(
        scan_id=SCAN_ID,
        started_at=STARTED_AT,
    )

    failed_at: datetime = STARTED_AT + timedelta(minutes=2)

    failed: Scan = scan.fail(at=failed_at)

    assert failed.scan_id == scan.scan_id
    assert failed.status is ScanStatus.FAILED
    assert failed.completed_at == failed_at


def test_finished_scan_cannot_finish_again() -> None:
    completed: Scan = Scan(
        scan_id=SCAN_ID,
        started_at=STARTED_AT,
    ).complete(at=STARTED_AT + timedelta(minutes=5))

    with pytest.raises(expected_exception=ValueError, match="already finished"):
        completed.complete(at=STARTED_AT + timedelta(minutes=10))


def test_scan_rejects_naive_started_at() -> None:
    naive_datetime = datetime(year=2026, month=9, day=29, hour=9, minute=0)

    with pytest.raises(
        expected_exception=ValueError,
        match="started_at must be timezone aware",
    ):
        Scan(
            scan_id=SCAN_ID,
            started_at=naive_datetime,
        )


def test_scan_rejects_completion_before_start() -> None:
    scan = Scan(
        scan_id=SCAN_ID,
        started_at=STARTED_AT,
    )

    with pytest.raises(
        expected_exception=ValueError,
        match="completed_at cannot be earlier",
    ):
        scan.complete(at=STARTED_AT - timedelta(seconds=1))


def test_running_scan_cannot_have_completion_timestamp() -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="running scan cannot",
    ):
        Scan(
            scan_id=SCAN_ID,
            started_at=STARTED_AT,
            status=ScanStatus.RUNNING,
            completed_at=STARTED_AT + timedelta(minutes=1),
        )


@pytest.mark.parametrize(
    argnames="status",
    argvalues=[
        ScanStatus.COMPLETED,
        ScanStatus.FAILED,
    ],
)
def test_finished_scan_requires_completion_timestamp(
    status: ScanStatus,
) -> None:
    with pytest.raises(
        expected_exception=ValueError,
        match="finished scan must",
    ):
        Scan(
            scan_id=SCAN_ID,
            started_at=STARTED_AT,
            status=status,
        )
