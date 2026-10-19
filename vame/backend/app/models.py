"""Entitas data (SRS Appendix B.2) + tabel pendukung audit (NFR-04)."""
import json
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    """UTC naive agar konsisten di SQLite maupun PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="learner")  # learner | admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Curriculum(Base):
    __tablename__ = "curricula"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)  # mis. PY-ALG-101
    title: Mapped[str] = mapped_column(String(200))
    short_name: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(String(40), default="Dasar")
    topic_label: Mapped[str] = mapped_column(String(80), default="")
    est_hours: Mapped[int] = mapped_column(Integer, default=10)
    mentor_name: Mapped[str] = mapped_column(String(80), default="Tutor AI VAME")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    modules: Mapped[list["Module"]] = relationship(
        back_populates="curriculum", order_by="Module.order", cascade="all, delete-orphan"
    )


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("curriculum_id", "order"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(ForeignKey("curricula.id"))
    title: Mapped[str] = mapped_column(String(200))
    label: Mapped[str] = mapped_column(String(60), default="MODUL")
    order: Mapped[int] = mapped_column(Integer)

    curriculum: Mapped[Curriculum] = relationship(back_populates="modules")
    reading_points: Mapped[list["ReadingPoint"]] = relationship(
        back_populates="module", order_by="ReadingPoint.order", cascade="all, delete-orphan"
    )


class ReadingPoint(Base):
    __tablename__ = "reading_points"
    __table_args__ = (UniqueConstraint("module_id", "order"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)  # isi_materi (konten poin bacaan)
    objective: Mapped[str] = mapped_column(Text, default="")  # tujuan pembelajaran
    keywords_json: Mapped[str] = mapped_column(Text, default="[]")
    references: Mapped[str] = mapped_column(Text, default="")  # sumber_referensi (SRS)
    order: Mapped[int] = mapped_column(Integer)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)  # sesuai ERD

    module: Mapped[Module] = relationship(back_populates="reading_points")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="reading_point", cascade="all, delete-orphan"
    )

    @property
    def keywords(self) -> list[str]:
        return json.loads(self.keywords_json or "[]")

    @keywords.setter
    def keywords(self, value: list[str]) -> None:
        self.keywords_json = json.dumps(value, ensure_ascii=False)


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("user_id", "curriculum_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    curriculum_id: Mapped[int] = mapped_column(ForeignKey("curricula.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | completed | dropped
    progress_persen: Mapped[float] = mapped_column(Float, default=0.0)  # sesuai ERD
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # tgl_selesai (ERD)


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    __table_args__ = (UniqueConstraint("user_id", "reading_point_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reading_point_id: Mapped[int] = mapped_column(ForeignKey("reading_points.id"))
    status: Mapped[str] = mapped_column(String(20), default="LOCKED")
    best_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class StateTransitionLog(Base):
    """Jejak perubahan status (NFR-04) termasuk percobaan transisi tidak valid (FR-15)."""

    __tablename__ = "state_transition_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reading_point_id: Mapped[int] = mapped_column(ForeignKey("reading_points.id"))
    from_status: Mapped[str] = mapped_column(String(20))
    trigger: Mapped[str] = mapped_column(String(40))
    to_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    valid: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ChatSession(Base):
    """Session mentoring/evaluasi. FK ke enrollment (bukan langsung user) sesuai ERD."""
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.id"), index=True)
    reading_point_id: Mapped[int] = mapped_column(ForeignKey("reading_points.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | ended
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    evaluation_rel: Mapped["Evaluation | None"] = relationship(back_populates="session_rel")

    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", order_by="Message.id", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # user | mentor
    content: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20), default="normal")  # normal | out_of_scope | blocked
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class EvaluationAttempt(Base):
    __tablename__ = "evaluation_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reading_point_id: Mapped[int] = mapped_column(ForeignKey("reading_points.id"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="pending")  # pending | graded
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)




class Question(Base):
    """Soal evaluasi untuk setiap poin bacaan (FR-11)."""
    
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    reading_point_id: Mapped[int] = mapped_column(ForeignKey("reading_points.id"))
    question_text: Mapped[str] = mapped_column(Text)
    answer_key: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(20), default="essay")  # essay | multiple_choice
    weight: Mapped[int] = mapped_column(Integer, default=1)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    reading_point: Mapped[ReadingPoint] = relationship(back_populates="questions")


class Evaluation(Base):
    """Sesi evaluasi lengkap (ERD table evaluation)."""
    
    __tablename__ = "evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback_ai: Mapped[str] = mapped_column(Text, default="")
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    session_rel: Mapped[ChatSession] = relationship(back_populates="evaluation_rel")
    answers: Mapped[list["Answer"]] = relationship(back_populates="evaluation", cascade="all, delete-orphan")


class Answer(Base):
    """Jawaban evaluasi per soal (ERD table answer)."""
    
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    student_answer: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer, default=0)
    feedback: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    evaluation: Mapped[Evaluation] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship()


class AIProviderConfig(Base):
    """Konfigurasi provider & model AI (ERD: ai_model_config)."""
    __tablename__ = "ai_model_config"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(30))  # openai | anthropic | ollama
    model_name: Mapped[str] = mapped_column(String(80))
    api_key_hint: Mapped[str] = mapped_column(String(100), default="")
    base_url: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PromptConfig(Base):
    __tablename__ = "prompt_configs"
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(Integer, unique=True)
    content: Mapped[str] = mapped_column(Text)  # isi_system_prompt
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(30))  # mentor | eval_question | eval_grade
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(80))
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str] = mapped_column(String(300), default="")
    prompt: Mapped[str] = mapped_column(Text, default="")  # audit prompt (NFR-04)
    response: Mapped[str] = mapped_column(Text, default="")  # audit respons (NFR-04)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class AppSetting(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class StudyActivity(Base):
    """Durasi belajar harian (untuk kartu 'Aktivitas hari ini')."""

    __tablename__ = "study_activity"
    __table_args__ = (UniqueConstraint("user_id", "day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    day: Mapped[date] = mapped_column(Date)
    seconds: Mapped[int] = mapped_column(Integer, default=0)
