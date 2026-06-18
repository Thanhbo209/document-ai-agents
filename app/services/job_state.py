from app.models.enums import JobStatus


class InvalidJobStatusTransition(ValueError):
    pass


_ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.QUEUED: {JobStatus.PROCESSING, JobStatus.CANCELLED},
    JobStatus.PROCESSING: {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.SUCCEEDED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELLED: set(),
}


def can_transition_job(current: JobStatus | str, target: JobStatus | str) -> bool:
    current_status = JobStatus(current)
    target_status = JobStatus(target)

    return target_status in _ALLOWED_TRANSITIONS[current_status]


def ensure_job_transition(current: JobStatus | str, target: JobStatus | str) -> None:
    if not can_transition_job(current, target):
        raise InvalidJobStatusTransition(
            f"Cannot transition ingestion job from {current!s} to {target!s}"
        )
