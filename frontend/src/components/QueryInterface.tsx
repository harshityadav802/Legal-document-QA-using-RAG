import { useEffect, useRef, useState } from 'react'
import { Search, Loader2, AlertCircle } from 'lucide-react'
import { useQuery } from '../hooks/useQuery'

export default function QueryInterface() {
  const { ask, loading, error, suggestions, fetchSuggestions } = useQuery()
  const [question, setQuestion] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // Fetch suggestions as the user types
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchSuggestions(question)
    }, 300)
    return () => clearTimeout(timer)
  }, [question, fetchSuggestions])

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleSubmit = async (q?: string) => {
    const text = (q ?? question).trim()
    if (!text || loading) return
    setShowSuggestions(false)
    setQuestion('')
    await ask(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit()
    if (e.key === 'Escape') setShowSuggestions(false)
  }

  return (
    <div className="card p-6 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <Search className="w-5 h-5 text-legal-500" />
        <h2 className="font-semibold text-lg text-slate-800 dark:text-slate-100">Ask a Question</h2>
      </div>
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Ask anything about your ingested legal documents.
      </p>

      <div className="relative">
        <div className="relative flex items-center">
          <Search className="absolute left-3 w-4 h-4 text-slate-400 pointer-events-none" />
          <input
            ref={inputRef}
            type="text"
            placeholder="e.g. What are the termination clauses?"
            value={question}
            onChange={e => {
              setQuestion(e.target.value)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            className="input-base pl-9 pr-4 text-sm"
          />
          {loading && (
            <Loader2 className="absolute right-3 w-4 h-4 animate-spin text-legal-400 pointer-events-none" />
          )}
        </div>

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-20 mt-1 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg overflow-hidden animate-fade-in"
          >
            {suggestions.map((s, i) => (
              <button
                key={i}
                onMouseDown={() => handleSubmit(s)}
                className="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-legal-50 dark:hover:bg-legal-900/20 flex items-center gap-2 transition-colors"
              >
                <Search className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg px-3 py-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      <button
        onClick={() => handleSubmit()}
        disabled={!question.trim() || loading}
        className="btn-primary w-full justify-center"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Searching…
          </>
        ) : (
          <>
            <Search className="w-4 h-4" />
            Ask
          </>
        )}
      </button>
    </div>
  )
}
