"""Seed data awal.  Jalankan:  python -m app.seed   (tambahkan --reset untuk menghapus DB dulu)

Akun demo (HANYA untuk purwarupa, ganti di produksi):
  admin@vame.id  / admin123       (Curriculum Admin)
  budi@vame.id   / belajar123     (Learner, sudah punya progres demo)
"""
import sys
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .core import learning as L
from .database import Base, SessionLocal, engine
from .models import ChatSession, Enrollment, EvaluationAttempt, LearningProgress, Message, StudyActivity, User, utcnow
from .routers.curricula import import_curriculum
from .schemas import CurriculumImport
from .security import hash_password
from .seed_data import ALL_CURRICULA


def seed_all(db: Session) -> None:
    L.active_prompt(db)
    curricula = [import_curriculum(db, CurriculumImport(**d)) for d in ALL_CURRICULA]

    if not db.scalar(select(User).where(User.email == "admin@vame.id")):
        db.add(User(name="Admin Kurikulum", email="admin@vame.id", password_hash=hash_password("admin123"), role="admin"))
    budi = db.scalar(select(User).where(User.email == "budi@vame.id"))
    if not budi:
        budi = User(name="Budi Santoso", email="budi@vame.id", password_hash=hash_password("belajar123"), role="learner")
        db.add(budi)
    db.commit()
    _seed_demo_progress(db, budi, curricula[0])


def _seed_demo_progress(db: Session, budi: User, py) -> None:
    """Progres demo mirip tampilan UI: modul 1 lulus, modul 2 sedang berjalan."""
    if db.scalar(select(Enrollment).where(Enrollment.user_id == budi.id)):
        return
    db.add(Enrollment(user_id=budi.id, curriculum_id=py.id, started_at=utcnow() - timedelta(days=13)))
    db.flush()
    lps = L.ensure_progress(db, budi.id, py.id)
    pts = L.ordered_points(db, py.id)
    scores = {0: 90.0, 1: 93.0, 2: 91.5, 3: 92.0}  # modul 1 (3 poin) + modul 2 poin 1
    feedbacks = {
        3: "Kamu menunjukkan pemahaman kuat pada boolean logic (skor 92), namun perlu lebih teliti pada urutan evaluasi "
           "operator and/or (short-circuit) dan pembedaan tanda = dengan ==.",
    }
    for i, pt in enumerate(pts[:4]):
        lp = lps[pt.id]
        lp.status, lp.best_score = "PASSED", scores[i]
        db.add(
            EvaluationAttempt(
                user_id=budi.id, reading_point_id=pt.id, question=f"Jelaskan konsep utama pada materi “{pt.title}” dengan kata-katamu sendiri.",
                answer="(jawaban demo)", score=scores[i], passed=True, status="graded", graded_at=utcnow() - timedelta(days=4 - i),
                feedback=feedbacks.get(i, "Jawabanmu tepat dan mencakup inti materi."),
            )
        )
    lps[pts[4].id].status = "DISCUSSING"
    lps[pts[5].id].status = "LOCKED"
    # Sesi diskusi hari ini
    for pt, qa in (
        (pts[2], ("Apa beda / dan // pada Python?", "Berdasarkan materi: / menghasilkan float, sedangkan // adalah pembagian bulat.")),
        (pts[3], ("Kapan hasil 'and' bernilai True?", "Berdasarkan materi: and bernilai True jika kedua sisi True.")),
        (pts[4], ("Kapan memakai elif?", "Berdasarkan materi: elif memeriksa kondisi lain bila if sebelumnya False.")),
    ):
        s = ChatSession(user_id=budi.id, reading_point_id=pt.id)
        s.messages = [Message(role="user", content=qa[0]), Message(role="mentor", content=qa[1])]
        db.add(s)
    today = date.today()
    db.add_all([
        StudyActivity(user_id=budi.id, day=today, seconds=105 * 60),
        StudyActivity(user_id=budi.id, day=today - timedelta(days=1), seconds=80 * 60),
    ])
    db.commit()


if __name__ == "__main__":
    if "--reset" in sys.argv:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if session.scalar(select(User.id).limit(1)):
            print("Database sudah berisi data. Gunakan --reset untuk mengulang.")
        else:
            seed_all(session)
            print("Seed selesai. admin@vame.id/admin123 dan budi@vame.id/belajar123")
