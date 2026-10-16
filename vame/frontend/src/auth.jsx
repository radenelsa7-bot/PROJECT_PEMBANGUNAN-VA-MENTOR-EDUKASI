import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { get, post, setToken, getToken } from "./api.js";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

const SEL_KEY = "vame_curriculum";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!getToken());
  const [enrollments, setEnrollments] = useState([]);
  const [enrollLoaded, setEnrollLoaded] = useState(false);
  const [selectedId, setSelectedId] = useState(() => Number(localStorage.getItem(SEL_KEY)) || null);

  const loadEnrollments = useCallback(async () => {
    try {
      const list = await get("/enrollments");
      setEnrollments(list);
      setEnrollLoaded(true);
      setSelectedId((cur) => {
        const id = list.some((e) => e.curriculum_id === cur) ? cur : list[0]?.curriculum_id ?? null;
        if (id) localStorage.setItem(SEL_KEY, id);
        return id;
      });
      return list;
    } catch {
      setEnrollLoaded(true);
      return [];
    }
  }, []);

  useEffect(() => {
    if (!getToken()) return;
    get("/auth/me")
      .then((u) => {
        setUser(u);
        if (u.role === "learner") loadEnrollments();
      })
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, [loadEnrollments]);

  useEffect(() => {
    const h = () => setUser(null);
    window.addEventListener("vame:logout", h);
    return () => window.removeEventListener("vame:logout", h);
  }, []);

  const finishAuth = async (res) => {
    setToken(res.access_token);
    setUser(res.user);
    if (res.user.role === "learner") await loadEnrollments();
    return res.user;
  };

  const value = {
    user,
    loading,
    enrollments,
    enrollLoaded: enrollLoaded || user?.role === "admin",
    selectedId,
    selected: enrollments.find((e) => e.curriculum_id === selectedId) || null,
    refreshEnrollments: loadEnrollments,
    selectCurriculum: (id) => {
      localStorage.setItem(SEL_KEY, id);
      setSelectedId(id);
    },
    login: async (email, password) => finishAuth(await post("/auth/login", { email, password })),
    register: async (name, email, password) => finishAuth(await post("/auth/register", { name, email, password })),
    logout: async () => {
      try {
        await post("/auth/logout");
      } catch {
        /* token mungkin sudah tidak valid */
      }
      setToken(null);
      setUser(null);
      setEnrollments([]);
      setEnrollLoaded(false);
    },
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
