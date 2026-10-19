# Kontribusi

Terima kasih sudah tertarik berkontribusi pada VAME (Virtual Assistant Mentor Edukasi).

## Panduan singkat

1. Fork repo, buat branch dari `main` dengan nama deskriptif (`fitur/xxx`, `fix/yyy`).
2. Pasang lingkungan pengembangan (lihat [README.md](README.md)).
3. Lakukan perubahan, jalankan tes di backend (`pytest tests/`) dan build frontend (`npm run build` di `frontend/`).
4. Buat Pull Request ke `main`. Teman tim akan review sebelum di-merge.

## Conventions

- Commit message: bahasa Indonesia, imperatif (`Tambah fitur X`, `Perbaiki bug Y`).
- Backend: Python, FastAPI, pytest. Jaga 80%+ coverage.
- Frontend: React + Vite, Tailwind-ish via `styles.css`. Hindari dependency baru kecuali perlu.
- Semua PR harus melalui review oleh setidaknya satu maintainer.

## Laporan bug / fitur baru

Gunakan template di `.github/ISSUE_TEMPLATE/`.

## Lisensi

Dibuat untuk proyek pendidikan / portfolio.
