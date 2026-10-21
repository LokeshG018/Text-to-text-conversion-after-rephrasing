import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getComparison } from '../services/api.js'

const PIPELINE = ['User text', 'Preprocessing', 'Text understanding (tokenizer)', 'Semantic representation (encoder)', 'Generative model (decoder)', 'Post-processing', 'Similarity & quality evaluation', 'Final text']

export default function About() {
  const [cmp, setCmp] = useState(null)
  useEffect(() => { getComparison().then(setCmp).catch(() => setCmp({ available: false })) }, [])
  const rows = cmp?.models?.map((m) => ({ model: m.model, BLEU: m.bleu, 'ROUGE-L': m.rougeL, BERTScore: m.bertscore_f1, Similarity: m.semantic_similarity })) || []
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">About the models</h1>
      <div className="card"><h2 className="mb-3 font-semibold">GenAI pipeline</h2>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {PIPELINE.map((p, i) => <span key={p} className="flex items-center gap-2"><span className="rounded-lg bg-brand-500/10 px-3 py-1 text-brand-600">{p}</span>{i < PIPELINE.length - 1 && '→'}</span>)}
        </div>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        <div className="card text-sm leading-6"><h2 className="mb-2 font-semibold">Why Transformers beat LSTM / GRU</h2>
          <ul className="list-disc pl-5">
            <li><b>Self-attention</b> connects every word to every other word directly; RNNs pass information step-by-step and forget long-range context.</li>
            <li><b>Parallel training</b>: all tokens are processed at once, unlike sequential RNNs.</li>
            <li><b>Pretraining</b> on huge corpora (FLAN-T5 is also instruction-tuned) gives vocabulary and grammar knowledge RNNs trained from scratch lack.</li>
            <li><b>Subword (SentencePiece) tokens</b> avoid out-of-vocabulary words.</li>
          </ul></div>
        <div className="card text-sm leading-6"><h2 className="mb-2 font-semibold">Evaluation metrics</h2>
          <ul className="list-disc pl-5">
            <li><b>Cosine similarity / BERTScore</b> – is the meaning preserved?</li>
            <li><b>BLEU / ROUGE</b> – how much wording overlaps (lower vs the original = more rephrased).</li>
            <li><b>Perplexity</b> – is the output fluent?</li>
          </ul></div>
      </div>
      <div className="card"><h2 className="mb-3 font-semibold">LSTM vs GRU vs Transformer (test set)</h2>
        {cmp?.available ? (
          <ResponsiveContainer width="100%" height={300}><BarChart data={rows}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="model" /><YAxis /><Tooltip /><Legend />
            <Bar dataKey="BLEU" fill="#6366f1" /><Bar dataKey="ROUGE-L" fill="#8b5cf6" /><Bar dataKey="BERTScore" fill="#06b6d4" /><Bar dataKey="Similarity" fill="#10b981" /></BarChart></ResponsiveContainer>
        ) : <p className="text-sm text-slate-500">No comparison yet. Train the models and run <code>python training/evaluate.py</code>.</p>}
      </div>
    </div>
  )
}
