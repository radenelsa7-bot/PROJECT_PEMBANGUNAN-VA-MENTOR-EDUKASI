import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { get, post } from "../api.js";
import { BackButton, Notice, useAsync } from "../components/common.jsx";

export default function Catalog() {
  const { selectCurriculum } = useAuth();
  const nav = useNavigate();
  const { data, error, reload } = useAsync(() => get("/curricula"), []);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(null);

  const enroll = async (c) => {
    setBusy(c.id);
    setErr("");
    try {
      if (!c.enrolled) await post("/enrollments", { curriculum_id: c.id });
      selectCurriculum(c.id);
      nav(`/curricula/${c.id}`);
    } catch (e) {
      setErr(e.message);
      reload();
    } finally {
      setBusy(null);
    }
  };

  return (
    <>
      <div className="crumbs">
        <div style={{ flex: 1 }}>
          <h1 className="page-title">Pilih Kurikulum</h1>
          <p className="page-sub">Setiap kurikulum terdiri dari modul dan poin bacaan wajib yang dibuka berurutan.</p>
        </div>
        <BackButton to="/dashboard" label="Kembali" />
      </div>
      {(error || err) && <Notice kind="err">{(error || { message: err }).message}</Notice>}
      <div className="cols-2" style={{ marginTop: 16 }}>
        {(data || []).map((c) => (
          <article key={c.id} className="card cur-card">
            <span className="tag" style={{ alignSelf: "flex-start" }}>Tingkat {c.level}{c.topic_label ? ` • ${c.topic_label}` : ""}</span>
            <h3>{c.title}</h3>
            <p>{c.description}</p>
            <div className="meta-row">
              <span>{c.modules_count} modul</span>
              <span>{c.points_count} poin bacaan</span>
              <span>~{c.est_hours} jam</span>
            </div>
            <button className="btn primary" disabled={busy === c.id} onClick={() => enroll(c)}>
              {c.enrolled ? "Buka peta belajar" : "Daftar & mulai"}
            </button>
          </article>
        ))}
      </div>
      {data && data.length === 0 && <p className="empty">Belum ada kurikulum aktif.</p>}
    </>
  );
}
