import { useState } from 'react'
import DiffView from '../components/DiffView.jsx'
import Loader from '../components/Loader.jsx'
import MetricsPanel from '../components/MetricsPanel.jsx'
import StyleSelector from '../components/StyleSelector.jsx'
import useRephrase from '../hooks/useRephrase.js'
import { downloadPdf, downloadTxt } from '../utils/download.js'

export default function Rephraser() {
  const [text, setText] = useState('')
  const [style, setStyle] = useState('standard')
  const [temperature, setTemperature] = useState(0.7)
  const [numResults, setNumResults] = useState(1)
  const [compare, setCompare] = useState(false)
  const [active, setActive] = useState(0)
  const [copied, setCopied] = useState(false)
  const { result, loading, error, run, reset } = useRephrase()

  const words = text.trim() ? text.trim().split(/\s+/).length : 0
  const payload = { text, style, temperature, num_results: numResults, evaluate: true }
  const submit = async () => { setActive(0); await run(payload) }
  const cand = result?.candidates?.[active]
  const shown = cand?.text || ''

  const copy = async () => { await navigator.clipboard.writeText(shown); setCopied(true); setTimeout(() => setCopied(false), 1500) }
  const clear = () => { setText(''); reset(); setActive(0) }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Original text</h2>
            <span className="text-xs text-slate-500">{words} words · {text.length}/5000 chars</span>
          </div>
          <textarea className="input min-h-[220px] resize-y" maxLength={5000} value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Paste or type the text you want to rephrase…" />
          <div><p className="mb-2 text-sm font-medium">Style</p><StyleSelector value={style} onChange={setStyle} /></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm">Creativity (temperature): <b>{temperature.toFixed(2)}</b>
              <input type="range" min="0" max="1.5" step="0.05" value={temperature} onChange={(e) => setTemperature(+e.target.value)} className="w-full" />
              <span className="text-xs text-slate-500">0 = deterministic beam search · higher = more varied</span>
            </label>
            <label className="text-sm">Number of results
              <select className="input mt-1" value={numResults} onChange={(e) => setNumResults(+e.target.value)}>
                {[1, 2, 3].map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="btn-primary" disabled={loading || words < 3} onClick={submit}>✨ Rephrase</button>
            <button className="btn-ghost" disabled={loading || !result} onClick={submit}>🔄 Regenerate</button>
            <button className="btn-ghost" onClick={clear}>Clear</button>
          </div>
          {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-950">{error}</p>}
        </section>

        <section className="card space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">Rephrased text</h2>
            {result && (
              <div className="flex flex-wrap gap-2">
                <button className="btn-ghost" onClick={copy}>{copied ? '✓ Copied' : 'Copy'}</button>
                <button className="btn-ghost" onClick={() => downloadTxt('rephrased.txt', shown)}>TXT</button>
                <button className="btn-ghost" onClick={() => downloadPdf('rephrased.pdf', { original: result.original_text, rephrased: shown, style: result.style, similarity: cand.similarity })}>PDF</button>
              </div>
            )}
          </div>
          {loading ? <Loader label="Preprocessing → generating → evaluating…" /> : result ? (
            <>
              {result.candidates.length > 1 && (
                <div className="flex gap-2">
                  {result.candidates.map((c, i) => (
                    <button key={i} onClick={() => setActive(i)} className={`rounded-full border px-3 py-1 text-xs ${active === i ? 'border-brand-600 bg-brand-600 text-white' : 'border-slate-300 dark:border-slate-700'}`}>
                      {c.is_best ? 'Best' : `Option ${i + 1}`} · {(c.similarity * 100).toFixed(0)}%
                    </button>
                  ))}
                </div>
              )}
              <div className="min-h-[160px] whitespace-pre-wrap rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">{shown}</div>
              <p className="text-xs text-slate-500">Model: {result.model} · style: {result.style} · temperature {result.temperature}</p>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={compare} onChange={(e) => setCompare(e.target.checked)} /> Compare original vs rephrased (highlight changes)</label>
            </>
          ) : <p className="text-sm text-slate-500">Your rephrased text will appear here.</p>}
        </section>
      </div>

      {result && compare && cand && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="card"><h3 className="mb-2 font-semibold">Original <span className="text-xs font-normal text-red-500">(removed words)</span></h3><DiffView tokens={cand.diff.original_tokens} mode="orig" /></div>
          <div className="card"><h3 className="mb-2 font-semibold">Rephrased <span className="text-xs font-normal text-emerald-600">(new words)</span></h3><DiffView tokens={cand.diff.rephrased_tokens} mode="new" /></div>
        </div>
      )}
      {result && !loading && <MetricsPanel metrics={result.metrics} explanation={result.explanation} stats={result.stats} timings={result.timings_ms} />}
    </div>
  )
}
