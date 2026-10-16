import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { Notice } from "../components/common.jsx";

export default function Login() {
  const { user, login, register } = useAuth();
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [f, setF] = useState({ name: "", email: "", password: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      if (mode === "login") await login(f.email, f.password);
      else await register(f.name, f.email, f.password);
      nav("/");
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="card form-card" onSubmit={submit}>
      <div className="brand"><span className="brand-mark">V</span> VAME</div>
      <h1>{mode === "login" ? "Masuk ke VAME" : "Daftar sebagai Learner"}</h1>
      <p style={{ color: "var(--muted)" }}>Virtual Asisten Mentor Edukasi</p>

      {mode === "register" && (
        <>
          <label className="lbl">Nama lengkap</label>
          <input className="field" value={f.name} onChange={set("name")} required minLength={2} />
        </>
      )}
      <label className="lbl">Email</label>
      <input className="field" type="email" value={f.email} onChange={set("email")} required autoComplete="email" />
      <label className="lbl">Kata sandi {mode === "register" && "(min. 8 karakter)"}</label>
      <input className="field" type="password" value={f.password} onChange={set("password")} required minLength={mode === "register" ? 8 : 1} autoComplete={mode === "login" ? "current-password" : "new-password"} />

      {err && <div style={{ marginTop: 14 }}><Notice kind="err">{err}</Notice></div>}
      <button className="btn primary" style={{ width: "100%", marginTop: 20, padding: "11px" }} disabled={busy}>
        {busy ? "Memproses…" : mode === "login" ? "Masuk" : "Daftar"}
      </button>
      <p style={{ textAlign: "center", marginTop: 14, fontSize: 14, color: "var(--muted)" }}>
        {mode === "login" ? "Belum punya akun?" : "Sudah punya akun?"}{" "}
        <button type="button" className="link-btn" onClick={() => { setMode(mode === "login" ? "register" : "login"); setErr(""); }}>
          {mode === "login" ? "Daftar" : "Masuk"}
        </button>
      </p>
      {mode === "login" && (
        <div className="demo-hint">
          Akun demo: Learner <code>budi@vame.id</code> / <code>belajar123</code><br />
          Admin <code>admin@vame.id</code> / <code>admin123</code>
        </div>
      )}
    </form>
  );
}
