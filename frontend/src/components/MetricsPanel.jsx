const pct = (v) => (v == null ? '–' : `${(v * 100).toFixed(1)}%`)

function Bar({ label, value, hint }) {
  return (
    <div title={hint}>
      <div className="mb-1 flex justify-between text-xs"><span>{label}</span><span className="font-semibold">{pct(value)}</span></div>
      <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-800">
        <div className="h-2 rounded-full bg-brand-500" style={{ width: `${Math.max(0, Math.min(1, value || 0)) * 100}%` }} />
      </div>
    </div>
  )
}

export default function MetricsPanel({ metrics, explanation, stats, timings }) {
  const sim = metrics.semantic_similarity ?? 0
  const color = sim >= 0.85 ? 'text-emerald-500' : sim >= 0.7 ? 'text-amber-500' : 'text-red-500'
  return (
    <div className="card space-y-5">
      <div className="flex items-center gap-4">
        <div className={`text-4xl font-bold ${color}`}>{(sim * 100).toFixed(0)}%</div>
        <div>
          <div className="font-semibold">Semantic similarity</div>
          <div className="text-sm text-slate-500">{metrics.verdict || explanation?.meaning_label}</div>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Bar label="Semantic similarity (cosine)" value={metrics.semantic_similarity} hint="Sentence-embedding cosine similarity" />
        <Bar label="BERTScore F1" value={metrics.bertscore_f1} hint="Contextual-embedding similarity" />
        <Bar label="BLEU (vs original)" value={metrics.bleu} hint="n-gram overlap; LOW means different wording" />
        <Bar label="ROUGE-L (vs original)" value={metrics.rougeL} hint="Longest common subsequence overlap" />
        <Bar label="Lexical change" value={metrics.lexical_change} hint="How different the wording is" />
        <div className="text-sm"><span className="text-slate-500">Perplexity (fluency, lower = better): </span><b>{metrics.perplexity ?? '–'}</b></div>
      </div>
      <p className="text-xs text-slate-500">A good paraphrase keeps <b>high semantic similarity</b> (meaning) while having <b>lower BLEU/ROUGE</b> (different wording).</p>

      {explanation && (
        <div className="space-y-2 text-sm">
          <h3 className="font-semibold">What changed?</h3>
          <p>{explanation.summary}</p>
          {explanation.replaced?.length > 0 && (
            <ul className="list-disc pl-5">
              {explanation.replaced.map((c, i) => <li key={i}>“{c.from}” → “{c.to}”</li>)}
            </ul>
          )}
          <ul className="list-disc pl-5 text-slate-600 dark:text-slate-300">
            {explanation.structure.notes.map((n, i) => <li key={i}>{n}</li>)}
          </ul>
        </div>
      )}

      {stats && (
        <div className="overflow-x-auto text-sm">
          <table className="w-full text-left">
            <thead><tr className="text-slate-500"><th></th><th>Original</th><th>Rephrased</th></tr></thead>
            <tbody>
              {[['Words', 'words'], ['Sentences', 'sentences'], ['Avg sentence length', 'avg_sentence_length'], ['Unique words', 'unique_words']].map(([l, k]) => (
                <tr key={k}><td className="py-0.5 text-slate-500">{l}</td><td>{stats.original[k]}</td><td>{stats.rephrased[k]}</td></tr>
              ))}
              <tr><td className="py-0.5 text-slate-500">Readability (Flesch)</td><td>{stats.original.readability.flesch_reading_ease} ({stats.original.readability.label})</td><td>{stats.rephrased.readability.flesch_reading_ease} ({stats.rephrased.readability.label})</td></tr>
              <tr><td className="py-0.5 text-slate-500">Detected tone</td><td className="capitalize">{stats.original.tone.label}</td><td className="capitalize">{stats.rephrased.tone.label}</td></tr>
            </tbody>
          </table>
        </div>
      )}
      {timings && <p className="text-xs text-slate-400">Pipeline time (ms): {Object.entries(timings).map(([k, v]) => `${k} ${v}`).join(' · ')}</p>}
    </div>
  )
}
