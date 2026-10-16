import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { get } from "../api.js";
import { Notice, STATUS_META, STATUS_ORDER, StatusBadge, pointRoute, useAsync } from "../components/common.jsx";

const pad = (n) => String(n).padStart(2, "0");
const fmtScore = (n) => (Number.isInteger(n) ? n.toFixed(0) : Number(n).toFixed(1));

function Hero({ c, s }) {
  return (
    <section className="card hero">
      <div>
        <div className="hero-tags">
          <span className="tag">
            Tingkat {c.level}
            {c.topic_label ? ` • ${c.topic_label}` : ""}
          </span>
          <span className="official">
            <span>✔</span> Kurikulum Resmi VAME <span className="cid">ID: {c.code}</span>
          </span>
        </div>
        <h1>{c.title}</h1>
        <p className="desc">{c.description}</p>
        <div className="hero-foot">
          <span className="mentor-chip">Mentor Utama: {c.mentor_name}</span>
          <span className="est">🕓 Est. Waktu: {c.est_hours} Jam Pembelajaran</span>
        </div>
      </div>
      <aside className="summary">
        <div className="summary-head">
          Ringkasan Kelulusan <span>{s.percent}%</span>
        </div>
        <div className="bar"><div style={{ width: `${s.percent}%` }} /></div>
        <ul>
          <li><i style={{ background: "#22c55e" }} /> Modul Selesai: <strong>{s.modules_done} / {s.modules_total} Modul</strong></li>
          <li><i style={{ background: "#6366f1" }} /> Status Saat Ini: <strong>{s.modules_in_progress} Sedang Berlangsung</strong></li>
          <li><i style={{ background: "#d5d8e3" }} /> Modul Menunggu: <strong>{s.modules_locked} Terkunci</strong></li>
        </ul>
      </aside>
    </section>
  );
}

function Legend({ counts }) {
  return (
    <section className="card legend">
      <div className="legend-head">
        <b>Indikator status belajar ({STATUS_ORDER.length} pembagian status sistem)</b>
        <span>Pembaruan real-time aktif</span>
      </div>
      <div className="chips">
        {STATUS_ORDER.map((k) => (
          <div key={k} className={`chip st-${k}`} title={`${counts?.[k] ?? 0} poin bacaan`}>
            <b>
              <span>{STATUS_META[k].icon}</span> {STATUS_META[k].label}
            </b>
            <small>{STATUS_META[k].sub}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function Module({ m, focus, open, onToggle }) {
  const nav = useNavigate();
  const pill =
    m.status === "PASSED" ? <span className="pill ok">LULUS 100%</span>
    : m.status === "IN_PROGRESS" ? <span className="pill run">● SEDANG BERLANGSUNG</span>
    : <span className="pill lock">🔒 TERKUNCI</span>;
  return (
    <section className={`card module ${focus ? "active" : ""}`}>
      <button className="module-head" onClick={onToggle} aria-expanded={open}>
        <span className={`mnum ${m.status}`}>{pad(m.order)}</span>
        <span className="mtitle">
          <span className="mlabel">
            {focus ? "Fokus utama saat ini" : m.label} {pill}
          </span>
          <h3>{m.title}</h3>
        </span>
        <span className="mright">
          {m.status === "PASSED" && m.final_score != null && <span>Nilai Akhir: <b>{fmtScore(m.final_score)}</b></span>}
          {m.status === "IN_PROGRESS" && <span>Progres: {m.passed} / {m.total} Selesai ({m.percent}%)</span>}
          {m.status === "LOCKED" && <span>Selesaikan modul sebelumnya</span>}
          <span className={`chev ${open ? "open" : ""}`}>⌄</span>
        </span>
      </button>
      {open && (
        <div className="points">
          {m.reading_points.map((p, i) => (
            <div className="point" key={p.id}>
              <span className="pidx">{i + 1}</span>
              <span className={`pname ${p.status === "LOCKED" ? "locked" : ""}`}>{p.title}</span>
              {p.score != null && <span className="pscore">{fmtScore(p.score)}</span>}
              <StatusBadge status={p.status} />
              <button
                className={`btn sm ${["AVAILABLE", "READING", "DISCUSSING", "ASSESSMENT", "NEEDS_REVIEW"].includes(p.status) ? "primary" : ""}`}
                disabled={p.status === "LOCKED"}
                onClick={() => nav(pointRoute(p.id, p.status))}
              >
                {STATUS_META[p.status].action}
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function Side({ data }) {
  const nav = useNavigate();
  const a = data.activity;
  const cur = data.current;
  return (
    <div className="stack">
      <section className="card side-card">
        <div className="side-head">
          <span>🗓️ Aktivitas hari ini</span>
          <span className="day-chip">Hari ke-{a.day_number}</span>
        </div>
        <div className="tiles">
          <div className="tile">
            <small>Waktu Belajar</small>
            <strong>{a.study_label}</strong>
            <em className={a.delta_positive ? "" : "neg"}>{a.delta_positive ? "↗" : "↘"} {a.delta_label}</em>
          </div>
          <div className="tile">
            <small>Poin Diskusi</small>
            <strong>{a.discussion_sessions} Sesi</strong>
            <span className="sub">Dengan AI Tutor</span>
          </div>
        </div>
      </section>
      <section className="card side-card">
        <div className="side-head"><span>🧠 Catatan AI Mentor</span></div>
        {data.insight ? (
          <div className="insight">
            <b>Insight Evaluasi Terakhir</b>
            <q>{data.insight.feedback}</q>
            <div className="reco" style={{ marginTop: 8 }}>Materi: {data.insight.title} · skor <b>{fmtScore(data.insight.score)}</b></div>
          </div>
        ) : (
          <p className="empty">Belum ada evaluasi. Selesaikan satu poin bacaan untuk mendapat catatan dari mentor.</p>
        )}
        <p className="reco"><b>Langkah berikutnya:</b> {data.recommendation}</p>
        {cur && (
          <div style={{ marginTop: 12 }}>
            <button className="btn primary" onClick={() => nav(pointRoute(cur.id, cur.status))}>Lanjutkan belajar →</button>
          </div>
        )}
      </section>
    </div>
  );
}

export default function Curricula() {
  const { cid } = useParams();
  const { enrollments, enrollLoaded, selectedId, selectCurriculum } = useAuth();
  const id = Number(cid) || selectedId;
  const [menu, setMenu] = useState(false);
  const [open, setOpen] = useState({});
  const initOpen = useRef(null);

  useEffect(() => {
    if (cid && Number(cid) !== selectedId && enrollments.some((e) => e.curriculum_id === Number(cid))) selectCurriculum(Number(cid));
  }, [cid]); // eslint-disable-line

  const { data, error, reload } = useAsync(() => (id ? get(`/learning-path/${id}`) : Promise.resolve(null)), [id]);

  // Pembaruan "real-time": polling tiap 15 detik saat tab terlihat
  useEffect(() => {
    if (!id) return;
    const t = setInterval(() => document.visibilityState === "visible" && reload(), 15000);
    return () => clearInterval(t);
  }, [id, reload]);

  // Buka modul fokus saat data pertama kali tiba
  useEffect(() => {
    if (data && initOpen.current !== id) {
      initOpen.current = id;
      const focus = data.modules.find((m) => m.status === "IN_PROGRESS");
      setOpen(focus ? { [focus.id]: true } : {});
    }
  }, [data, id]);

  if (enrollLoaded && !id) return <Navigate to="/catalog" replace />;
  if (error) return <Notice kind="err">{error.message}</Notice>;
  if (!data) return <div className="center-note">Memuat peta alur belajar…</div>;

  const c = data.curriculum;
  const focusId = data.modules.find((m) => m.status === "IN_PROGRESS")?.id;

  return (
    <>
      <div className="crumbs">
        <div className="crumb-trail">
          <Link to="/catalog">Kurikulum</Link> › {c.short_name} › <b>Peta Alur Belajar</b>
        </div>
        <div className="switcher">
          <button className="switch-btn" onClick={() => setMenu(!menu)}>
            ⇄ Ganti Kurikulum: <b>{c.short_name}</b> ⌄
          </button>
          {menu && (
            <div className="switch-menu">
              {enrollments.map((e) => (
                <button key={e.curriculum_id} className={e.curriculum_id === c.id ? "on" : ""} onClick={() => { selectCurriculum(e.curriculum_id); setMenu(false); setOpen({}); initOpen.current = null; }}>
                  <span>{e.short_name}</span>
                  <span>{e.percent}%</span>
                </button>
              ))}
              <Link to="/catalog" onClick={() => setMenu(false)}>＋ Jelajahi kurikulum lain</Link>
            </div>
          )}
        </div>
      </div>

      <Hero c={c} s={data.summary} />

      <div className="grid-main">
        <div className="stack">
          <Legend counts={data.summary.status_counts} />
          {data.modules.map((m) => (
            <Module key={m.id} m={m} focus={m.id === focusId} open={!!open[m.id]} onToggle={() => setOpen((o) => ({ ...o, [m.id]: !o[m.id] }))} />
          ))}
        </div>
        <Side data={data} />
      </div>
    </>
  );
}
