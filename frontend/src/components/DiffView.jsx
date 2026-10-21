/** Renders token lists from the backend, highlighting removed / added words. */
const PUNCT = /^[^\w\s]$/
export default function DiffView({ tokens, mode }) {
  return (
    <p className="leading-8">
      {tokens.map((tk, i) => {
        const cls = tk.type === 'equal' ? '' : mode === 'orig'
          ? 'rounded bg-red-100 px-0.5 text-red-700 line-through dark:bg-red-950 dark:text-red-300'
          : 'rounded bg-emerald-100 px-0.5 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
        return <span key={i}>{i > 0 && !PUNCT.test(tk.t) ? ' ' : ''}<span className={cls}>{tk.t}</span></span>
      })}
    </p>
  )
}
