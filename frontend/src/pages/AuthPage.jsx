import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { errorMessage } from '../services/api.js'

export default function AuthPage({ mode }) {
  const isLogin = mode === 'login'
  const { login, register } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      if (isLogin) await login(form.email, form.password)
      else await register(form.name, form.email, form.password)
      nav('/dashboard')
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return (
    <form onSubmit={submit} className="card mx-auto mt-10 max-w-md space-y-4">
      <h1 className="text-xl font-bold">{isLogin ? 'Welcome back' : 'Create your account'}</h1>
      {!isLogin && <input className="input" placeholder="Full name" value={form.name} onChange={set('name')} required minLength={2} />}
      <input className="input" type="email" placeholder="Email" value={form.email} onChange={set('email')} required />
      <input className="input" type="password" placeholder="Password (min 6 chars)" value={form.password} onChange={set('password')} required minLength={6} />
      {error && <p className="text-sm text-red-500">{error}</p>}
      <button className="btn-primary w-full" disabled={busy}>{busy ? 'Please wait…' : isLogin ? 'Login' : 'Register'}</button>
      <p className="text-center text-sm text-slate-500">
        {isLogin ? <>No account? <Link className="text-brand-600" to="/register">Sign up</Link></> : <>Already registered? <Link className="text-brand-600" to="/login">Login</Link></>}
      </p>
    </form>
  )
}
