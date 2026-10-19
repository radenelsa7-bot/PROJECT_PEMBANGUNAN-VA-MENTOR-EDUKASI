import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

export const STATUS_META = {
  LOCKED: { icon: "🔒", label: "LOCKED", sub: "Terkunci", action: "Terkunci" },
  AVAILABLE: { icon: "📘", label: "AVAILABLE", sub: "Siap Dibaca", action: "Mulai Baca" },
  READING: { icon: "📖", label: "READING", sub: "Sedang Baca", action: "Lanjut Baca" },
  DISCUSSING: { icon: "💬", label: "DISCUSSING", sub: "Mentoring", action: "Mentoring" },
  ASSESSMENT: { icon: "📝", label: "ASSESSMENT", sub: "Evaluasi Kuis", action: "Kerjakan Evaluasi" },
  PASSED: { icon: "✅", label: "PASSED", sub: "Lulus Materi", action: "Tinjau" },
  NEEDS_REVIEW: { icon: "⚠️", label: "NEEDS_REVIEW", sub: "Perlu Tinjauan", action: "Tinjau Ulang" },
};
export const STATUS_ORDER = Object.keys(STATUS_META);

export function StatusBadge({ status }) {
  return <span className={`stbadge st-${status}`}>{STATUS_META[status]?.label || status}</span>;
}

// Tujuan halaman untuk sebuah poin sesuai statusnya (state machine di backend)
export function pointRoute(id, status) {
  if (status === "DISCUSSING") return `/mentoring/${id}`;
  if (status === "ASSESSMENT") return `/evaluation/${id}`;
  return `/reading/${id}`;
}

// Tombol kembali konsisten di seluruh halaman
export function BackButton({ to, label = "Kembali" }) {
  const nav = useNavigate();
  return (
    <button className="btn back-btn" onClick={() => (to ? nav(to) : nav(-1))}>
      <span aria-hidden="true">←</span> {label}
    </button>
  );
}

// Penunjuk alur belajar: Baca → Diskusi AI → Evaluasi → Lulus
const FLOW = [
  { key: "BACA", label: "Baca Materi", icon: "📖", match: ["AVAILABLE", "READING", "NEEDS_REVIEW"] },
  { key: "DISKUSI", label: "Diskusi AI", icon: "💬", match: ["DISCUSSING"] },
  { key: "EVALUASI", label: "Evaluasi", icon: "📝", match: ["ASSESSMENT"] },
  { key: "LULUS", label: "Lulus", icon: "✅", match: ["PASSED"] },
];

export function FlowSteps({ status, compact = false }) {
  const idx = FLOW.findIndex((f) => f.match.includes(status));
  const active = idx === -1 ? 0 : idx;
  return (
    <div className={`flow-steps ${compact ? "compact" : ""}`}>
      {FLOW.map((f, i) => (
        <div key={f.key} className={`flow-step ${i < active ? "done" : ""} ${i === active ? "on" : ""}`}>
          <span className="flow-dot">{i < active ? "✓" : f.icon}</span>
          <span className="flow-label">{f.label}</span>
          {i < FLOW.length - 1 && <span className="flow-line" aria-hidden="true" />}
        </div>
      ))}
    </div>
  );
}

// Panduan langkah alur belajar + peran AI di tiap tahap
const GUIDE = [
  { icon: "📖", title: "1. Baca Materi", desc: "Baca bahan bacaan wajib. AI belum aktif di sini — kamu harus selesai membaca dulu sebelum bisa diskusi." },
  { icon: "💬", title: "2. Diskusi dengan AI", desc: "Tanya apa saja seputar materi. Mentor AI hanya menjawab berdasarkan isi kurikulum, dan kamu minimal 1 pertanyaan untuk membuka evaluasi." },
  { icon: "📝", title: "3. Evaluasi", desc: "Setelah cukup berdiskusi, minta evaluasi. AI menilai pemahamanmu dan memberi skor + umpan balik." },
  { icon: "✅", title: "4. Lulus / Ulang", desc: "Skor ≥ 70 → lulus & lanjut ke materi berikutnya. Di bawah itu, AI menunjukkan bagian yang perlu dibaca ulang." },
];

export function FlowGuide({ onClose }) {
  return (
    <div className="flow-guide">
      <div className="flow-guide-head">
        <h3>🧭 Cara Kerja Alur Belajar & AI Mentor</h3>
        {onClose && <button className="btn sm" onClick={onClose}>Tutup</button>}
      </div>
      <div className="flow-guide-grid">
        {GUIDE.map((g) => (
          <div className="flow-guide-item" key={g.title}>
            <span className="flow-guide-icon">{g.icon}</span>
            <div>
              <b>{g.title}</b>
              <p>{g.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const alive = useRef(true);
  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => alive.current && setState({ data, error: null, loading: false }))
      .catch((error) => alive.current && setState({ data: null, error, loading: false }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => {
    alive.current = true;
    run();
    return () => {
      alive.current = false;
    };
  }, [run]);
  return { ...state, reload: run };
}

export function Notice({ kind = "warn", children }) {
  const cls = kind === "err" ? "notice err" : kind === "ok" ? "notice ok" : kind === "info" ? "notice info" : "notice";
  return <div className={cls}>{children}</div>;
}

// Penampil markdown sederhana (paragraf, `kode`, **tebal**, blok ``` ```), tanpa dangerouslySetInnerHTML
function inline(text) {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.startsWith("`") && part.endsWith("`")) return <code key={i}>{part.slice(1, -1)}</code>;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    return part;
  });
}
export function Markdown({ text }) {
  const out = [];
  const parts = text.split(/```[a-zA-Z]*\n([\s\S]*?)```/g);
  parts.forEach((seg, i) => {
    if (i % 2 === 1) {
      out.push(
        <pre key={i}>
          <code>{seg.replace(/\n$/, "")}</code>
        </pre>
      );
    } else {
      seg
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .forEach((l, j) => out.push(<p key={`${i}-${j}`}>{inline(l)}</p>));
    }
  });
  return <div className="md">{out}</div>;
}

export function Modal({ onClose, children }) {
  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        {children}
        <div className="actions">
          <button className="btn primary" onClick={onClose}>
            Mengerti
          </button>
        </div>
      </div>
    </div>
  );
}
