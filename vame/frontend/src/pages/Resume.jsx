import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { get } from "../api.js";
import { Notice, STATUS_META, StatusBadge, pointRoute, useAsync } from "../components/common.jsx";

// "Mentoring Session" / "Ask AI Mentor": pilih poin yang sudah melewati tahap bacaan.
export default function Resume() {
  const { selectedId, enrollLoaded } = useAuth();
  const nav = useNavigate();
  const { data, error } = useAsync(() => (selectedId ? get(`/learning-path/${selectedId}`) : Promise.resolve(null)), [selectedId]);

  if (enrollLoaded && !selectedId) return <Notice>Pilih kurikulum dahulu. <Link to="/catalog">Buka katalog</Link></Notice>;
  if (error) return <Notice kind="err">{error.message}</Notice>;
  if (!data) return <div className="center-note">Memuat sesi mentoring…</div>;

  const cur = data.current;
  const points = data.modules.flatMap((m) => m.reading_points.map((p) => ({ ...p, module: m.title })));
  const open = points.filter((p) => ["DISCUSSING", "ASSESSMENT", "PASSED", "NEEDS_REVIEW"].includes(p.status));

  return (
    <>
      <h1 className="page-title">Mentoring Session</h1>
      <p className="page-sub">Berdiskusi dengan mentor AI. Jawabannya dibatasi pada materi kurikulum yang sudah kamu baca.</p>

      {cur && (
        <section className="card panel">
          <h3>Sesi saat ini</h3>
          <div className="row">
            <div className="grow">
              <div style={{ fontSize: 19, fontWeight: 700 }}>{cur.title}</div>
              <div style={{ margin: "6px 0" }}><StatusBadge status={cur.status} /></div>
              {["AVAILABLE", "READING"].includes(cur.status) && <p className="reco">Selesaikan bacaan wajib dulu agar sesi mentoring terbuka.</p>}
            </div>
            <button className="btn primary" onClick={() => nav(cur.status === "DISCUSSING" ? `/mentoring/${cur.id}` : pointRoute(cur.id, cur.status))}>
              {cur.status === "DISCUSSING" ? "Lanjutkan sesi →" : STATUS_META[cur.status].action}
            </button>
          </div>
        </section>
      )}

      <section className="card panel">
        <h3>Topik yang bisa didiskusikan</h3>
        {open.length === 0 ? (
          <p className="empty">Belum ada topik. Baca dan tandai selesai satu poin bacaan terlebih dahulu.</p>
        ) : (
          <table className="tbl">
            <tbody>
              {open.map((p) => (
                <tr key={p.id}>
                  <td><b>{p.title}</b><div style={{ color: "var(--muted)", fontSize: 13 }}>{p.module}</div></td>
                  <td><StatusBadge status={p.status} /></td>
                  <td style={{ textAlign: "right" }}><button className="btn sm" onClick={() => nav(`/mentoring/${p.id}`)}>Buka sesi</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}
