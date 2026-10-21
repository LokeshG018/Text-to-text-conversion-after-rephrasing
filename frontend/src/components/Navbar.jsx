import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'

const link = ({ isActive }) => `rounded-lg px-3 py-1.5 text-sm ${isActive ? 'bg-brand-600 text-white' : 'hover:bg-slate-200 dark:hover:bg-slate-800'}`

export default function Navbar() {
  const { user, logout } = useAuth()
  const { dark, toggle } = useTheme()
  const nav = useNavigate()
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-2 px-4 py-3">
        <Link to="/" className="mr-4 text-lg font-bold text-brand-600">✨ RePhraseAI</Link>
        <NavLink to="/rephrase" className={link}>Rephraser</NavLink>
        {user && <NavLink to="/history" className={link}>History</NavLink>}
        {user && <NavLink to="/dashboard" className={link}>Dashboard</NavLink>}
        <NavLink to="/about" className={link}>About / Models</NavLink>
        <div className="ml-auto flex items-center gap-2">
          <button className="btn-ghost" onClick={toggle} aria-label="Toggle theme">{dark ? '☀️ Light' : '🌙 Dark'}</button>
          {user ? (
            <>
              <span className="hidden text-sm sm:inline">Hi, {user.name.split(' ')[0]}</span>
              <button className="btn-ghost" onClick={async () => { await logout(); nav('/') }}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-ghost">Login</Link>
              <Link to="/register" className="btn-primary">Sign up</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
