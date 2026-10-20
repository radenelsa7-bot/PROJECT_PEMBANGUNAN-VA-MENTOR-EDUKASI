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

  useEffect(() => {
    const token = getToken()
    if (token) {
      const payload = decodeUser(token)
      if (payload) setUser({ id: payload.sub, role: payload.role })
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    const data = await api("/auth/login", { method: "POST", body: { email, password } })
    setToken(data.access_token)
    setUser(data.user)
  }

  const register = async (name, email, password) => {
    const data = await api("/auth/register", { method: "POST", body: { name, email, password } })
    setToken(data.access_token)
    setUser(data.user)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
