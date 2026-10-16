import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { get, post } from "../api.js";
import { Modal, StatusBadge, pointRoute } from "./common.jsx";

function initials(name = "") {
  return name.split(" ").filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}

export default function Navbar() {
  const { user, selected, selectedId, logout } = useAuth();
  const nav = useNavigate();
  const { pathname } = useLocation();
  const learner = user.role === "learner";

  const [q, setQ] = useState("");
  const [hits, setHits] = useState(null);
  const [menu, setMenu] = useState(null); // 'bell' | 'user'
  const [help, setHelp] = useState(false);
  const [reco, setReco] = useState(null);
  const boxRef = useRef(null);

  // Pencarian topik (hanya judul & status; isi materi terkunci tidak bocor)
  useEffect(() => {
    if (!learner || q.trim().length < 2) return setHits(null);
    const t = setTimeout(() => get(`/search?q=${encodeURIComponent(q.trim())}`).then(setHits).catch(() => setHits([])), 300);
    return () => clearTimeout(t);
  }, [q, learner]);

  // Catat durasi belajar tiap 30 detik saat tab aktif
  useEffect(() => {
    if (!learner) return;
    const t = setInterval(() => {
      if (document.visibilityState === "visible") post("/progress/heartbeat", { seconds: 30 }).catch(() => {});
    }, 30000);
    return () => clearInterval(t);
  }, [learner]);

  useEffect(() => {
    const close = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) {
        setMenu(null);
        setHits(null);
      }
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const openBell = () => {
    setMenu(menu === "bell" ? null : "bell");
    if (selectedId) get(`/learning-path/${selectedId}`).then((p) => setReco(p)).catch(() => {});
  };

  const is = (p) => pathname === p || pathname.startsWith(p + "/");
  const curActive = is("/curricula") || is("/catalog") || is("/reading") || is("/evaluation");

  return (
    <header className="nav" ref={boxRef}>
      <div className="nav-inner">
        <Link to="/" className="brand">
          <span className="brand-mark">V</span> VAME
        </Link>

        {learner && (
          <div className="search">
            <input
              placeholder="Cari topik, fungsi python, modul…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Cari topik"
            />
            {hits && (
              <div className="search-results">
                {hits.length === 0 && <div className="search-item" style={{ color: "var(--muted)" }}>Tidak ada topik yang cocok.</div>}
                {hits.map((h) => (
                  <button
                    key={h.id}
                    className="search-item"
                    disabled={h.status === "LOCKED"}
                    onClick={() => {
                      setQ("");
                      setHits(null);
                      nav(pointRoute(h.id, h.status));
                    }}
                  >
                    <span>{h.title}</span>
                    <small>{h.status === "LOCKED" ? "🔒 Terkunci" : h.module}</small>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <nav className="nav-links">
          {learner ? (
            <>
              <Link to="/dashboard" className={is("/dashboard") ? "active" : ""}>Dashboard</Link>
              <Link to="/curricula" className={curActive ? "active" : ""}>Curricula</Link>
              <Link to="/mentoring" className={is("/mentoring") ? "active" : ""}>Mentoring Session</Link>
              <Link to="/progress" className={is("/progress") ? "active" : ""}>Progress</Link>
            </>
          ) : (
            <Link to="/admin" className="active">Panel Admin</Link>
          )}
        </nav>

        <div className="nav-right">
          {learner && (
            <button className="btn-ai" onClick={() => nav("/mentoring")}>
              ✨ Ask AI Mentor
            </button>
          )}
          <span className="role-pill">
            <i /> Role: {learner ? "Learner" : "Admin"}
          </span>
          {learner && (
            <div style={{ position: "relative" }}>
              <button className="icon-btn" aria-label="Notifikasi" onClick={openBell}>
                🔔
              </button>
              {menu === "bell" && (
                <div className="popover">
                  <h4>Langkah berikutnya</h4>
                  {reco ? (
                    <>
                      <p>{reco.recommendation}</p>
                      {reco.current && (
                        <>
                          <div style={{ marginTop: 8 }}><StatusBadge status={reco.current.status} /></div>
                          <button className="link-btn" onClick={() => { setMenu(null); nav(pointRoute(reco.current.id, reco.current.status)); }}>
                            Lanjutkan →
                          </button>
                        </>
                      )}
                    </>
                  ) : (
                    <p>Pilih kurikulum untuk melihat rekomendasi.</p>
                  )}
                </div>
              )}
            </div>
          )}
          <button className="icon-btn" aria-label="Bantuan" onClick={() => setHelp(true)} style={{ color: "var(--red)" }}>
            ❓
          </button>
          <div className="user-box">
            <button className="avatar" onClick={() => setMenu(menu === "user" ? null : "user")} aria-label="Menu akun">
              {initials(user.name)}
            </button>
            <div className="user-meta">
              <b>{user.name}</b>
              <span>{learner ? `Progres: ${selected?.percent ?? 0}%` : "Curriculum Admin"}</span>
            </div>
            {menu === "user" && (
              <div className="popover" style={{ width: 220 }}>
                <h4>{user.email}</h4>
                <button
                  className="btn danger"
                  style={{ width: "100%", marginTop: 6 }}
                  onClick={async () => {
                    await logout();
                    nav("/login");
                  }}
                >
                  Keluar
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {help && (
        <Modal onClose={() => setHelp(false)}>
          <h3>Cara belajar di VAME</h3>
          <ol>
            <li><b>Baca</b> poin bacaan wajib sampai selesai.</li>
            <li><b>Diskusikan</b> dengan mentor AI (jawabannya dibatasi pada materi kurikulum).</li>
            <li><b>Minta evaluasi</b> dan jawab pertanyaannya.</li>
            <li>Skor ≥ batas kelulusan (default 70) → <b>PASSED</b> dan poin berikutnya terbuka. Jika belum, tinjau ulang materi.</li>
          </ol>
          <p style={{ color: "var(--muted)", fontSize: 14 }}>Jawaban mentor tidak sesuai materi? Gunakan tombol “Tandai” agar ditinjau admin.</p>
        </Modal>
      )}
    </header>
  );
}
