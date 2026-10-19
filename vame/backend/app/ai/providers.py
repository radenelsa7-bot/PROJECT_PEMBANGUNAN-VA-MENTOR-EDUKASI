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

# Pertanyaan generik yang disediakan aplikasi (starter chips) — mereferensikan materi saat ini secara implisit.
# Wajib dianggap on-scope agar tidak ditolak AI sendiri.
_META_RE = re.compile(
    r"(jelaskan|beri|tunjukkan|apa)\s+(konsep\s+ini|materi\s+ini|ini|topik\s+ini|"
    r"contoh|analogi|penjelasan|kesalahan (umum|sering)|perbedaan)"
    r"|jelaskan\s+(dengan\s+)?analogi|beri\s+contoh\s+(kode\s+)?(singkat|sederhana)|"
    r"apa\s+kesalahan\s+yang\s+sering\s+terjadi",
    re.IGNORECASE,
)


_STEM_EXCEPTIONS = {
    # awalan menyerap konsonan akar (meny+s, mem+p, pem+p, men+t/d, meng+k/g)
    "pemrograman": "program", "pemrogram": "program",
    "menyimpan": "simpan", "penyimpanan": "simpan",
    "memilih": "pilih", "memakai": "pakai", "membantu": "bantu",
    "menulis": "tulis", "mengetik": "ketik", "menunjukkan": "tunjuk",
    "menampilkan": "tampil", "menyatakan": "nyata", "menyata": "nyata",
    "menggunakan": "guna", "menghasilkan": "hasil", "mengubah": "ubah",
    "mendeklarasikan": "deklarasi", "mengeksekusi": "eksekusi",
}


def _stem_id(word: str) -> str:
    """Stemming ringan Indonesia: menjalankan→jalan, pemrograman→program."""
    w = word.lower()
    root = _STEM_EXCEPTIONS.get(w)
    if root:
        w = root
    else:
        # awalan: pem/peng/peny/pen sebelum pe; terpanjang dulu
        prefixes = ("meng", "meny", "men", "mem", "pem", "peng", "peny", "pen", "me", "pe", "ber", "ter", "di", "ke")
        for pfx in prefixes:
            if w.startswith(pfx) and len(w) > len(pfx) + 1:
                w = w[len(pfx):]
                break
    # akhiran dipotong SETELAH awalan (dan juga untuk bentuk root) agar simetris:
    # 'eksekusi' dan 'mengeksekusi' sama-sama jadi 'eksekus'
    for sfx in ("nya", "lah", "kah", "pun", "kan", "an", "i"):
        if w.endswith(sfx) and len(w) - len(sfx) >= 3:
            w = w[: -len(sfx)]
            break
    return w or word.lower()


def _fuzzy_match(a: str, b: str, threshold: float = 0.80) -> bool:
    from difflib import SequenceMatcher
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= threshold


# Sinonim konseptual untuk keyword (pre‑stemmed).
_CONCEPT_SYNONYMS = {
    # --- Modul 1: sintaks dasar ---
    "interpreter": "penerjemah eksekusi jalankan baris demi baris mesin baca kode",
    "indentasi": "spasi awal baris menjorok indent blok",
    "komentar": "catatan keterangan tanda pagar diabaikan",
    "print": "cetak tampil keluaran layar output",
    "repl": "mode interaktif langsung ketik terminal",
    # --- variabel & tipe ---
    "variabel": "wadah tempat nama label penampung simpan kotak memori isi nilai",
    "int": "bulat integer utuh",
    "float": "desimal pecahan koma berkoma real",
    "str": "teks string huruf kata kalimat rangkaian karakter tulisan",
    "bool": "boolean benar salah true false logika tanda",
    "boolean": "bool benar salah true false logika",
    "tipe dinamis": "dinamis berubah mengikuti otomatis deklarasi tebak menebak sendiri",
    "nilai": "isi harga value",
    # --- I/O & operator ---
    "input": "baca masukkan pengguna user keyboard ketik",
    "output": "keluaran tampil cetak hasil",
    "konversi tipe": "ubah ganti jenis casting angka teks",
    "operator aritmetika": "tambah kurang kali bagi hitung matematika operasi sisa pangkat",
    "f-string": "format string sisip kurung kurawal awalan f",
    "modulus": "sisa bagi modulo mod",
    "operator perbandingan": "banding lebih besar kecil sama tidak",
    "ekspresi kondisional": "kondisional satu baris if else singkat",
    # --- percabangan ---
    "if": "jika apabila bila ketika",
    "else": "lain sebaliknya jika tidak",
    "elif": "lain jika else if tambahan",
    "perbandingan": "banding lebih besar kecil sama dengan",
    "kondisi": "syarat keadaan",
    "nested if": "bersarang di dalam",
    "percabangan": "cabang pilihan keputusan if else",
    "and": "dan serta kedua",
    "or": "atau salah satu",
    "not": "tidak bukan negasi",
    "truthy": "benar dianggap benar",
    "falsy": "salah dianggap salah",
    "short-circuit": "henti awal evaluasi singkat",
    # --- perulangan ---
    "for": "ulang perulangan loop iterasi",
    "while": "selama perulangan loop",
    "range": "rentang deret urutan angka",
    "break": "henti keluar stop",
    "continue": "lanjut lewati",
    "iterasi": "ulang putaran iterasi",
    "perulangan": "ulang loop iterasi",
    "loop tak hingga": "tak berhenti tanpa henti infinite",
    "kondisi berhenti": "berhenti akhir batas",
    "variabel penghitung": "hitung counter pencacah",
    # --- struktur data ---
    "list": "daftar array urutan kumpulan",
    "tuple": "tuple pasangan tetap tidak berubah",
    "dictionary": "kamus dict pasangan kunci nilai",
    "set": "himpunan unik",
    "indeks": "indeks posisi nomor urut",
    "slicing": "potong iris ambil sebagian",
    "mutable": "bisa diubah berubah",
    "immutable": "tidak bisa diubah tetap",
    "kunci": "key kunci",
    "unik": "tidak ada duplikat berbeda",
    "urutan": "urut deret",
    # --- fungsi ---
    "def": "definisi fungsi buat fungsi",
    "argumen": "argumen masukan nilai",
    "parameter": "parameter argumen masukan",
    "return": "kembali hasil keluaran",
    "scope": "lingkup jangkauan global lokal",
    "import": "impor ambil modul pustaka",
    "from import": "impor sebagian dari modul",
    "modul": "modul berkas pustaka",
    "pustaka standar": "pustaka bawaan library standard",
    # --- algoritma & analisis ---
    "algoritma": "langkah urutan cara penyelesaian",
    "pseudocode": "pseudocode kode semu deskripsi langkah",
    "flowchart": "diagram alir bagan",
    "terminator": "mulai selesai awal akhir",
    "proses": "langkah proses kerjakan",
    "kompleksitas": "kompleksitas efisiensi biaya",
    "o(n^2)": "kuadratik kuadrat n kuadrat",
    "pengurutan": "urut sorting",
    "bubble sort": "bubble gelembung tukar",
    "linear search": "cari berurutan satu per satu",
    "pertukaran": "tukar swap",
    "dekomposisi": "pecah bagi kecil",
    "sub-masalah": "bagian kecil masalah",
    # --- rekayasa kebutuhan ---
    "sdlc": "siklus pengembangan tahapan",
    "srs": "spesifikasi kebutuhan dokumen",
    "analisis": "analisa telaah",
    "perancangan": "rancang desain",
    "implementasi": "terapkan buat bangun",
    "pengujian": "uji test periksa",
    "pemeliharaan": "rawat perbaiki lanjut",
    "kebutuhan fungsional": "fitur fungsi harus bisa",
    "kebutuhan nonfungsional": "kinerja kualitas batasan",
    "keamanan": "aman security lindung",
    "performa": "kinerja cepat lambat",
}

_KW_SYNONYMS = {k: {_stem_id(w) for w in v.split()} for k, v in _CONCEPT_SYNONYMS.items()}

def _keyword_hit(keyword: str, ans_stems: set[str], ans_tokens: set[str]) -> bool:
    """Cek keyword tercakup: stemmed → sinonim → fuzzy → substring."""
    kw_tokens = tokenize(keyword)
    kw_stems = {_stem_id(t) for t in kw_tokens}
    if not kw_stems:
        return False
    # 1. Stemmed exact match
    if sum(1 for ks in kw_stems if ks in ans_stems) >= max(1, (len(kw_stems) + 1) // 2):
        return True
    # 2. Sinonim konseptual
    synonyms = _KW_SYNONYMS.get(keyword.lower(), set())
    if synonyms and (synonyms & ans_stems):
        return True
    # 3. Fuzzy + substring fallback
    for kt in kw_tokens:
        for at in ans_tokens:
            if _fuzzy_match(kt, at) or (len(kt) >= 4 and (kt in at or at in kt)):
                return True
    return False

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


def _sentence_coverage(isi: str, ans_stems: set[str]) -> float:
    """Fraksi kalimat materi yang tercakup oleh jawaban (pakai stem)."""
    sents = _sentences(isi)
    if not sents:
        return 0.0
    covered = 0
    for s in sents:
        s_tokens = tokenize(s)
        if not s_tokens:
            continue
        s_stems = {_stem_id(t) for t in s_tokens}
        overlap = len(s_stems & ans_stems)
        if overlap / len(s_stems) >= 0.40:
            covered += 1
    return covered / len(sents)


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
        q_stems = {_stem_id(t) for t in q_tokens}
        mat_tokens = tokenize(" ".join([mat["title"], mat["objective"], " ".join(mat["keywords"]), mat["isi"]]))
        mat_stems = {_stem_id(t) for t in mat_tokens}
        overlap = q_stems & mat_stems or q_tokens & mat_tokens
        has_history = len(messages) > 1
        followup = bool(_FOLLOWUP_RE.search(q)) and len(q.split()) <= 10 and has_history
        meta = bool(_META_RE.search(q))  # starter chip / pertanyaan generik tentang materi saat ini
        if not overlap and not followup and not meta:
            return OUT_OF_SCOPE_TOKEN
        sents = _sentences(mat["isi"])
        # Saat meta, paksa pilih kalimat paling representatif (intro & definisi), bukan yang kebetulan punya overlap
        if meta and not overlap:
            picked = sents[:2] if sents else [mat["objective"]]
            kws = mat["keywords"][:3]
        else:
            ranked = sorted(sents, key=lambda s: len(tokenize(s) & q_tokens), reverse=True)
            picked = [s for s in ranked[:2] if len(tokenize(s) & q_tokens) > 0] or sents[:2]
            kws = [k for k in mat["keywords"] if tokenize(k) & q_tokens] or mat["keywords"][:2]
        return (
            f"Dari materi “{mat['title']}”: {' '.join(picked)}\n\n"
            f"Kata kunci yang perlu kamu pegang: {', '.join(kws)}.\n\n"
            f"Pertanyaan pemantik: bagaimana “{kws[0] if kws else mat['title']}” muncul di contoh tadi? "
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
        ans = m.group(1) if m else user_content
        ans_tokens = tokenize(ans)
        ans_stems = {_stem_id(t) for t in ans_tokens}
        kws = mat["keywords"]
        hit = [k for k in kws if _keyword_hit(k, ans_stems, ans_tokens)]
        mat_tokens = tokenize(mat["isi"] + " " + mat["objective"])
        mat_stems = {_stem_id(t) for t in mat_tokens}
        # coverage saturasi di 3 konsep (materi sering punya 5-6 keyword;
        # menyentuh 3 sudah bukti pemahaman inti). max() agar tidak bagi-nol.
        coverage = min(1.0, len(hit) / 3)
        length = min(1.0, len(ans_tokens) / 20)
        relevance_stem = len(ans_stems & mat_stems)
        relevance_raw = len(ans_tokens & mat_tokens)
        relevance = min(1.0, max(relevance_stem, relevance_raw) / 10)
        sentence_cov = min(1.0, _sentence_coverage(mat["isi"], ans_stems))
        # Bobot: konsep 55%, relevansi 20%, kelengkapan kalimat 15%, panjang 10%.
        # Konsep dominan agar parafrase benar (istilah beda) tetap lulus,
        # sementara jawaban dangkal/kabur tetap di bawah ambang.
        score = round(100 * (
            0.55 * coverage +
            0.20 * relevance +
            0.15 * sentence_cov +
            0.10 * length
        ))
        score = max(0, min(100, score))
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
