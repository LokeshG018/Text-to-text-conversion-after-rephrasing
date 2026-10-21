export default function Loader({ label = 'Generating…' }) {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      {label}
    </div>
  )
}
