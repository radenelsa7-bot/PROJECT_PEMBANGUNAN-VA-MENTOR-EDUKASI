import { useState } from "react";
import { Link } from "react-router-dom";
import { api, get } from "../api.js";
import { BackButton, Notice, useAsync } from "../components/common.jsx";

export default function Progress() {
  const { data, error } = useAsync(() => get("/progress"), []);
  const [err, setErr] = useState("");

  if (error) return <Notice kind="err">{error.message}</Notice>;
  if (!data) return <div className="center-note">Memuat progres…</div>;

  const exportCsv = async () => {
    try {
      const res = await api("/progress/export", { raw: true });
      const url = URL.createObjectURL(await res.blob());
      const a = Object.assign(document.createElement("a"), { href: url, download: "laporan-progres.csv" });
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <>
      <div className="crumbs">
        <div style={{ flex: 1 }}>
          <h1 className="page-title">Progres Belajar</h1>
          <p className="page-sub">Ringkasan penyelesaian, skor, dan rekomendasi langkah berikutnya.</p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <button className="btn" onClick={exportCsv}>⬇ Ekspor CSV</button>
          <BackButton to="/dashboard" label="Kembali" />
        </div>
      </div>
      {err && <Notice kind="err">{err}</Notice>}

      <div className="kpis">
        <div className="card kpi"><small>Rata-rata skor</small><strong>{data.overall.avg_score ?? "–"}</strong></div>
        <div className="card kpi"><small>Percobaan evaluasi</small><strong>{data.overall.attempts}</strong></div>
        <div className="card kpi"><small>Evaluasi lulus</small><strong>{data.overall.passed_attempts}</strong></div>
      </div>

      {data.curricula.map((c) => (
        <section key={c.curriculum_id} className="card panel">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3>{c.title}</h3>
            <b style={{ color: "var(--primary)" }}>{c.summary.percent}%</b>
          </div>
          <div className="bar"><div style={{ width: `${c.summary.percent}%` }} /></div>
          <p className="reco"><b>Rekomendasi:</b> {c.recommendation}</p>
          <table className="tbl" style={{ marginTop: 10 }}>
            <thead><tr><th>Modul</th><th>Lulus</th><th style={{ width: 200 }}>Progres</th><th>Nilai</th></tr></thead>
            <tbody>
              {c.modules.map((m) => (
                <tr key={m.id}>
                  <td>{m.title}</td>
                  <td>{m.passed} / {m.total}</td>
                  <td><div className="bar"><div style={{ width: `${m.percent}%` }} /></div></td>
                  <td>{m.final_score ?? "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}

      <section className="card panel">
        <h3>Riwayat evaluasi</h3>
        {data.history.length === 0 ? (
          <p className="empty">Belum ada evaluasi.</p>
        ) : (
          <table className="tbl">
            <thead><tr><th>Tanggal</th><th>Poin bacaan</th><th>Skor</th><th>Hasil</th><th>Umpan balik</th></tr></thead>
            <tbody>
              {data.history.map((h) => (
                <tr key={h.id}>
                  <td>{new Date(h.graded_at).toLocaleDateString("id-ID")}</td>
                  <td>{h.point}<div style={{ color: "var(--muted)", fontSize: 12.5 }}>{h.module}</div></td>
                  <td><b>{h.score}</b></td>
                  <td>{h.passed ? "✅ Lulus" : "⚠️ Tinjau"}</td>
                  <td style={{ maxWidth: 420 }}>{h.feedback}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}
