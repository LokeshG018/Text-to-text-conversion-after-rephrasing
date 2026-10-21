import { createContext, useContext, useEffect, useState } from 'react'
import * as api from '../services/api.js'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!localStorage.getItem('token'))

  useEffect(() => {
    if (!localStorage.getItem('token')) return
    api.getMe().then(setUser).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false))
  }, [])

  const save = (data) => { localStorage.setItem('token', data.access_token); setUser(data.user) }
  const login = async (email, password) => save(await api.loginUser({ email, password }))
  const register = async (name, email, password) => save(await api.registerUser({ name, email, password }))
  const logout = async () => { await api.logoutUser(); localStorage.removeItem('token'); setUser(null) }

  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
}
