import { wordFrequencies } from '../utils/words.js'

const COLORS = ['text-indigo-500', 'text-violet-500', 'text-cyan-600', 'text-emerald-500', 'text-amber-500', 'text-rose-500']

export default function WordCloud({ texts }) {
  const words = wordFrequencies(texts)
  if (!words.length) return <p className="text-sm text-slate-500">Not enough data yet.</p>
  const max = words[0][1]
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      {words.map(([w, c], i) => (
        <span key={w} className={`${COLORS[i % COLORS.length]} font-semibold`} style={{ fontSize: `${0.8 + (c / max) * 1.6}rem` }} title={`${c}×`}>{w}</span>
      ))}
    </div>
  )
}
