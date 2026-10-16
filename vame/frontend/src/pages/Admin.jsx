import { Fragment, useEffect, useState } from "react";
import { get, post, put } from "../api.js";
import { Notice, useAsync } from "../components/common.jsx";

const TABS = [
  ["overview", "Ikhtisar"],
  ["curricula", "Kurikulum"],
  ["prompt", "System Prompt"],
  ["sessions", "Log Sesi"],
  ["usage", "Statistik AI"],
  ["users", "Pengguna"],
  ["states", "Audit Status"],
];
const dt = (s) => (s ? new Date(s).toLocaleString("id-ID") : "–");

function useMsg() {
  const [m, setM] = useState(null);
  return [m, (kind, text) => setM({ kind, text }), () => setM(null)];
}

/* ---------------- Ikhtisar ---------------- */
function Overview() {
  const { data, reload } = useAsync(() => get("/admin/overview"), []);
  const [th, setTh] = useState("");
  const [msg, say] = useMsg();
  useEffect(() => { if (data) setTh(data.pass_threshold); }, [data]);
  if (!data) return <div className="center-note">Memuat…</div>;
  const save = async () => {
    try {
      await put("/admin/settings", { pass_threshold: Number(th) });
      say("ok", "Batas kelulusan disimpan.");
      reload();
    } catch (e) {
      say("err", e.message);
    }
  };
  return (
    <>
      <div className="kpis">
        {[["Learner", data.learners], ["Sesi mentoring", data.sessions], ["Jawaban ditandai", data.flagged_messages], ["Panggilan AI", data.ai_calls], ["AI gagal", data.ai_failures]].map(([k, v]) => (
          <div className="card kpi" key={k}><small>{k}</small><strong>{v}</strong></div>
        ))}
      </div>
      <section className="card panel">
        <h3>Batas kelulusan evaluasi (BR-04)</h3>
        <div className="row">
          <input className="field" style={{ width: 120 }} type="number" min={1} max={100} value={th} onChange={(e) => setTh(e.target.value)} />
          <button className="btn primary" onClick={save}>Simpan</button>
        </div>
        {msg && <div style={{ marginTop: 12 }}><Notice kind={msg.kind}>{msg.text}</Notice></div>}
      </section>
    </>
  );
}

/* ---------------- Kurikulum ---------------- */
const EMPTY_CUR = { code: "", title: "", short_name: "", description: "", level: "Dasar", topic_label: "", est_hours: 10, mentor_name: "Tutor AI VAME" };

function CurriculumDetail({ id, onChange }) {
  const { data: c, reload } = useAsync(() => get(`/curricula/${id}`), [id]);
  const [mod, setMod] = useState({ title: "", label: "MODUL", order: 1 });
  const [rp, setRp] = useState({ module_id: "", title: "", objective: "", keywords: "", references: "", order: 1, content: "" });
  const [msg, say] = useMsg();
  if (!c) return <div className="center-note">Memuat…</div>;

  const run = async (fn, ok) => {
    try {
      await fn();
      say("ok", ok);
      reload();
      onChange();
    } catch (e) {
      say("err", e.message);
    }
  };
  const nextModuleOrder = (c.modules.at(-1)?.order || 0) + 1;

  return (
    <div style={{ marginTop: 14 }}>
      {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}
      {c.modules.map((m) => (
        <div key={m.id} style={{ margin: "12px 0" }}>
          <b>{String(m.order).padStart(2, "0")} · {m.title}</b> <span className="mono" style={{ color: "var(--muted)" }}>({m.label})</span>
          <ul style={{ margin: "4px 0 0", color: "var(--muted)" }}>
            {m.reading_points.map((r) => <li key={r.id}>{r.order}. {r.title} <small>· {r.keywords.join(", ")}</small></li>)}
          </ul>
        </div>
      ))}

      <h4 style={{ margin: "18px 0 8px" }}>Tambah modul</h4>
      <div className="row">
        <input className="field grow" placeholder="Judul modul" value={mod.title} onChange={(e) => setMod({ ...mod, title: e.target.value })} />
        <input className="field" style={{ width: 150 }} placeholder="Label" value={mod.label} onChange={(e) => setMod({ ...mod, label: e.target.value })} />
        <input className="field" style={{ width: 80 }} type="number" min={1} value={mod.order || nextModuleOrder} onChange={(e) => setMod({ ...mod, order: Number(e.target.value) })} />
        <button className="btn primary" onClick={() => run(() => post(`/curricula/${c.id}/modules`, { ...mod, order: mod.order || nextModuleOrder }), "Modul ditambahkan.")}>Tambah</button>
      </div>

      <h4 style={{ margin: "18px 0 8px" }}>Tambah poin bacaan wajib</h4>
      <div className="row" style={{ alignItems: "stretch" }}>
        <select className="field" style={{ width: 240 }} value={rp.module_id} onChange={(e) => setRp({ ...rp, module_id: e.target.value })}>
          <option value="">Pilih modul…</option>
          {c.modules.map((m) => <option key={m.id} value={m.id}>{m.order}. {m.title}</option>)}
        </select>
        <input className="field grow" placeholder="Judul" value={rp.title} onChange={(e) => setRp({ ...rp, title: e.target.value })} />
        <input className="field" style={{ width: 80 }} type="number" min={1} value={rp.order} onChange={(e) => setRp({ ...rp, order: Number(e.target.value) })} />
      </div>
      <input className="field" style={{ marginTop: 10 }} placeholder="Tujuan pembelajaran" value={rp.objective} onChange={(e) => setRp({ ...rp, objective: e.target.value })} />
      <input className="field" style={{ marginTop: 10 }} placeholder="Kata kunci (pisahkan dengan koma)" value={rp.keywords} onChange={(e) => setRp({ ...rp, keywords: e.target.value })} />
      <input className="field" style={{ marginTop: 10 }} placeholder="Referensi sumber (wajib, BR-05)" value={rp.references} onChange={(e) => setRp({ ...rp, references: e.target.value })} />
      <textarea className="field" style={{ marginTop: 10 }} placeholder="Isi materi (boleh memakai ``` untuk blok kode)" value={rp.content} onChange={(e) => setRp({ ...rp, content: e.target.value })} />
      <button
        className="btn primary"
        style={{ marginTop: 10 }}
        disabled={!rp.module_id}
        onClick={() =>
          run(
            () => post(`/modules/${rp.module_id}/reading-points`, { title: rp.title, objective: rp.objective, references: rp.references, content: rp.content, order: rp.order, keywords: rp.keywords.split(",").map((k) => k.trim()).filter(Boolean) }),
            "Poin bacaan ditambahkan."
          )
        }
      >
        Tambah poin bacaan
      </button>
    </div>
  );
}

function Curricula() {
  const { data, reload } = useAsync(() => get("/curricula"), []);
  const [form, setForm] = useState(EMPTY_CUR);
  const [open, setOpen] = useState(null);
  const [json, setJson] = useState("");
  const [msg, say] = useMsg();
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const run = async (fn, ok) => {
    try {
      await fn();
      say("ok", ok);
      reload();
    } catch (e) {
      say("err", e.message);
    }
  };

  return (
    <>
      {msg && <div style={{ marginBottom: 14 }}><Notice kind={msg.kind}>{msg.text}</Notice></div>}
      <section className="card panel">
        <h3>Daftar kurikulum</h3>
        <table className="tbl">
          <thead><tr><th>Kode</th><th>Judul</th><th>Modul / Poin</th><th>Status</th><th /></tr></thead>
          <tbody>
            {(data || []).map((c) => (
              <Fragment key={c.id}>
                <tr>
                  <td className="mono">{c.code}</td>
                  <td>{c.title}</td>
                  <td>{c.modules_count} / {c.points_count}</td>
                  <td>{c.is_active ? "Aktif" : "Nonaktif"}</td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    <button className="btn sm" onClick={() => setOpen(open === c.id ? null : c.id)}>{open === c.id ? "Tutup" : "Kelola"}</button>{" "}
                    <button className="btn sm" onClick={() => run(() => put(`/curricula/${c.id}`, { is_active: !c.is_active }), c.is_active ? "Kurikulum dinonaktifkan." : "Kurikulum diaktifkan.")}>
                      {c.is_active ? "Nonaktifkan" : "Aktifkan"}
                    </button>
                  </td>
                </tr>
                {open === c.id && (
                  <tr><td colSpan={5}><CurriculumDetail id={c.id} onChange={reload} /></td></tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card panel">
        <h3>Buat kurikulum baru</h3>
        <div className="row">
          <input className="field" style={{ width: 150 }} placeholder="Kode (mis. PY-101)" value={form.code} onChange={set("code")} />
          <input className="field grow" placeholder="Judul" value={form.title} onChange={set("title")} />
          <input className="field" style={{ width: 180 }} placeholder="Nama singkat" value={form.short_name} onChange={set("short_name")} />
        </div>
        <textarea className="field" style={{ marginTop: 10 }} placeholder="Deskripsi" value={form.description} onChange={set("description")} />
        <div className="row" style={{ marginTop: 10 }}>
          <input className="field" style={{ width: 140 }} placeholder="Tingkat" value={form.level} onChange={set("level")} />
          <input className="field" style={{ width: 160 }} placeholder="Label topik (Python 3.12)" value={form.topic_label} onChange={set("topic_label")} />
          <input className="field" style={{ width: 110 }} type="number" min={1} value={form.est_hours} onChange={(e) => setForm({ ...form, est_hours: Number(e.target.value) })} />
          <input className="field grow" placeholder="Nama mentor" value={form.mentor_name} onChange={set("mentor_name")} />
          <button className="btn primary" onClick={() => run(async () => { await post("/curricula", form); setForm(EMPTY_CUR); }, "Kurikulum dibuat. Klik “Kelola” untuk menambah modul.")}>Simpan</button>
        </div>
      </section>

      <section className="card panel">
        <h3>Impor kurikulum (JSON)</h3>
        <textarea className="field" style={{ minHeight: 140, fontFamily: "var(--mono)", fontSize: 13 }} placeholder='{"code":"...","title":"...","modules":[{"title":"...","order":1,"reading_points":[{...}]}]}' value={json} onChange={(e) => setJson(e.target.value)} />
        <button className="btn primary" style={{ marginTop: 10 }} onClick={() => run(async () => { await post("/curricula/import", JSON.parse(json)); setJson(""); }, "Kurikulum berhasil diimpor.")}>Impor</button>
      </section>
    </>
  );
}

/* ---------------- System Prompt ---------------- */
function PromptTab() {
  const { data, reload } = useAsync(() => get("/admin/prompt-config"), []);
  const [text, setText] = useState("");
  const [msg, say] = useMsg();
  useEffect(() => { if (data) setText(data.active.content); }, [data]);
  if (!data) return <div className="center-note">Memuat…</div>;
  const save = async () => {
    try {
      const r = await put("/admin/prompt-config", { content: text });
      say("ok", `Tersimpan sebagai versi ${r.version} dan langsung aktif.`);
      reload();
    } catch (e) {
      say("err", e.message);
    }
  };
  return (
    <>
      <section className="card panel">
        <h3>System Prompt mentor · versi aktif v{data.active.version}</h3>
        <textarea className="field" style={{ minHeight: 280, fontFamily: "var(--mono)", fontSize: 13 }} value={text} onChange={(e) => setText(e.target.value)} />
        <div className="row" style={{ marginTop: 10 }}>
          <button className="btn primary" onClick={save} disabled={text === data.active.content}>Simpan sebagai versi baru</button>
          <span style={{ color: "var(--muted)", fontSize: 13 }}>Setiap perubahan membuat versi baru agar dapat ditelusuri (FR-38).</span>
        </div>
        {msg && <div style={{ marginTop: 12 }}><Notice kind={msg.kind}>{msg.text}</Notice></div>}
      </section>
      <section className="card panel">
        <h3>Riwayat versi</h3>
        <table className="tbl">
          <thead><tr><th>Versi</th><th>Dibuat</th><th>Status</th><th /></tr></thead>
          <tbody>
            {data.versions.map((v) => (
              <tr key={v.version}>
                <td>v{v.version}</td><td>{dt(v.created_at)}</td><td>{v.active ? "Aktif" : "–"}</td>
                <td style={{ textAlign: "right" }}><button className="btn sm" onClick={() => setText(v.content)}>Muat ke editor</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

/* ---------------- Log sesi ---------------- */
function Sessions() {
  const [flagged, setFlagged] = useState(false);
  const { data } = useAsync(() => get(`/admin/sessions?flagged=${flagged}`), [flagged]);
  const [sid, setSid] = useState(null);
  const detail = useAsync(() => (sid ? get(`/admin/sessions/${sid}`) : Promise.resolve(null)), [sid]);
  return (
    <>
      <section className="card panel">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3>Log sesi mentoring</h3>
          <label><input type="checkbox" checked={flagged} onChange={(e) => setFlagged(e.target.checked)} /> Hanya yang ditandai</label>
        </div>
        <table className="tbl">
          <thead><tr><th>#</th><th>Learner</th><th>Poin bacaan</th><th>Mulai</th><th>Pesan</th><th>🚩</th><th /></tr></thead>
          <tbody>
            {(data || []).map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td><td>{s.learner}</td><td>{s.reading_point}</td><td>{dt(s.started_at)}</td><td>{s.messages}</td><td>{s.flagged || ""}</td>
                <td><button className="btn sm" onClick={() => setSid(s.id)}>Lihat</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.length === 0 && <p className="empty">Tidak ada sesi.</p>}
      </section>
      {detail.data && (
        <section className="card panel">
          <h3>Sesi #{detail.data.id} · {detail.data.learner} · {detail.data.reading_point}</h3>
          {detail.data.messages.map((m) => (
            <div key={m.id} style={{ margin: "10px 0" }}>
              <b>{m.role === "user" ? "Learner" : "Mentor"}</b> <small className="mono" style={{ color: "var(--muted)" }}>{m.kind} · {dt(m.created_at)}</small>
              <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
              {m.flagged && <Notice>🚩 Ditandai learner: {m.flag_reason || "(tanpa alasan)"}</Notice>}
            </div>
          ))}
        </section>
      )}
    </>
  );
}

/* ---------------- Statistik AI ---------------- */
function Usage() {
  const [range, setRange] = useState({ from: "", to: "" });
  const qs = new URLSearchParams(Object.entries({ date_from: range.from, date_to: range.to }).filter(([, v]) => v)).toString();
  const { data } = useAsync(() => get(`/admin/ai-usage${qs ? `?${qs}` : ""}`), [qs]);
  const [audit, setAudit] = useState(null);
  if (!data) return <div className="center-note">Memuat…</div>;
  const t = data.totals;
  const max = Math.max(1, ...data.by_day.map((d) => d.calls));
  return (
    <>
      <section className="card panel">
        <div className="row">
          <h3 style={{ margin: 0 }}>Rentang tanggal</h3>
          <input className="field" style={{ width: 160 }} type="date" value={range.from} onChange={(e) => setRange({ ...range, from: e.target.value })} />
          <span>s/d</span>
          <input className="field" style={{ width: 160 }} type="date" value={range.to} onChange={(e) => setRange({ ...range, to: e.target.value })} />
        </div>
      </section>
      <div className="kpis">
        {[["Panggilan", t.calls], ["Gagal", t.failures], ["Token masuk", t.tokens_in], ["Token keluar", t.tokens_out], ["Latensi rata-rata", `${t.avg_latency_ms} ms`]].map(([k, v]) => (
          <div className="card kpi" key={k}><small>{k}</small><strong>{v}</strong></div>
        ))}
      </div>
      <section className="card panel">
        <h3>Panggilan per hari</h3>
        <div className="bars">{data.by_day.map((d) => <div key={d.day} title={`${d.day}: ${d.calls}`} style={{ height: `${(d.calls / max) * 100}%` }} />)}</div>
        <p className="mono" style={{ color: "var(--muted)" }}>{Object.entries(data.by_kind).map(([k, v]) => `${k}: ${v}`).join(" · ") || "Belum ada panggilan."}</p>
      </section>
      <section className="card panel">
        <h3>Panggilan terbaru</h3>
        <table className="tbl">
          <thead><tr><th>Waktu</th><th>Jenis</th><th>Model</th><th>Token (in/out)</th><th>Latensi</th><th>Hasil</th><th /></tr></thead>
          <tbody>
            {data.recent.map((r) => (
              <tr key={r.id}>
                <td>{dt(r.created_at)}</td><td>{r.kind}</td><td className="mono">{r.provider}/{r.model}</td><td>{r.tokens_in}/{r.tokens_out}</td><td>{r.latency_ms} ms</td>
                <td>{r.success ? "OK" : `Gagal: ${r.error || ""}`}</td>
                <td><button className="btn sm" onClick={async () => setAudit(await get(`/admin/ai-usage/calls/${r.id}`))}>Audit</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {audit && (
        <section className="card panel">
          <h3>Audit panggilan #{audit.id} ({audit.kind})</h3>
          <b>Prompt</b><pre className="audit">{audit.prompt}</pre>
          <b>Respons</b><pre className="audit">{audit.response || audit.error}</pre>
        </section>
      )}
    </>
  );
}

/* ---------------- Pengguna ---------------- */
function Users() {
  const { data } = useAsync(() => get("/admin/users"), []);
  return (
    <section className="card panel">
      <h3>Pengguna & progres agregat</h3>
      <table className="tbl">
        <thead><tr><th>Nama</th><th>Email</th><th>Role</th><th>Kurikulum</th><th>Poin lulus</th><th>Progres</th><th>Rata-rata skor</th></tr></thead>
        <tbody>
          {(data || []).map((u) => (
            <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td>{u.role}</td><td>{u.enrollments}</td><td>{u.points_passed} / {u.points_total}</td><td>{u.percent}%</td><td>{u.avg_score ?? "–"}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

/* ---------------- Audit status ---------------- */
function States() {
  const [inv, setInv] = useState(false);
  const { data } = useAsync(() => get(`/admin/state-logs?invalid_only=${inv}`), [inv]);
  return (
    <section className="card panel">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3>Jejak transisi status belajar</h3>
        <label><input type="checkbox" checked={inv} onChange={(e) => setInv(e.target.checked)} /> Hanya transisi ditolak</label>
      </div>
      <table className="tbl">
        <thead><tr><th>Waktu</th><th>User</th><th>Poin</th><th>Dari</th><th>Pemicu</th><th>Ke</th><th>Valid</th><th>Catatan</th></tr></thead>
        <tbody>
          {(data || []).map((r) => (
            <tr key={r.id}><td>{dt(r.created_at)}</td><td>{r.user_id}</td><td>{r.reading_point_id}</td><td className="mono">{r.from}</td><td className="mono">{r.trigger}</td><td className="mono">{r.to || "–"}</td><td>{r.valid ? "✔" : "✖ ditolak"}</td><td>{r.note}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default function Admin() {
  const [tab, setTab] = useState("overview");
  const View = { overview: Overview, curricula: Curricula, prompt: PromptTab, sessions: Sessions, usage: Usage, users: Users, states: States }[tab];
  return (
    <>
      <h1 className="page-title">Panel Admin</h1>
      <p className="page-sub">Kurikulum, System Prompt mentor, log sesi, dan statistik penggunaan AI.</p>
      <div className="tabs">
        {TABS.map(([k, l]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>)}
      </div>
      <View />
    </>
  );
}
