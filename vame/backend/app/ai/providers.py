"""Lapisan adapter penyedia LLM (FR-34, NFR-15). Ganti penyedia cukup lewat AI_PROVIDER di .env."""
import json
import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from ..config import Settings
from .guardrails import OUT_OF_SCOPE_TOKEN, tokenize


@dataclass
class LLMResult:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


class ProviderError(Exception):
    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


class LLMProvider(ABC):
    name = "base"
    model = ""

    @abstractmethod
    def complete(
        self, system: str, messages: list[dict], *, json_mode: bool = False, max_tokens: int = 900, timeout: float = 30
    ) -> LLMResult: ...


def _post(url: str, headers: dict, body: dict, timeout: float) -> dict:
    try:
        r = httpx.post(url, headers=headers, json=body, timeout=timeout)
    except httpx.HTTPError as e:  # timeout / koneksi
        raise ProviderError(f"Koneksi ke penyedia AI gagal: {type(e).__name__}") from e
    if r.status_code >= 400:
        retryable = r.status_code in (408, 409, 429) or r.status_code >= 500
        raise ProviderError(f"Penyedia AI mengembalikan HTTP {r.status_code}", retryable=retryable)
    try:
        return r.json()
    except ValueError as e:
        raise ProviderError("Respons penyedia AI bukan JSON", retryable=True) from e


class OpenAICompatProvider(LLMProvider):
    """OpenAI Chat Completions; juga dipakai Local LLM (Ollama, LM Studio, vLLM) yang kompatibel."""

    def __init__(self, name: str, base_url: str, api_key: str, model: str):
        self.name, self.base_url, self.api_key, self.model = name, base_url.rstrip("/"), api_key, model

    def complete(self, system, messages, *, json_mode=False, max_tokens=900, timeout=30) -> LLMResult:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = _post(f"{self.base_url}/chat/completions", headers, body, timeout)
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError("Format respons OpenAI tidak dikenali") from e
        usage = data.get("usage", {})
        return LLMResult(text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), data.get("model", self.model))


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self.api_key, self.model = api_key, model

    def complete(self, system, messages, *, json_mode=False, max_tokens=900, timeout=30) -> LLMResult:
        if json_mode:
            system += "\n\nPENTING: balas HANYA dengan satu objek JSON valid, tanpa teks lain."
        body = {"model": self.model, "max_tokens": max_tokens, "system": system, "messages": messages, "temperature": 0.3}
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
        data = _post("https://api.anthropic.com/v1/messages", headers, body, timeout)
        try:
            text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
        except (KeyError, TypeError) as e:
            raise ProviderError("Format respons Anthropic tidak dikenali") from e
        usage = data.get("usage", {})
        return LLMResult(text, usage.get("input_tokens", 0), usage.get("output_tokens", 0), data.get("model", self.model))


# ---------------------------------------------------------------------------
# MockProvider: simulasi offline yang meniru kontrak LLM (untuk pengembangan & pengujian, NFR-16).
# Bukan AI sungguhan: mengutip kalimat relevan dari materi dan menilai dengan rubrik kata kunci.
# ---------------------------------------------------------------------------
_FOLLOWUP_RE = re.compile(
    r"(lebih sederhana|sederhana|contoh|ulang|maksud(nya)?|jelaskan lagi|tidak (mengerti|paham)|bingung|lanjut|"
    r"analogi|kurang jelas|simpel|explain|example)",
    re.IGNORECASE,
)


def _parse_material(system: str) -> dict:
    m = re.search(r"=== MATERI KURIKULUM.*?===\n(.*?)=== AKHIR MATERI ===", system, re.DOTALL)
    block = m.group(1) if m else ""

    def field(name: str) -> str:
        mm = re.search(rf"^{name}: (.*)$", block, re.MULTILINE)
        return mm.group(1).strip() if mm else ""

    isi = ""
    mm = re.search(r"^ISI:\n(.*?)\nSUMBER:", block, re.DOTALL | re.MULTILINE)
    if mm:
        isi = mm.group(1)
    keywords = [k.strip() for k in field("KATA KUNCI").split(",") if k.strip()]
    return {"title": field("JUDUL"), "objective": field("TUJUAN"), "keywords": keywords, "isi": isi}


def _sentences(isi: str) -> list[str]:
    out: list[str] = []
    in_code = False
    for line in isi.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        line = line.strip().lstrip("#-*> ").strip()
        if in_code or not line:
            continue
        out.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if len(s.strip()) > 15)
    return out


class MockProvider(LLMProvider):
    name = "mock"
    model = "vame-mock-1"

    def complete(self, system, messages, *, json_mode=False, max_tokens=900, timeout=30) -> LLMResult:
        task = (re.search(r"\[TASK:(\w+)\]", system) or [None, "mentor"])[1]
        mat = _parse_material(system)
        if task == "eval_question":
            text = self._question(mat)
        elif task == "eval_grade":
            text = self._grade(mat, messages[-1]["content"])
        else:
            text = self._mentor(mat, messages)
        return LLMResult(text, len(system + json.dumps(messages)) // 4, len(text) // 4, self.model)

    # -- mentor --
    def _mentor(self, mat: dict, messages: list[dict]) -> str:
        raw = messages[-1]["content"]
        q = re.sub(r"</?pesan_learner>", "", raw).strip()
        q_tokens = tokenize(q)
        mat_tokens = tokenize(" ".join([mat["title"], mat["objective"], " ".join(mat["keywords"]), mat["isi"]]))
        overlap = q_tokens & mat_tokens
        has_history = len(messages) > 1
        followup = bool(_FOLLOWUP_RE.search(q)) and len(q.split()) <= 10 and has_history
        if not overlap and not followup:
            return OUT_OF_SCOPE_TOKEN
        sents = _sentences(mat["isi"])
        ranked = sorted(sents, key=lambda s: len(tokenize(s) & q_tokens), reverse=True)
        picked = [s for s in ranked[:2] if len(tokenize(s) & q_tokens) > 0] or sents[:2]
        kws = [k for k in mat["keywords"] if tokenize(k) & q_tokens] or mat["keywords"][:2]
        return (
            f"Berdasarkan materi “{mat['title']}”: {' '.join(picked)}\n\n"
            f"Kata kunci yang perlu kamu pegang: {', '.join(kws)}.\n\n"
            f"Pertanyaan pemantik: menurutmu, bagaimana “{kws[0] if kws else mat['title']}” muncul pada contoh di bacaan? "
            "Kalau sudah merasa paham, klik “Minta Evaluasi” untuk lanjut."
        )

    # -- evaluasi --
    def _question(self, mat: dict) -> str:
        kws = mat["keywords"][:]
        random.shuffle(kws)
        a = kws[0] if kws else mat["title"]
        b = f" dan kaitannya dengan “{kws[1]}”" if len(kws) > 1 else ""
        return json.dumps(
            {
                "question": f"Berdasarkan materi “{mat['title']}”, jelaskan dengan kata-katamu sendiri apa yang dimaksud "
                f"dengan “{a}”{b}, lalu berikan satu contoh penerapannya."
            },
            ensure_ascii=False,
        )

    def _grade(self, mat: dict, user_content: str) -> str:
        m = re.search(r"<jawaban_learner>\n?(.*?)\n?</jawaban_learner>", user_content, re.DOTALL)
        ans_tokens = tokenize(m.group(1) if m else user_content)
        kws = mat["keywords"]
        hit = [k for k in kws if tokenize(k) and len(tokenize(k) & ans_tokens) >= max(1, (len(tokenize(k)) + 1) // 2)]
        mat_tokens = tokenize(mat["isi"] + " " + mat["objective"])
        coverage = min(1.0, len(hit) / max(1, min(len(kws), 4)))
        length = min(1.0, len(ans_tokens) / 20)
        relevance = min(1.0, len(ans_tokens & mat_tokens) / 10)
        score = round(100 * (0.5 * coverage + 0.25 * length + 0.25 * relevance))
        missed = [k for k in kws if k not in hit][:3]
        if score >= 70:
            fb = f"Bagus! Jawabanmu sudah mencakup {', '.join(hit) or 'inti materi'}."
            if missed:
                fb += f" Agar lebih lengkap, tinjau juga: {', '.join(missed)}."
        else:
            fb = "Jawabanmu belum cukup mencakup inti materi."
            if missed:
                fb += f" Tinjau kembali bagian tentang: {', '.join(missed)}."
            fb += " Baca ulang bacaan, lalu coba jelaskan dengan contohmu sendiri."
        return json.dumps({"score": score, "feedback": fb, "missed_points": missed}, ensure_ascii=False)


_DEFAULT_MODELS = {"openai": "gpt-4o-mini", "anthropic": "claude-sonnet-5-5", "local": "llama3.1"}


def build_provider(s: Settings) -> LLMProvider:
    name = s.ai_provider
    model = s.ai_model or _DEFAULT_MODELS.get(name, "")
    if name == "mock":
        return MockProvider()
    if name == "openai":
        if not s.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY belum diatur di environment (.env).")
        return OpenAICompatProvider("openai", "https://api.openai.com/v1", s.openai_api_key, model)
    if name == "anthropic":
        if not s.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY belum diatur di environment (.env).")
        return AnthropicProvider(s.anthropic_api_key, model)
    if name == "local":
        return OpenAICompatProvider("local", s.local_llm_url, s.local_llm_api_key, model)
    raise RuntimeError(f"AI_PROVIDER tidak dikenal: {name} (pilih mock|openai|anthropic|local)")
