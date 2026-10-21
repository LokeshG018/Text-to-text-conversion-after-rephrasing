import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const errorMessage = (e) => {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  return e?.message || 'Something went wrong'
}

export const registerUser = (data) => api.post('/auth/register', data).then((r) => r.data)
export const loginUser = (data) => api.post('/auth/login', data).then((r) => r.data)
export const logoutUser = () => api.post('/auth/logout').catch(() => null)
export const getMe = () => api.get('/auth/me').then((r) => r.data)
export const rephrase = (payload) => api.post('/rephrase', payload).then((r) => r.data)
export const getHistory = (params) => api.get('/history', { params }).then((r) => r.data)
export const getSummary = () => api.get('/history/stats/summary').then((r) => r.data)
export const toggleFavorite = (id) => api.patch(`/history/${id}/favorite`).then((r) => r.data)
export const deleteHistory = (id) => api.delete(`/history/${id}`).then((r) => r.data)
export const getStyles = () => api.get('/styles').then((r) => r.data)
export const getComparison = () => api.get('/models/comparison').then((r) => r.data)
export const fixGrammar = (text) => api.post('/grammar', { text }).then((r) => r.data)
