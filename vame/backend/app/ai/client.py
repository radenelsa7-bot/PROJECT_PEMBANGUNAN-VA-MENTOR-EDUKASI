"""Klien AI: timeout, retry+backoff, validasi keluaran terstruktur, pencatatan penggunaan
(FR-29, FR-36, FR-37, NFR-04)."""
import json
import re
import time
from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from ..config import settings
from ..models import AIUsageLog
from .providers import LLMProvider, LLMResult, ProviderError, build_provider

T = TypeVar("T", bound=BaseModel)


class AIServiceError(Exception):
    """AI API tidak tersedia setelah retry (HTTP 503)."""


class AIOutputError(Exception):
    """Keluaran AI tidak valid terhadap skema setelah retry (HTTP 502)."""


class AIClient:
    def __init__(self, provider: LLMProvider, max_retries: int = 2, timeout: float = 30, backoff_base: float = 0.5):
        self.provider, self.max_retries, self.timeout, self.backoff_base = provider, max_retries, timeout, backoff_base

    # -- pencatatan pakai session terpisah agar tetap tersimpan walau transaksi utama dibatalkan --
    def _log(self, db: Session, *, user_id, kind, system, messages, result: LLMResult | None, latency_ms, error=""):
        with Session(bind=db.get_bind()) as s:
            s.add(
                AIUsageLog(
                    user_id=user_id,
                    kind=kind,
                    provider=self.provider.name,
                    model=result.model if result else self.provider.model,
                    tokens_in=result.tokens_in if result else 0,
                    tokens_out=result.tokens_out if result else 0,
                    latency_ms=latency_ms,
                    success=result is not None and not error,
                    error=error[:300],
                    prompt=system + "\n---\n" + json.dumps(messages, ensure_ascii=False),
                    response=result.text if result else "",
                )
            )
            s.commit()

    def complete(self, db: Session, *, kind: str, system: str, messages: list[dict], json_mode=False, user_id=None) -> LLMResult:
        last_err = "tidak diketahui"
        for attempt in range(self.max_retries + 1):
            t0 = time.perf_counter()
            try:
                res = self.provider.complete(system, messages, json_mode=json_mode, timeout=self.timeout)
            except ProviderError as e:
                last_err = str(e)
                self._log(db, user_id=user_id, kind=kind, system=system, messages=messages, result=None,
                          latency_ms=int((time.perf_counter() - t0) * 1000), error=last_err)
                if not e.retryable or attempt == self.max_retries:
                    break
                time.sleep(self.backoff_base * (2**attempt))  # exponential backoff
                continue
            self._log(db, user_id=user_id, kind=kind, system=system, messages=messages, result=res,
                      latency_ms=int((time.perf_counter() - t0) * 1000))
            return res
        raise AIServiceError(last_err)

    def complete_structured(self, db: Session, *, kind: str, system: str, messages: list[dict], schema: type[T], user_id=None) -> T:
        last = ""
        for _ in range(2):  # 1x ulang bila format tidak valid (FR-29)
            res = self.complete(db, kind=kind, system=system, messages=messages, json_mode=True, user_id=user_id)
            try:
                return schema.model_validate(_extract_json(res.text))
            except (ValueError, ValidationError) as e:
                last = str(e)[:200]
        raise AIOutputError(f"Keluaran AI tidak sesuai skema: {last}")


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("tidak ada objek JSON")
    return json.loads(m.group(0))


@lru_cache
def get_ai_client() -> AIClient:
    return AIClient(
        build_provider(settings),
        max_retries=settings.ai_max_retries,
        timeout=settings.ai_timeout,
        backoff_base=settings.ai_backoff_base,
    )
