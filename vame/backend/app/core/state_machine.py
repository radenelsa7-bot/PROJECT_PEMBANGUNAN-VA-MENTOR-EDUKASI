"""Core Engine: state machine status belajar (SRS B.1, FR-13..FR-15).

Modul ini MURNI (tanpa DB / tanpa AI) sehingga dapat diuji tanpa memanggil AI API (NFR-16).
Alur belajar dikendalikan di sini, bukan oleh AI (SRS 2.5).
"""
from enum import Enum


class Status(str, Enum):
    LOCKED = "LOCKED"
    AVAILABLE = "AVAILABLE"
    READING = "READING"
    DISCUSSING = "DISCUSSING"
    ASSESSMENT = "ASSESSMENT"
    PASSED = "PASSED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class Trigger(str, Enum):
    UNLOCK = "unlock"  # poin sebelumnya PASSED
    OPEN_READING = "open_reading"
    COMPLETE_READING = "complete_reading"
    REQUEST_EVALUATION = "request_evaluation"
    PASS_ = "pass"
    FAIL = "fail"
    REVIEW = "review"


TRANSITIONS: dict[tuple[Status, Trigger], Status] = {
    (Status.LOCKED, Trigger.UNLOCK): Status.AVAILABLE,
    (Status.AVAILABLE, Trigger.OPEN_READING): Status.READING,
    (Status.READING, Trigger.COMPLETE_READING): Status.DISCUSSING,
    (Status.DISCUSSING, Trigger.REQUEST_EVALUATION): Status.ASSESSMENT,
    (Status.ASSESSMENT, Trigger.PASS_): Status.PASSED,
    (Status.ASSESSMENT, Trigger.FAIL): Status.NEEDS_REVIEW,
    (Status.NEEDS_REVIEW, Trigger.REVIEW): Status.READING,
}


class InvalidTransition(Exception):
    def __init__(self, current: Status, trigger: Trigger):
        self.current, self.trigger = current, trigger
        super().__init__(f"Transisi '{trigger.value}' tidak valid dari status {current.value}")


def transition(current: Status | str, trigger: Trigger | str) -> Status:
    cur, trg = Status(current), Trigger(trigger)
    try:
        return TRANSITIONS[(cur, trg)]
    except KeyError:
        raise InvalidTransition(cur, trg) from None


def next_status_after_score(score: float, threshold: float) -> tuple[Trigger, Status]:
    """FR-24: PASSED jika skor >= batas, selain itu NEEDS_REVIEW."""
    trg = Trigger.PASS_ if score >= threshold else Trigger.FAIL
    return trg, TRANSITIONS[(Status.ASSESSMENT, trg)]


def can_open_mentoring(status: Status | str) -> bool:
    """BR-01 / FR-12: mentoring hanya setelah bacaan wajib ditandai selesai."""
    return Status(status) == Status.DISCUSSING
