import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../auth.jsx";
import { get } from "../api.js";
import { FlowSteps, FlowGuide, Notice, StatusBadge, pointRoute, useAsync } from "../components/common.jsx";

export default function Dashboard() {
  const { user, selectedId, enrollLoaded } = useAuth();
  const nav = useNavigate();
  const [showGuide, setShowGuide] = useState(false);
  const path = useAsync(() => (selectedId ? get(`/learning-path/${selectedId}`) : Promise.resolve(null)), [selectedId]);
  const prog = useAsync(() => get("/progress"), []);

  if (enrollLoaded && !selectedId)
    return (
      <>
        <h1 className="page-title">Halo, {user.name.split(" ")[0]}!</h1>
        <p className="page-sub">Kamu belum mengikuti kurikulum apa pun.</p>
        <Link className="btn primary" to="/catalog">Pilih kurikulum</Link>
      </>
    );
  if (path.error) return <Notice kind="err">{path.error.message}</Notice>;
  if (!path.data) return <div className="center-note">Memuat dashboard…</div>;

  const d = path.data;
  const cur = d.current;
  const o = prog.data?.overall;
  return (
    <>
      <h1 className="page-title">Halo, {user.name.split(" ")[0]} 👋</h1>
      <p className="page-sub">{d.curriculum.title} · hari ke-{d.activity.day_number}</p>

      <div className="flow-head">
        {cur && <FlowSteps status={cur.status} />}
        <button className="btn sm" onClick={() => setShowGuide((v) => !v)}>
          {showGuide ? "Sembunyikan panduan" : "🧭 Cara kerja alur & AI"}
        </button>
      </div>
      {showGuide && <FlowGuide onClose={() => setShowGuide(false)} />}

      <div className="kpis">
        <div className="card kpi"><small>Progres kurikulum</small><strong>{d.summary.percent}%</strong></div>
        <div className="card kpi"><small>Poin lulus</small><strong>{d.summary.points_passed} / {d.summary.points_total}</strong></div>
        <div className="card kpi"><small>Rata-rata skor</small><strong>{o?.avg_score ?? "–"}</strong></div>
        <div className="card kpi"><small>Waktu belajar hari ini</small><strong>{d.activity.study_label}</strong></div>
      </div>

      <section className="card panel">
        <h3>Lanjutkan belajar</h3>
        {cur ? (
          <div className="row">
            <div className="grow">
              <div style={{ color: "var(--muted)", fontSize: 13.5 }}>{cur.module_title}</div>
              <div style={{ fontSize: 20, fontWeight: 700, margin: "2px 0 6px" }}>{cur.title}</div>
              <StatusBadge status={cur.status} />
            </div>
            <button className="btn primary" onClick={() => nav(pointRoute(cur.id, cur.status))}>Lanjutkan →</button>
          </div>
        ) : (
          <p className="empty">Tidak ada poin aktif.</p>
        )}
        <p className="reco"><b>Rekomendasi mentor:</b> {d.recommendation}</p>
      </section>

      <section className="card panel">
        <h3>Catatan AI Mentor</h3>
        {d.insight ? (
          <div className="insight" style={{ marginTop: 0 }}>
            <b>Insight Evaluasi Terakhir · {d.insight.title}</b>
            <q>{d.insight.feedback}</q>
          </div>
        ) : (
          <p className="empty">Belum ada evaluasi.</p>
        )}
      </section>

      <div className="row">
        <Link className="btn" to="/curricula">Peta alur belajar</Link>
        <Link className="btn" to="/progress">Lihat progres lengkap</Link>
      </div>
    </>
  );
}
