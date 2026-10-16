import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as _HTTPException  # noqa: F401
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from .ai.client import AIOutputError, AIServiceError
from .config import settings
from .core import learning as L
from .database import Base, SessionLocal, engine
from .models import Curriculum
from .routers import admin, auth, curricula, evaluation, learning, mentoring, progress

DESCRIPTION = """
**VAME** - Virtual Asisten Mentor Edukasi. Backend REST API (FastAPI) dengan state machine status belajar,
mentor AI yang dibatasi materi kurikulum (guardrail anti-halusinasi), evaluasi pemahaman, dan monitoring admin.

Klik **Authorize** lalu tempel `access_token` dari `POST /api/v1/auth/login`.
"""

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        L.active_prompt(db)
        if os.getenv("AUTO_SEED", "1") == "1" and not db.scalar(select(Curriculum.id).limit(1)):
            from .seed import seed_all

            seed_all(db)  # data demo; matikan dengan AUTO_SEED=0
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", description=DESCRIPTION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

for r in (auth, curricula, learning, mentoring, evaluation, progress, admin):
    app.include_router(r.router, prefix=settings.api_prefix)


@app.exception_handler(AIServiceError)
async def _ai_unavailable(_: Request, exc: AIServiceError):  # FR-36, NFR-05
    return JSONResponse(
        status_code=503,
        content={"detail": {"code": "AI_UNAVAILABLE", "message": "Mentor AI sedang tidak tersedia. Status belajarmu tidak berubah, silakan coba lagi.", "reason": str(exc)}},
    )


@app.exception_handler(AIOutputError)
async def _ai_bad_output(_: Request, exc: AIOutputError):  # FR-29
    return JSONResponse(
        status_code=502,
        content={"detail": {"code": "AI_BAD_OUTPUT", "message": "Respons mentor AI tidak valid. Status belajarmu tidak berubah, silakan coba lagi.", "reason": str(exc)}},
    )


@app.get("/health", tags=["0. Sistem"])
def health():
    return {"status": "ok"}


@app.get(f"{settings.api_prefix}/meta", tags=["0. Sistem"])
def meta():
    return {"app": "VAME", "ai_provider": settings.ai_provider, "api_prefix": settings.api_prefix}


