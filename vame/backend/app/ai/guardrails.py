"""Guardrail anti-halusinasi (SRS 4.6: FR-26..FR-29, BR-03).

Lapisan pertahanan:
1. sanitize_user_text  : membersihkan input & menghapus delimiter yang bisa dipakai 'kabur' dari kotak data.
2. detect_injection    : mendeteksi upaya mengubah instruksi sistem (FR-28) -> ditolak tanpa memanggil AI.
3. grounding di prompt : AI hanya boleh memakai MATERI; di luar lingkup wajib menjawab [OUT_OF_SCOPE] (FR-26/27).
4. postprocess_mentor  : mengganti token OUT_OF_SCOPE dengan penolakan sopan & menahan kebocoran system prompt.
"""
import re

OUT_OF_SCOPE_TOKEN = "[OUT_OF_SCOPE]"
MAX_USER_CHARS = 2000

REFUSAL_OUT_OF_SCOPE = (
    "Pertanyaan itu berada di luar materi poin bacaan yang sedang kita pelajari, jadi saya tidak "
    "bisa menjawabnya dengan akurat. Yuk kembali ke materi: coba tanyakan bagian bacaan yang "
    "masih membingungkan, atau minta contoh sederhana dari konsep di atas."
)
REFUSAL_INJECTION = (
    "Saya tidak dapat mengubah peran atau instruksi saya. Saya adalah mentor untuk materi kurikulum "
    "ini, jadi mari lanjutkan belajar: bagian mana dari bacaan yang ingin kamu dalami?"
)

_INJECTION_PATTERNS = [
    r"ab(ai|ay)kan\s+(semua\s+|seluruh\s+)?(instruksi|perintah|aturan|petunjuk)",
    r"lupakan\s+(semua\s+|seluruh\s+)?(instruksi|perintah|aturan)",
    r"ignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier|system)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+|the\s+)?(previous|prior|above|system)",
    r"(system|sistem)\s*(prompt|instruction|instruksi)",
    r"(tampilkan|tunjukkan|bocorkan|ungkapkan|reveal|show|print|repeat)\s+.{0,40}(instruksi|prompt|aturan\s+sistem|instructions)",
    r"kamu\s+(sekarang\s+)?(adalah|menjadi|bukan lagi)\s+",
    r"you\s+are\s+now\s+",
    r"\bact\s+as\b",
    r"berpura-?pura\s+(menjadi|jadi|bahwa)",
    r"pretend\s+(to\s+be|you)",
    r"developer\s+mode|mode\s+developer|\bjailbreak\b|\bDAN\s+mode\b",
    r"override\s+(your|the)\s+(rules|instructions|system)",
]
_INJECTION_RE = re.compile("|".join(f"(?:{p})" for p in _INJECTION_PATTERNS), re.IGNORECASE)

_STRIP_TAGS_RE = re.compile(r"</?\s*pesan_learner\s*>|\[TASK:[^\]]*\]|={3,}[^\n]*MATERI[^\n]*={3,}", re.IGNORECASE)
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_user_text(text: str, max_chars: int = MAX_USER_CHARS) -> str:
    text = _CTRL_RE.sub("", text or "")
    text = _STRIP_TAGS_RE.sub("", text)
    return text.strip()[:max_chars]


def detect_injection(text: str) -> bool:
    return bool(_INJECTION_RE.search(text or ""))


def postprocess_mentor(text: str, system_prompt: str) -> tuple[str, str]:
    """Return (teks_final, kind) dengan kind: normal | out_of_scope | blocked."""
    cleaned = (text or "").strip()
    if OUT_OF_SCOPE_TOKEN in cleaned:
        return REFUSAL_OUT_OF_SCOPE, "out_of_scope"
    probe = system_prompt.strip()[:60]
    if "[TASK:" in cleaned or (len(probe) > 30 and probe in cleaned):
        return REFUSAL_INJECTION, "blocked"
    return cleaned, "normal"


# ---- tokenisasi ringan (dipakai MockProvider & rubrik) ----
_STOP = set(
    """dan yang di ke dari untuk dengan atau ini itu pada adalah akan juga saya aku kamu anda apa apakah
    bagaimana mengapa kenapa bisa dapat ada tidak jika maka agar oleh sebagai dalam lebih sangat the a an
    of to in is are for and or it be how what why can you me my tolong mohon dong sih nih lah kah kok""".split()
)
_WORD_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]{1,}|\d+")


def tokenize(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text or "") if w.lower() not in _STOP}
