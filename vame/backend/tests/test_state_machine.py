"""Core Engine diuji tanpa AI (NFR-16)."""
import pytest

from app.core import state_machine as sm
from app.core.state_machine import InvalidTransition, Status, Trigger


def test_happy_path_follows_appendix_b1():
    s = Status.LOCKED
    for trg, expected in [
        (Trigger.UNLOCK, Status.AVAILABLE),
        (Trigger.OPEN_READING, Status.READING),
        (Trigger.COMPLETE_READING, Status.DISCUSSING),
        (Trigger.REQUEST_EVALUATION, Status.ASSESSMENT),
        (Trigger.PASS_, Status.PASSED),
    ]:
        s = sm.transition(s, trg)
        assert s == expected


def test_fail_then_review_returns_to_reading():
    assert sm.transition(Status.ASSESSMENT, Trigger.FAIL) == Status.NEEDS_REVIEW
    assert sm.transition(Status.NEEDS_REVIEW, Trigger.REVIEW) == Status.READING


@pytest.mark.parametrize(
    "status,trigger",
    [
        (Status.LOCKED, Trigger.OPEN_READING),
        (Status.AVAILABLE, Trigger.REQUEST_EVALUATION),
        (Status.READING, Trigger.REQUEST_EVALUATION),  # BR-01: bacaan dulu, lalu diskusi
        (Status.DISCUSSING, Trigger.PASS_),
        (Status.PASSED, Trigger.OPEN_READING),  # PASSED = final
        (Status.NEEDS_REVIEW, Trigger.PASS_),
    ],
)
def test_invalid_transitions_rejected(status, trigger):
    with pytest.raises(InvalidTransition):
        sm.transition(status, trigger)


def test_score_threshold_boundary():
    assert sm.next_status_after_score(70, 70)[1] == Status.PASSED
    assert sm.next_status_after_score(69.9, 70)[1] == Status.NEEDS_REVIEW
    assert sm.next_status_after_score(55, 50)[1] == Status.PASSED


def test_mentoring_only_when_discussing():
    assert sm.can_open_mentoring(Status.DISCUSSING)
    assert not any(sm.can_open_mentoring(s) for s in Status if s != Status.DISCUSSING)
