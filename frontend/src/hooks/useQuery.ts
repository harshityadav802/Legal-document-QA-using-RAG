import { useCallback, useState } from 'react'
import { queryDocuments, getSuggestions } from '../services/api'
import { useApp } from '../context/AppContext'
import type { QueryResponse } from '../types'

// Simple uuid-like id generator
function uuid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export function useQuery() {
  const { preferences, addChatEntry } = useApp()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])

  const ask = useCallback(
    async (question: string): Promise<QueryResponse | null> => {
      setError(null)
      setLoading(true)
      const start = performance.now()
      try {
        const result = await queryDocuments({
          question,
          language: preferences.language,
          k: preferences.numResults,
          index_name: preferences.indexName,
        })
        const elapsed = (performance.now() - start) / 1000
        addChatEntry({
          id: uuid(),
          question,
          answer: result,
          elapsed,
          timestamp: new Date(),
        })
        return result
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Query failed'
        setError(msg)
        return null
      } finally {
        setLoading(false)
      }
    },
    [preferences, addChatEntry],
  )

  const fetchSuggestions = useCallback(async (q: string) => {
    try {
      const s = await getSuggestions(q)
      setSuggestions(s)
    } catch {
      setSuggestions([])
    }
  }, [])

  return { ask, loading, error, suggestions, fetchSuggestions }
}
