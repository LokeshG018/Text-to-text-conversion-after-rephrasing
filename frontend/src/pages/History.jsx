import { useCallback, useEffect, useState } from 'react'
import * as api from '../services/api.js'

export default function History() {
  const [items, setItems] = useState([])
  const [search, setSearch] = useState('')
  const [favOnly, setFavOnly] = useState(false)
  const [open, setOpen] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    api.getHistory({ search: search || undefined, favorites_only: favOnly }).then(setItems).catch((e) => setError(api.errorMessage(e)))
  }, [search, favOnly])
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t) }, [load])

  const fav = async (id) => { const u = await api.toggleFavorite(id); setItems((l) => l.map((x) => (x.id === id ? u : x))) }
  const del = async (id) => { await api.deleteHistory(id); setItems((l) => l.filter((x) => x.id !== id)) }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="mr-auto text-2xl font-bold">History</h1>
        <input className="input max-w-xs" placeholder="Search…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={favOnly} onChange={(e) => setFavOnly(e.target.checked)} /> Favourites only</label>
      </div>
      {error && <p className="text-red-500">{error}</p>}
      {items.length === 0 && <p className="text-slate-500">No rephrasing requests yet.</p>}
      {items.map((h) => (
        <div key={h.id} className="card space-y-2">
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span className="rounded-full bg-brand-500/10 px-2 py-0.5 capitalize text-brand-600">{h.style}</span>
            <span>{h.model}</span>
            <span>{new Date(h.created_at).toLocaleString()}</span>
            {h.similarity_score != null && <span>similarity {(h.similarity_score * 100).toFixed(0)}%</span>}
            <div className="ml-auto flex gap-1">
              <button className="btn-ghost px-2 py-1" onClick={() => fav(h.id)}>{h.is_favorite ? '★' : '☆'}</button>
              <button className="btn-ghost px-2 py-1" onClick={() => navigator.clipboard.writeText(h.rephrased_text)}>Copy</button>
              <button className="btn-ghost px-2 py-1" onClick={() => setOpen(open === h.id ? null : h.id)}>Details</button>
              <button className="btn-ghost px-2 py-1 text-red-500" onClick={() => del(h.id)}>Delete</button>
            </div>
          </div>
          <p className="text-sm text-slate-500">{h.original_text}</p>
          <p className="font-medium">{h.rephrased_text}</p>
          {open === h.id && (
            <div className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-800/60">
              <p>{h.explanation?.summary}</p>
              <p className="mt-1 text-slate-500">
                BLEU {h.metrics?.bleu} · ROUGE-L {h.metrics?.rougeL} · BERTScore {h.metrics?.bertscore_f1 ?? '–'} · Perplexity {h.metrics?.perplexity ?? '–'}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
