"""Skema request/response (Pydantic) - SRS 2.5, FR-29."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORM):
    id: int
    name: str
    email: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


# ---------- Kurikulum ----------
class ReadingPointIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
    references: str = Field(min_length=1, description="Sumber materi wajib dicantumkan (BR-05)")
    order: int = Field(ge=1)

    @field_validator("keywords")
    @classmethod
    def _clean_keywords(cls, v: list[str]) -> list[str]:
        cleaned = [k.strip() for k in v if k.strip()]
        if not cleaned:
            raise ValueError("keywords tidak boleh kosong")
        return cleaned


class ReadingPointUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    objective: str | None = Field(default=None, min_length=1)
    keywords: list[str] | None = None
    references: str | None = Field(default=None, min_length=1)
    order: int | None = Field(default=None, ge=1)


class ModuleIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    label: str = Field(default="MODUL", max_length=60)
    order: int = Field(ge=1)


class ModuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    label: str | None = None
    order: int | None = Field(default=None, ge=1)


class CurriculumIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=3, max_length=200)
    short_name: str = ""
    description: str = ""
    level: str = "Dasar"
    topic_label: str = ""
    est_hours: int = Field(default=10, ge=1)
    mentor_name: str = "Tutor AI VAME"


class CurriculumUpdate(BaseModel):
    title: str | None = None
    short_name: str | None = None
    description: str | None = None
    level: str | None = None
    topic_label: str | None = None
    est_hours: int | None = Field(default=None, ge=1)
    mentor_name: str | None = None
    is_active: bool | None = None


class ModuleImport(ModuleIn):
    reading_points: list[ReadingPointIn] = Field(min_length=1)


class CurriculumImport(CurriculumIn):
    modules: list[ModuleImport] = Field(min_length=1)


class EnrollmentIn(BaseModel):
    curriculum_id: int


# ---------- Question ----------
class QuestionIn(BaseModel):
    question_text: str = Field(min_length=1)
    answer_key: str = Field(min_length=1)
    question_type: str = Field(default="essay", pattern="^(essay|multiple_choice)$")
    weight: int = Field(default=1, ge=1, le=10)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class QuestionOut(ORM):
    id: int
    reading_point_id: int
    question_text: str
    answer_key: str
    question_type: str
    weight: int
    difficulty: str
    created_at: datetime


# ---------- AI Provider Config ----------
class AIProviderConfigIn(BaseModel):
    provider: str = Field(min_length=1, max_length=30)
    model_name: str = Field(min_length=1, max_length=80)
    api_key_hint: str = Field(default="", max_length=100)
    base_url: str = Field(default="", max_length=255)
    is_active: bool = False
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1)


class AIProviderConfigOut(ORM):
    id: int
    provider: str
    model_name: str
    api_key_hint: str
    base_url: str
    is_active: bool
    temperature: float
    max_tokens: int
    created_at: datetime


# ---------- Evaluation & Assessment ----------
class AnswerIn(BaseModel):
    question_text: str = Field(min_length=1)
    answer_text: str = Field(min_length=1)


class EvaluationAttemptOut(ORM):
    id: int
    user_id: int
    reading_point_id: int
    status: str
    score: float | None = None
    feedback: str | None = None
    passed: bool | None = None
    created_at: datetime
    graded_at: datetime | None = None


class EvaluationResultOut(BaseModel):
    attempt_id: int
    status: str
    score: float | None = None
    passed: bool
    feedback: str


# ---------- Mentoring ----------
class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Pesan tidak boleh kosong")
        return v


class MessageOut(ORM):
    id: int
    role: str
    content: str
    kind: str
    flagged: bool
    created_at: datetime


class FlagIn(BaseModel):
    reason: str = Field(default="", max_length=500)


# ---------- Evaluasi (model lama Evaluation+Answer) ----------
class AnswerLegacyOut(ORM):
    id: int
    evaluation_id: int
    question_id: int
    student_answer: str
    score: int
    feedback: str


class EvaluationLegacyOut(ORM):
    id: int
    session_id: int
    score: float
    is_passed: bool
    feedback_ai: str
    evaluated_at: datetime


# Keluaran terstruktur dari AI (FR-29)
class AIQuestion(BaseModel):
    question: str = Field(min_length=10, max_length=800)


class AIGrade(BaseModel):
    score: int = Field(ge=0, le=100)
    feedback: str = Field(min_length=3, max_length=1500)
    missed_points: list[str] = Field(default_factory=list)


# ---------- Admin ----------
class PromptConfigIn(BaseModel):
    content: str = Field(min_length=30)


class SettingsIn(BaseModel):
    pass_threshold: int = Field(ge=1, le=100)


class HeartbeatIn(BaseModel):
    seconds: int = Field(ge=1, le=120)
