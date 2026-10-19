"""Tes keadilan grader mock (parafrase harus lulus, jawaban kosong harus gagal).

Menjaga regresi masalah: grader lama hanya mencocokkan kata kunci mentah,
sehingga jawaban benar dengan istilah berbeda tidak pernah lulus.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.providers import MockProvider, _stem_id  # noqa: E402

MATERI = """=== MATERI KURIKULUM ===
JUDUL: Variabel & Tipe Data Dasar
TUJUAN: Learner mampu menjelaskan konsep variabel dan empat tipe data dasar Python
KATA KUNCI: variabel, int, float, str, bool, tipe dinamis
ISI:
Variabel adalah nama yang menunjuk ke sebuah nilai di memori. Di Python, variabel tidak perlu dideklarasikan dengan tipe tertentu.
Empat tipe data dasar adalah int (bilangan bulat), float (bilangan desimal), str (teks), dan bool (True atau False).
Fungsi type() menampilkan tipe suatu nilai.
Karena Python bertipe dinamis, tipe variabel mengikuti nilai terakhir yang diberikan.
SUMBER: Python Dasar - Bab 2
=== AKHIR MATERI ==="""

SYSTEM = "[TASK:eval_grade]\n" + MATERI


def _grade(answer: str) -> dict:
    p = MockProvider()
    uc = "<jawaban_learner>\n" + answer + "\n</jawaban_learner>"
    return json.loads(p.complete(SYSTEM, [{"role": "user", "content": uc}]).text)


def test_parafrase_tanpa_kata_kunci_lulus():
    """Jawaban benar dengan istilah berbeda harus lulus (masalah utama yang diperbaiki)."""
    ans = (
        'Jadi begini: bayangkan nama yang menempel pada sebuah isi di memori komputer.\n'
        'Kita tidak perlu menyatakan jenisnya lebih dulu karena Python mengenali sendiri dari isi yang kita masukkan.\n'
        'Ada empat jenis isi yang paling sering dipakai: angka utuh seperti 10, angka pecahan seperti 3.14, '
        'rangkaian huruf seperti "Budi", dan nilai benar/salah.\n'
        'Karena sifatnya yang mengikuti isi terakhir, jenis sebuah nama bisa berubah kapan saja saat kita mengganti isinya.'
    )
    out = _grade(ans)
    assert out["score"] >= 70, f"Parafrase benar harus lulus, dapat {out['score']}"


def test_jawaban_dengan_istilah_tepat_lulus_penuh():
    ans = (
        "Variabel itu wadah bernama untuk menyimpan nilai. Python tidak butuh deklarasi tipe.\n"
        "Tipe dasar: bilangan bulat (int), pecahan (float), teks (str), logika benar/salah (bool).\n"
        'Contoh: usia = 25, berat = 68.5, nama = "Andi", aktif = True. type(usia) -> <class \'int\'>.'
    )
    out = _grade(ans)
    assert out["score"] >= 90, f"Jawaban tepat harus skor tinggi, dapat {out['score']}"


def test_jawaban_kabur_tidak_lulus():
    out = _grade("Variabel itu buat nyimpen data aja sih.")
    assert out["score"] < 70, f"Jawaban dangkal tidak boleh lulus, dapat {out['score']}"


def test_nonsense_tidak_lulus():
    out = _grade("Saya suka makan nasi goreng pedas dengan telur mata sapi dan kerupuk.")
    assert out["score"] < 30, f"Jawaban nyasar harus skor sangat rendah, dapat {out['score']}"


def test_stemmer_konsisten():
    """Bentuk berimbuhan dan akarnya harus menghasilkan stem yang sama."""
    cases = [
        ("menjalankan", "dijalankan"),
        ("mengeksekusi", "eksekusi"),
        ("pemrograman", "program"),
        ("menyimpan", "simpan"),
    ]
    for a, b in cases:
        assert _stem_id(a) == _stem_id(b), f"{a} ({_stem_id(a)}) != {b} ({_stem_id(b)})"
