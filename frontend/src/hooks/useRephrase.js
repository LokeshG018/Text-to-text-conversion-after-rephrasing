import { useCallback, useState } from 'react'
import * as api from '../services/api.js'

/** Wraps the rephrase API call with loading / error / result state. */
export default function useRephrase() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const run = useCallback(async (payload) => {
    setLoading(true); setError('')
    try { const data = await api.rephrase(payload); setResult(data); return data }
    catch (e) { setError(api.errorMessage(e)) }
    finally { setLoading(false) }
  }, [])

  const reset = useCallback(() => { setResult(null); setError('') }, [])
  return { result, loading, error, run, reset }
}
