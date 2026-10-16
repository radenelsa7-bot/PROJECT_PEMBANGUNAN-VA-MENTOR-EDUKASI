import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { get, post } from "../api.js";
import { Notice, useAsync } from "../components/common.jsx";

export default function Evaluation() {
  const { rid } = useParams();
  const nav = useNavigate();
  const { data: ev, error } = useAsync(() => post(`/reading-points/${rid}/evaluation`), [rid]);
  const hist = useAsync(() => get(`/reading-points/${rid}/evaluations`), [rid, ev?.id]);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState(null);

  if (error)
    return (
      <>
        <Notice kind="warn">{error.message}</Notice>
        <div className="actions">
          <button className="btn primary" onClick={() => nav(`/mentoring/${rid}`)}>Kembali ke mentoring</button>
          <Link className="btn" to="/curricula">Peta belajar</Link>
        </div>
      </>
    );
  if (!ev) return <div className="center-note">Mentor sedang menyusun pertanyaan evaluasi…</div>;

  const submit = async () => {
    setBusy(true);
    setErr("");
    try {
      setRes(await post(`/evaluations/${ev.id}/answer`, { answer }));
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const r = res?.evaluation;
  return (
    <>
      <div className="crumbs">
        <div className="crumb-trail"><Link to="/curricula">Peta belajar</Link> › <b>Evaluasi pemahaman</b></div>
      </div>
      <div className="card panel" style={{ maxWidth: 900 }}>
        <span className="tag">📝 Evaluasi</span>
        <h2 style={{ margin: "14px 0" }}>Jawab dengan kata-katamu sendiri</h2>
        <div className="question-box">{ev.question}</div>

        {!res ? (
          <>
            <textarea className="answer" value={answer} onChange={(e) => setAnswer(e.target.value)} maxLength={4000} placeholder="Tulis jawabanmu di sini…" disabled={busy} />
            {err && <div style={{ marginTop: 12 }}><Notice kind="err">{err}</Notice></div>}
            <div className="actions">
              <button className="btn primary" disabled={busy || answer.trim().length < 3} onClick={submit}>{busy ? "Menilai jawabanmu…" : "Kirim jawaban"}</button>
              <button className="btn" onClick={() => nav(`/mentoring/${rid}`)}>Kembali berdiskusi</button>
            </div>
          </>
        ) : (
          <div className="card result">
            <div className={`score-ring ${res.passed ? "pass" : "fail"}`}>{r.score}</div>
            <div>
              {res.passed ? <Notice kind="ok">✅ LULUS (batas {res.threshold}). Poin berikutnya telah dibuka.</Notice>
                : <Notice>⚠️ Belum lulus (batas {res.threshold}). Tinjau ulang materi, lalu ulangi evaluasi.</Notice>}
            </div>
            <div><b>Umpan balik mentor</b><p style={{ marginTop: 6 }}>{r.feedback}</p></div>
            {res.missed_points?.length > 0 && (
              <div><b>Poin yang perlu diperkuat</b><ul>{res.missed_points.map((m) => <li key={m}>{m}</li>)}</ul></div>
            )}
            <div className="actions" style={{ marginTop: 0 }}>
              {res.passed && res.next_point_id && <button className="btn primary" onClick={() => nav(`/reading/${res.next_point_id}`)}>Lanjut ke poin berikutnya →</button>}
              {!res.passed && <button className="btn primary" onClick={() => nav(`/reading/${rid}`)}>📖 Tinjau ulang materi</button>}
              <Link className="btn" to="/curricula">Peta belajar</Link>
            </div>
          </div>
        )}
      </div>

      {hist.data?.some((h) => h.status === "graded") && (
        <div className="card panel" style={{ maxWidth: 900 }}>
          <h3>Riwayat evaluasi poin ini</h3>
          <table className="tbl">
            <thead><tr><th>Waktu</th><th>Skor</th><th>Hasil</th></tr></thead>
            <tbody>
              {hist.data.filter((h) => h.status === "graded").map((h) => (
                <tr key={h.id}><td>{new Date(h.created_at).toLocaleString("id-ID")}</td><td>{h.score}</td><td>{h.passed ? "Lulus" : "Perlu tinjauan"}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
