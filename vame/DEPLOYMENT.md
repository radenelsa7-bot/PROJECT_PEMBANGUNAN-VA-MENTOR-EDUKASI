# VAME Deployment Guide

## Prasyarat
- Docker + Docker Compose
- Git
- Port 8000 (backend), 5173 (frontend)

## Deploy Staging/Prod

### 1. Clone repo
```bash
git clone <repo-url>
cd vame
```

### 2. Config environment
Backend `.env` (opsional, default mock AI):
```bash
cp backend/.env.example backend/.env
# Edit backend/.env: DATABASE_URL, AI_PROVIDER, AI_API_KEY, SECRET_KEY
```

### 3. Build & run
```bash
docker compose up -d
```

### 4. Smoke test
```bash
curl http://localhost:8000/health    # {"status":"ok"}
curl http://localhost:5173           # frontend HTML
```

### 5. Login demo
Frontend: http://localhost:5173  
User: `budi@vame.id` / `belajar123`

## Rollback
```bash
git log --oneline                    # pilih commit stabil
git checkout <commit-hash>
docker compose down
docker compose up -d --build
```

## Monitoring
- Backend logs: `docker compose logs -f backend`
- Frontend logs: `docker compose logs -f frontend`
- DB: `backend/vame.db` (SQLite, backup manual)

## Production Hardening
1. Ganti `SECRET_KEY` di `.env` (backend/app/config.py)
2. Set `AUTO_SEED=0` (matikan data demo)
3. HTTPS reverse proxy (nginx/Caddy)
4. PostgreSQL ganti SQLite: `DATABASE_URL=postgresql://...`
5. AI provider: OpenAI/Azure/Ollama (set `AI_PROVIDER`, `AI_API_KEY`)

## CI/CD
GitHub Actions (`.github/workflows/ci.yml`):
- Push ke `main` → pytest + smoke test (docker health check)
- PR → pytest only

## Troubleshooting
- Port conflict: ubah `ports:` di `docker-compose.yml`
- DB reset: `rm backend/vame.db && docker compose restart backend`
- Build cache: `docker compose build --no-cache`
