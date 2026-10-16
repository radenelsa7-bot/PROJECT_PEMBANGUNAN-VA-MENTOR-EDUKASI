// Klien REST API VAME (semua endpoint berprefiks /api/v1, FR-43)
const BASE = "/api/v1";
const TOKEN_KEY = "vame_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY));

export class ApiError extends Error {
  constructor(status, message, code, data) {
    super(message);
    this.status = status;
    this.code = code;
    this.data = data;
  }
}

function messageFrom(detail, status) {
  if (!detail) return `Terjadi kesalahan (HTTP ${status}).`;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; "); // galat validasi Pydantic
  return detail.message || `Terjadi kesalahan (HTTP ${status}).`;
}

export async function api(path, { method = "GET", body, raw = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch {
    throw new ApiError(0, "Tidak dapat terhubung ke server VAME. Pastikan backend berjalan di port 8000.", "NETWORK");
  }
  if (raw && res.ok) return res;
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* tidak ada body */
  }
  if (!res.ok) {
    const detail = data?.detail;
    if (res.status === 401 && token && !path.startsWith("/auth/login")) {
      setToken(null);
      window.dispatchEvent(new Event("vame:logout"));
    }
    throw new ApiError(res.status, messageFrom(detail, res.status), detail?.code, detail);
  }
  return data;
}

export const get = (p) => api(p);
export const post = (p, body = {}) => api(p, { method: "POST", body });
export const put = (p, body = {}) => api(p, { method: "PUT", body });
