# Project Management Plan – Virtual Asisten Mentor Edukasi (VAME)

Dokumen ini dibuat sebagai acuan pengelolaan proyek yang melengkapi issue-issue yang sudah ada di repositori. Issue yang sudah ada sudah mencakup kickoff, requirement gathering, UX/UI, arsitektur, backend/frontend implementation, QA/UAT, keamanan, dan deployment. Karena itu, file ini hanya menambahkan komponen manajemen proyek yang masih kurang, yaitu milestone, sprint, label, alur kerja, dan pembagian tanggung jawab.

## 1. Informasi Proyek
- Nama Proyek: Virtual Asisten Mentor Edukasi (VAME)
- Repository: radenelsa7-bot/PROJECT_PEMBANGUNAN-VA-MENTOR-EDUKASI
- Domain: EdTech / AI-powered mentoring
- Platform: Backend API berbasis Python dan AI API
- Fokus utama: learning path terstruktur, mentoring berbasis AI, evaluasi pemahaman, dan anti-halusinasi
- Sumber acuan utama: SRS VAME dan daftar issue yang sudah dibuat

## 2. Struktur Tim dan Assign

| Peran | Nama | Tanggung Jawab Utama |
|---|---|---|
| Project Manager | radenelsa7-bot | koordinasi tim, milestone, sprint, stakeholder review, escalasi risiko |
| Frontend Developer | amarasylviyuliana | UI/UX, halaman pembelajaran, dashboard, interaksi user |
| Backend Developer | RifqyWildan | API, database, logika bisnis, learning engine, integrasi backend |
| System Analyst | Adhiryansyah | kebutuhan bisnis, analisis alur, validasi fungsi dengan SRS |
| QA Tester | NabilahAsanaAlecia | pengujian fungsional, UAT, bug report, validasi kualitas jawaban AI |

Catatan:
- Penugasan di atas adalah pembagian peran utama.
- Beberapa pekerjaan dapat dilakukan secara lintas peran sesuai kebutuhan sprint.

## 3. Milestone Proyek

| Milestone | Fokus | Waktu Target | Deliverable |
|---|---|---|---|
| M1. Kickoff & Analysis | project alignment, business analysis, ruang lingkup | Sprint 1 | SRS, scope, daftar kebutuhan, timeline |
| M2. Design & Architecture | wireframe, desain sistem, arsitektur teknis, model data | Sprint 2 | UX flow, ERD, API contract, arsitektur aplikasi |
| M3. Foundation & Setup | repo structure, CI/CD, environment, base project | Sprint 2 | repositori siap kerja, pipeline dasar |
| M4. Core Implementation | backend core, frontend core, learning path, mentoring | Sprint 3–4 | fitur utama aplikasi berjalan |
| M5. AI & Integration | prompt design, knowledge base, AI integration, anti-halusinasi | Sprint 4 | model AI terintegrasi, guardrail, evaluasi |
| M6. QA, UAT, & Fixes | pengujian end-to-end, revisi, perbaikan bug | Sprint 5 | laporan QA, UAT, perbaikan |
| M7. Deployment & Retrospective | staging, production, dokumentasi akhir, review | Sprint 6 | release, dokumentasi, retrospective |

## 4. Sprint Planning

### Sprint 1 – Kickoff & Requirement Alignment
Tujuan:
- finalisasi ruang lingkup
- validasi kebutuhan sesuai SRS
- menentukan prioritas fitur
- menyepakati jadwal dan peran

Output utama:
- SRS dan ruang lingkup final
- daftar issue prioritas
- pembagian tugas per role

Issue terkait yang sudah ada:
- Project Kickoff & Planning
- Requirement Gathering & Business Analysis

### Sprint 2 – Design & Architecture
Tujuan:
- merancang flow pengguna
- menentukan struktur API
- menyusun model data
- menyiapkan environment dan repositori

Output utama:
- UX/UI wireframe dan design system
- technical feasibility
- repo structure & CI/CD setup
- API schema dan model data

Issue terkait yang sudah ada:
- UX/UI Wireframes & Design System
- Technical Feasibility & High-Level Architecture
- Repo Structure & CI/CD Setup
- API & Data Model Design

### Sprint 3 – Core Development Iterasi 1
Tujuan:
- membangun modul inti backend dan frontend
- menyusun learning path dan flow utama

Output utama:
- backend core implementation
- frontend core implementation
- prototipe fitur utama

Issue terkait yang sudah ada:
- Backend — Core Implementation (Iterasi 1)
- Frontend — Core Implementation (Iterasi 1)
- Backend & Frontend Core Implementation (8 hari)
- Backend Core Implementation (sub-task)
- Frontend Core Implementation (sub-task)

### Sprint 4 – AI Engine & Knowledge Base
Tujuan:
- integrasi AI mentor
- knowledge base / sumber materi
- prompt design dan persona mentor
- evaluasi kualitas jawaban

Output utama:
- persona AI mentor siap pakai
- prompt design dan rule-based guardrail
- materi kurikulum terstruktur
- log evaluasi jawaban AI

Issue terkait yang sudah ada:
- Persona VA mentor & prompt design
- Knowledge base / sumber materi
- Evaluasi kualitas jawaban VA
- Desain kurikulum & konten edukasi

### Sprint 5 – QA, Security, dan UAT
Tujuan:
- pengecekan kualitas aplikasi
- evaluasi keamanan dan privasi data
- validasi terhadap kebutuhan pengguna dan stakeholder

Output utama:
- laporan QA
- hasil UAT
- daftar perbaikan
- kebijakan keamanan dan privasi data

Issue terkait yang sudah ada:
- Keamanan, privasi data & kebijakan penggunaan
- End-to-End Testing & QA
- UAT & Stakeholder Demo
- Bug fixing / revisi hasil UAT (sebelum Deployment)

### Sprint 6 – Deployment & Release Readiness
Tujuan:
- validasi final
- deploy ke staging/production
- ringkasan hasil proyek dan pembelajaran

Output utama:
- deployment release
- release log
- post-release retrospective

Issue terkait yang sudah ada:
- Deployment — Staging to Production
- [Final] Post-release Review & Retrospective

## 5. Label yang Disarankan di GitHub

Label yang sudah ada di repo saat ini:
- bug
- documentation

Label yang belum ada dan perlu ditambahkan agar pengelolaan proyek lebih rapi (hanya label yang belum tercakup di issue yang ada):

| Label | Kegunaan |
|---|---|
| backend | semua pekerjaan backend |
| frontend | semua pekerjaan frontend |
| ui/ux | task desain antarmuka dan pengalaman pengguna |
| architecture | pekerjaan arsitektur dan teknologi |
| ai | integrasi model AI, prompt, evaluation |
| security | keamanan, privacy, auth, data protection |
| qa | pengujian, validasi, regression test |
| deployment | release, staging, production, rollback |
| research | analisis kebutuhan, riset teknologi, referensi |
| ready-for-review | task siap ditinjau |
| blocked | task tertunda karena dependency |
| needs-uat | fitur sudah selesai, menunggu UAT |

Catatan:
- Label `bug` dan `documentation` tidak perlu ditambahkan kembali karena sudah ada.
- Label tambahan di atas hanya menutup celah pengelolaan sprint dan workflow issue.

## 6. Workflow Issue Board

Status default yang disarankan:
- Backlog
- In Progress
- Review
- Needs UAT
- Done
- Blocked

Prinsip pengelolaan:
- issue baru masuk ke Backlog
- tugas dikerjakan oleh owner sesuai role
- saat selesai disimpan dalam `ready-for-review`
- task yang menunggu validasi stakeholder diberi label `needs-uat`
- issue yang tertunda karena dependency diberi `blocked`

## 7. Definition of Done (DoD)
Sebuah task dianggap selesai bila:
- fitur atau tugas sudah sesuai dengan SRS dan kebutuhan bisnis
- kode terintegrasi dengan repo dan tidak menimbulkan error dasar
- untuk fitur AI, hasil sudah sesuai dengan materi kurikulum dan tidak melanggar guardrail
- dilakukan testing minimal untuk area yang terdampak
- dokumentasi teknis atau catatan implementasi sudah ada bila diperlukan
- status issue ditutup atau dipindahkan ke milestone berikutnya dengan bukti validasi

## 8. Risiko Utama dan Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| ketersediaan API AI | gangguan fungsional mentoring | gunakan adapter, retry, fallback, dan monitoring |
| kualitas prompt tidak konsisten | jawaban AI berbahaya/halusinasi | prompt guardrail + evaluasi manual |
| perubahan kebutuhan user | revisi besar | review sprint dan validasi SRS |
| keamanan data pengguna | pelanggaran privasi | enkripsi, auth, log audit, kebijakan privasi |
| keterlambatan tim | target sprint terganggu | prioritisasi must-have dan review progres mingguan |

## 9. Escalation & Reporting
- Project Manager memimpin rapat progres mingguan.
- Setiap sprint diakhiri dengan review deliverable dan status issue.
- Jika ada blocker yang menghambat milestone, PM akan eskalasi ke stakeholder sebelum batas sprint.
- Setiap issue yang sudah selesai harus terhubung ke milestone terkait dan label status yang jelas.

## 10. Ringkasan Implementasi Manajemen

Proyek ini sudah memiliki issue yang cukup lengkap untuk ranah produk dan teknis. Yang masih perlu dipenuhi secara manajerial adalah:
1. milestone yang jelas per tahapan
2. sprint planning yang terstruktur
3. label tambahan untuk pengelolaan workflow
4. pembagian ownership yang konsisten
5. definition of done dan escalation flow

Dengan komponen tersebut, pengelolaan proyek VAME akan lebih terukur, konsisten, dan siap diukur progresnya dari sprint ke sprint.

---

Dokumen ini merupakan panduan manajemen proyek internal yang selaras dengan SRS dan daftar issue yang sudah ada di repository.
