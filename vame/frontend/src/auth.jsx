import { createContext, useContext, useState, useEffect } from "react"
import { api, setToken, getToken } from "./api.js"

const AuthContext = createContext(null)

function decodeUser(token) {
  const payload = token.split(".")[1]
  if (!payload) return null
  try {
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [enrollments, setEnrollments] = useState([])
  const [enrollLoaded, setEnrollLoaded] = useState(false)
  const [selectedId, setSelectedId] = useState(null)

  useEffect(() => {
    const token = getToken()
    if (token) {
      const payload = decodeUser(token)
      if (payload) setUser({ id: payload.sub, role: payload.role })
      // fetch enrollments
      api("/enrollments").then((list) => {
        setEnrollments(list)
        if (list.length > 0) setSelectedId(list[0].curriculum_id)
        setEnrollLoaded(true)
      }).catch(() => setEnrollLoaded(true))
    } else {
      setEnrollLoaded(true)
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    const data = await api("/auth/login", { method: "POST", body: { email, password } })
    setToken(data.access_token)
    setUser(data.user)
    // reload enrollments
    const list = await api("/enrollments")
    setEnrollments(list)
    if (list.length > 0) setSelectedId(list[0].curriculum_id)
    setEnrollLoaded(true)
  }

  const register = async (name, email, password) => {
    const data = await api("/auth/register", { method: "POST", body: { name, email, password } })
    setToken(data.access_token)
    setUser(data.user)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    setEnrollments([])
    setEnrollLoaded(false)
    setSelectedId(null)
  }

  const selectCurriculum = (id) => setSelectedId(id)

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      enrollments,
      enrollLoaded,
      selectedId,
      selectCurriculum,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
