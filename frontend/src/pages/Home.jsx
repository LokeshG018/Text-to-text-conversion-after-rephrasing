import { Link } from 'react-router-dom'

const features = [
  ['🧠', 'Transformer-powered', 'Fine-tuned FLAN-T5 encoder-decoder generates the paraphrase.'],
  ['🎛️', '9 writing styles', 'Professional, academic, simple, creative, concise, expand and more.'],
  ['📏', 'Quality evaluation', 'Cosine similarity, BERTScore, BLEU, ROUGE and perplexity for every result.'],
  ['🔍', 'Explainable', 'See replaced words, structure changes and whether meaning was preserved.'],
  ['⚔️', 'LSTM vs GRU vs Transformer', 'Built-in model comparison from real experiments.'],
  ['🔐', 'Private history', 'JWT auth, favourites, dashboard and word cloud.'],
]

export default function Home() {
  return (
    <div className="space-y-12">
      <section className="py-10 text-center">
        <h1 className="text-4xl font-extrabold sm:text-5xl">Say it differently. <span className="text-brand-600">Mean the same.</span></h1>
        <p className="mx-auto mt-4 max-w-2xl text-slate-600 dark:text-slate-300">
          RePhraseAI rewrites your text with a generative Transformer, then measures how well the meaning was preserved.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Link to="/rephrase" className="btn-primary px-6 py-3">Start rephrasing</Link>
          <Link to="/about" className="btn-ghost px-6 py-3">How it works</Link>
        </div>
        <div className="card mx-auto mt-10 max-w-2xl text-left">
          <p className="text-xs uppercase text-slate-400">Example</p>
          <p className="mt-1 text-slate-500">“Artificial intelligence is changing the way businesses operate.”</p>
          <p className="mt-2 font-medium">→ “AI is transforming how modern businesses function.”</p>
        </div>
      </section>
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(([i, t, d]) => (
          <div key={t} className="card"><div className="text-2xl">{i}</div><h3 className="mt-2 font-semibold">{t}</h3><p className="text-sm text-slate-500">{d}</p></div>
        ))}
      </section>
    </div>
  )
}
