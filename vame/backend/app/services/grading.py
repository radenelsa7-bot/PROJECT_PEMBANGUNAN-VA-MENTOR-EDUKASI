"""Service grading evaluasi jawaban (FR-29)."""
import logging
import time

from sqlalchemy.orm import Session

from ..ai.client import AIClient, AIServiceError, AIOutputError
from ..ai.prompts import build_eval_grade_prompt, DEFAULT_SYSTEM_PROMPT
from ..core.learning import pass_threshold
from ..core.state_machine import next_status_after_score
from ..models import EvaluationAttempt, Question, ReadingPoint, utcnow
from ..schemas import AIGrade

log = logging.getLogger(__name__)


def grade_evaluation_attempt(db: Session, attempt_id: int, ai: AIClient) -> dict:
    """Grade pending EvaluationAttempt (FR-29). Returns updated attempt."""
    attempt = db.get(EvaluationAttempt, attempt_id)
    if not attempt or attempt.status != "pending":
        log.warning(f"Attempt {attempt_id} not pending or not found")
        return {}

    try:
        rp = db.get(ReadingPoint, attempt.reading_point_id)
        if not rp:
            raise ValueError(f"ReadingPoint {attempt.reading_point_id} not found")

        system, messages = build_eval_grade_prompt(
            DEFAULT_SYSTEM_PROMPT,
            rp,
            attempt.question,
            attempt.answer or "",
        )

        start = time.time()
        grade = ai.complete_structured(
            db,
            kind="eval_grade",
            system=system,
            messages=messages,
            schema=AIGrade,
            user_id=attempt.user_id,
        )
        elapsed = time.time() - start

        # Determine pass/fail
        threshold = pass_threshold(db)
        trigger, next_status = next_status_after_score(float(grade.score), threshold)

        attempt.status = "graded"
        attempt.score = float(grade.score)
        attempt.passed = trigger.value == "pass"
        attempt.feedback = grade.feedback
        attempt.graded_at = utcnow()
        db.commit()

        log.info(
            f"Graded attempt {attempt_id}: score={grade.score}, passed={attempt.passed}, "
            f"missed={len(grade.missed_points)}, elapsed={elapsed:.2f}s"
        )
        return {
            "attempt_id": attempt_id,
            "score": grade.score,
            "passed": attempt.passed,
            "feedback": grade.feedback,
            "missed_points": grade.missed_points,
            "grading_time": elapsed,
        }
    except AIServiceError as e:
        log.error(f"AI service unavailable grading attempt {attempt_id}: {e}")
        attempt.status = "error"
        attempt.feedback = f"AI service error: {e}"
        db.commit()
        return {"error": "AI_SERVICE_ERROR", "details": str(e)}
    except AIOutputError as e:
        log.error(f"AI output invalid grading attempt {attempt_id}: {e}")
        attempt.status = "error"
        attempt.feedback = f"AI output error: {e}"
        db.commit()
        return {"error": "AI_OUTPUT_ERROR", "details": str(e)}
    except Exception as e:
        log.exception(f"Grading service failed for attempt {attempt_id}")
        attempt.status = "error"
        attempt.feedback = "Grading service error"
        db.commit()
        return {"error": "GRADING_FAILED", "details": str(e)}
