import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { get, post } from "../api.js";
import { Markdown, Notice, StatusBadge, pointRoute, useAsync } from "../components/common.jsx";

// Bacaan wajib (BR-01). GET ini membuka poin: AVAILABLE -> READING, NEEDS_REVIEW -> READING.
export default function Reading() {
  const { rid } = useParams();
  const nav = useNavigate();
  const { data: p, error, reload } = useAsync(() => get(`/reading-points/${rid}`), [rid]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  if (error)
    return (
      <>
        <Notice kind="err">{error.message}</Notice>
        <p style={{ marginTop: 16 }}><Link className="btn" to="/curricula">← Kembali ke peta belajar</Link></p>
      </>
    );
  if (!p) return <div className="center-note">Memuat bacaan…</div>;

  const finish = async () => {
    setBusy(true);
    setErr("");
    try {
      await post(`/reading-points/${p.id}/complete-reading`);
      nav(`/mentoring/${p.id}`);
    } catch (e) {
      setErr(e.message);
      reload();
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="crumbs">
        <div className="crumb-trail">
          <Link to={`/curricula/${p.curriculum.id}`}>{p.curriculum.short_name}</Link> › {p.module.title} › <b>Poin {p.position.index} / {p.position.total}</b>
        </div>
        <Link className="btn" to={`/curricula/${p.curriculum.id}`}>← Peta belajar</Link>
      </div>

      <article className="card reading">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="tag">Bacaan wajib</span>
          <StatusBadge status={p.status} />
        </div>
        <h1>{p.title}</h1>
        <div className="objective"><b>Tujuan pembelajaran:</b> {p.objective}</div>
        <div className="kw">{p.keywords.map((k) => <span key={k}>{k}</span>)}</div>
        <Markdown text={p.content} />
        <div className="refs"><b>Sumber:</b> {p.references}</div>

        {err && <div style={{ marginTop: 16 }}><Notice kind="err">{err}</Notice></div>}
        <div className="actions">
          {p.status === "READING" && (
            <button className="btn primary" disabled={busy} onClick={finish}>✔ Saya sudah selesai membaca</button>
          )}
          {["DISCUSSING", "ASSESSMENT"].includes(p.status) && (
            <button className="btn primary" onClick={() => nav(pointRoute(p.id, p.status))}>
              {p.status === "DISCUSSING" ? "Lanjut ke sesi mentoring →" : "Lanjut ke evaluasi →"}
            </button>
          )}
          {p.status === "PASSED" && (
            <>
              <span className="notice ok">✅ Lulus{p.score != null ? ` · skor terbaik ${p.score}` : ""}</span>
              <button className="btn" onClick={() => nav(`/mentoring/${p.id}`)}>Diskusi lagi dengan mentor</button>
            </>
          )}
          <Link className="btn" to={`/curricula/${p.curriculum.id}`}>Kembali</Link>
        </div>
      </article>
    </>
  );
}
