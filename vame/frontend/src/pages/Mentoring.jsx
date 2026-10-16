import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, post } from "../api.js";
import { Notice, StatusBadge, useAsync } from "../components/common.jsx";

const STARTERS = ["Jelaskan konsep ini dengan analogi sederhana", "Beri contoh kode singkat", "Apa kesalahan yang sering terjadi?"];
const KIND_LABEL = { out_of_scope: "Di luar lingkup kurikulum", blocked: "Pesan diblokir guardrail" };

export default function Mentoring() {
  const { rid } = useParams();
  const nav = useNavigate();
  const { data: s, error, reload } = useAsync(() => post(`/reading-points/${rid}/sessions`), [rid]);
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [err, setErr] = useState("");
  const [interactions, setInteractions] = useState(0);
  const [evalBusy, setEvalBusy] = useState(false);
  const log = useRef(null);

  useEffect(() => {
    if (s) {
      setMsgs(s.messages);
      setInteractions(s.interactions);
    }
  }, [s]);
  useEffect(() => {
    log.current?.scrollTo({ top: log.current.scrollHeight, behavior: "smooth" });
  }, [msgs, sending]);

  if (error)
    return (
      <>
        <Notice kind={error.code === "READ_FIRST" ? "warn" : "err"}>{error.message}</Notice>
        <div className="actions">
          {error.code === "READ_FIRST" && <button className="btn primary" onClick={() => nav(`/reading/${rid}`)}>Buka bacaan wajib</button>}
          <Link className="btn" to="/curricula">← Peta belajar</Link>
        </div>
      </>
    );
  if (!s) return <div className="center-note">Menyiapkan sesi mentoring…</div>;

  const rp = s.reading_point;
  const send = async (content) => {
    const c = (content ?? text).trim();
    if (!c || sending) return;
    setSending(true);
    setErr("");
    setText("");
    const tmp = { id: `tmp-${Date.now()}`, role: "user", content: c, kind: "normal" };
    setMsgs((m) => [...m, tmp]);
    try {
      const r = await post(`/sessions/${s.id}/messages`, { content: c });
      setMsgs((m) => [...m.filter((x) => x.id !== tmp.id), r.user_message, r.mentor_message]);
      if (r.interactions != null) setInteractions(r.interactions);
    } catch (e) {
      setMsgs((m) => m.filter((x) => x.id !== tmp.id));
      setText(c);
      setErr(e instanceof ApiError ? e.message : "Gagal mengirim pesan.");
    } finally {
      setSending(false);
    }
  };

  const flag = async (m) => {
    const reason = window.prompt("Apa yang tidak sesuai dengan materi? (opsional)", "");
    if (reason === null) return;
    try {
      await post(`/messages/${m.id}/flag`, { reason });
      setMsgs((ms) => ms.map((x) => (x.id === m.id ? { ...x, flagged: true } : x)));
    } catch (e) {
      setErr(e.message);
    }
  };

  const goEval = async () => {
    setEvalBusy(true);
    setErr("");
    try {
      if (rp.status !== "ASSESSMENT") await post(`/reading-points/${rp.id}/evaluation`);
      nav(`/evaluation/${rp.id}`);
    } catch (e) {
      setErr(e.message);
      reload();
    } finally {
      setEvalBusy(false);
    }
  };

  const ready = interactions >= s.min_interactions;
  return (
    <>
      <div className="crumbs">
        <div className="crumb-trail"><Link to={`/curricula/${rp.curriculum_id}`}>Peta belajar</Link> › {rp.module_title} › <b>Mentoring</b></div>
      </div>
      <div className="chat-wrap">
        <aside className="card side-card stack" style={{ gap: 14 }}>
          <div><StatusBadge status={rp.status} /></div>
          <h3 style={{ fontSize: 19 }}>{rp.title}</h3>
          <p style={{ color: "var(--muted)", fontSize: 14 }}>{rp.objective}</p>
          <div className="kw" style={{ margin: 0 }}>{rp.keywords.map((k) => <span key={k}>{k}</span>)}</div>
          <div className="notice info">
            Pertanyaan ke mentor: <b>{interactions}</b> / {s.min_interactions} (minimal untuk membuka evaluasi)
          </div>
          <button className="btn primary" disabled={!ready || evalBusy || rp.status === "PASSED"} onClick={goEval}>
            {rp.status === "ASSESSMENT" ? "Lanjutkan evaluasi →" : "📝 Minta evaluasi"}
          </button>
          <Link className="btn" to={`/reading/${rp.id}`} style={{ textAlign: "center" }}>📖 Baca ulang materi</Link>
        </aside>

        <section className="card chat">
          <div className="chat-log" ref={log}>
            {msgs.length === 0 && (
              <div className="msg mentor">
                Halo! Saya mentor AI VAME. Tanyakan apa saja tentang <b>{rp.title}</b>. Saya hanya menjawab berdasarkan materi kurikulum ini.
              </div>
            )}
            {msgs.map((m) => (
              <div key={m.id} className={`msg ${m.role} ${m.kind}`}>
                {m.content}
                {m.role === "mentor" && (
                  <div className="msg-foot">
                    {KIND_LABEL[m.kind] && <span>⚠ {KIND_LABEL[m.kind]}</span>}
                    {m.flagged ? <span>🚩 Ditandai untuk ditinjau admin</span> : typeof m.id === "number" && <button onClick={() => flag(m)}>Tandai tidak sesuai materi</button>}
                  </div>
                )}
              </div>
            ))}
            {sending && <div className="typing">Mentor sedang mengetik…</div>}
          </div>
          {err && <div style={{ padding: "0 14px 10px" }}><Notice kind="err">{err}</Notice></div>}
          {msgs.length === 0 && (
            <div className="row" style={{ padding: "0 14px 10px" }}>
              {STARTERS.map((q) => <button key={q} className="btn sm" onClick={() => send(q)}>{q}</button>)}
            </div>
          )}
          <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
            <textarea
              value={text}
              maxLength={2000}
              placeholder="Tulis pertanyaanmu tentang materi ini…"
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            />
            <button className="btn primary" disabled={sending || !text.trim()}>Kirim</button>
          </form>
        </section>
      </div>
    </>
  );
}
