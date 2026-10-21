export const STYLES = ['standard', 'professional', 'simple', 'academic', 'creative', 'formal', 'casual', 'concise', 'expand']

export default function StyleSelector({ value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {STYLES.map((s) => (
        <button key={s} type="button" onClick={() => onChange(s)}
          className={`rounded-full border px-3 py-1 text-sm capitalize transition ${value === s
            ? 'border-brand-600 bg-brand-600 text-white'
            : 'border-slate-300 hover:border-brand-500 dark:border-slate-700'}`}>
          {s}
        </button>
      ))}
    </div>
  )
}
