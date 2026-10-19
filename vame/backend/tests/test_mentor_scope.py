"""Tes: pertanyaan starter generik tidak boleh ditolak, yang nyata di luar materi tetap ditolak.

Menjaga regresi masalah: aplikasi menawarkan chip pertanyaan "Jelaskan konsep ini dengan
analogi sederhana", tetapi guardrail lingkup menolaknya karena tidak ada irisan kata kunci
materi. Chip bawaan aplikasi wajib dianggap on-scope.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.providers import MockProvider  # noqa: E402
from app.ai.guardrails import OUT_OF_SCOPE_TOKEN  # noqa: E402

MATERI = """=== MATERI KURIKULUM (satu-satunya sumber kebenaran) ===
JUDUL: Boolean & Operator Logika
TUJUAN: Learner mampu menyusun ekspresi boolean dengan operator perbandingan dan and, or, not.
KATA KUNCI: boolean, operator perbandingan, and, or, not, short-circuit
ISI:
Nilai boolean hanya True atau False. Operator perbandingan menghasilkan boolean: ==, !=, <, >, <=, >=.
Operator and benar bila kedua operand benar; or benar bila salah satu benar; not membalik nilai.
Ekspresi dapat dievaluasi short-circuit: and berhenti jika kiri False, or berhenti jika kiri True.
SUMBER: Python Dasar - Bab 3
=== AKHIR MATERI ==="""

SYSTEM = "[TASK:mentor]\n" + MATERI


def _ask(question: str) -> str:
    p = MockProvider()
    r = p.complete(SYSTEM, [{"role": "user", "content": f"<pesan_learner>\n{question}\n</pesan_learner>"}])
    return r.text


def test_starter_generik_dijawab_bukan_out_of_scope():
    out = _ask("Jelaskan konsep ini dengan analogi sederhana")
    assert OUT_OF_SCOPE_TOKEN not in out, "Starter generik wajib dijawab, bukan ditolak"
    assert "boolean" in out.lower() or "operator" in out.lower()


def test_stainer_beri_contoh_dijawab():
    out = _ask("Beri contoh kode singkat")
    assert OUT_OF_SCOPE_TOKEN not in out


def test_starter_kesalahan_dijawab():
    out = _ask("Apa kesalahan yang sering terjadi?")
    assert OUT_OF_SCOPE_TOKEN not in out


def test_pertanyaan_kontekstual_dengan_kata_kunci_dijawab():
    out = _ask('Jelaskan "boolean" dengan analogi sederhana')
    assert OUT_OF_SCOPE_TOKEN not in out
    assert "boolean" in out.lower()


def test_benar_benar_di_luar_materi_tetap_ditolak():
    out = _ask("Bagaimana cara membuat rendang padang yang empuk?")
    assert OUT_OF_SCOPE_TOKEN in out


def test_pertanyaan_teknologi_lain_ditolak():
    out = _ask("Jelaskan cara deploy aplikasi ke AWS dengan Kubernetes")
    assert OUT_OF_SCOPE_TOKEN in out
