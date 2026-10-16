# VAME – Virtual Asisten Mentor Edukasi

Backend **FastAPI** (Python 3.10+) + frontend **React (Vite)** sesuai SRS Kelompok 3 dan desain UI "Curricula / Peta Alur Belajar".

## Menjalankan (Windows PowerShell / VS Code terminal)

### 1. Backend  (http://localhost:8000, dokumen API: /docs)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```
Database SQLite + data demo dibuat otomatis saat pertama jalan.

### 2. Frontend  (http://localhost:5173)
```powershell
cd frontend
npm install
npm run dev
```

### Akun demo
| Role | Email | Password |
|---|---|---|
| Learner | budi@vame.id | belajar123 |
| Admin | admin@vame.id | admin123 |

## Mengaktifkan AI sungguhan
Default `AI_PROVIDER=mock` (tanpa API key, cocok untuk demo/tes). Ubah di `backend/.env`:
- `AI_PROVIDER=anthropic` + `ANTHROPIC_API_KEY=...`
- `AI_PROVIDER=openai` + `OPENAI_API_KEY=...`
- `AI_PROVIDER=local` + `LOCAL_LLM_URL=http://localhost:11434/v1` (Ollama, dll.)
API key hanya dibaca dari environment (NFR-08).

## Tes
```powershell
cd backend
pytest
```

## Struktur
- `backend/app/core` – state machine & Core Engine (tanpa AI, mudah diuji)
- `backend/app/ai` – adapter LLM, prompt, guardrail anti-halusinasi / prompt-injection
- `backend/app/routers` – auth, curricula, learning, mentoring, evaluation, progress, admin (`/api/v1`)
- `frontend/src/pages` – Curricula, Dashboard, Baca, Mentoring, Evaluasi, Progress, Admin

Alur belajar: LOCKED → AVAILABLE → READING → DISCUSSING → ASSESSMENT → PASSED / NEEDS_REVIEW (skor ≥ 70, dapat diubah admin).
