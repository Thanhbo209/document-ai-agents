import pytest

from app.models.enums import JobStatus
from app.services.job_state import (
    InvalidJobStatusTransition,
    can_transition_job,
    ensure_job_transition,
)


def test_valid_job_transitions() -> None:
    assert can_transition_job(JobStatus.QUEUED, JobStatus.PROCESSING)
    assert can_transition_job(JobStatus.QUEUED, JobStatus.CANCELLED)
    assert can_transition_job(JobStatus.PROCESSING, JobStatus.SUCCEEDED)
    assert can_transition_job(JobStatus.PROCESSING, JobStatus.FAILED)
    assert can_transition_job(JobStatus.PROCESSING, JobStatus.CANCELLED)


def test_terminal_job_statuses_cannot_transition() -> None:
    assert not can_transition_job(JobStatus.SUCCEEDED, JobStatus.PROCESSING)
    assert not can_transition_job(JobStatus.FAILED, JobStatus.PROCESSING)
    assert not can_transition_job(JobStatus.CANCELLED, JobStatus.PROCESSING)


def test_invalid_transition_raises_error() -> None:
    with pytest.raises(InvalidJobStatusTransition):
        ensure_job_transition(JobStatus.SUCCEEDED, JobStatus.PROCESSING)
