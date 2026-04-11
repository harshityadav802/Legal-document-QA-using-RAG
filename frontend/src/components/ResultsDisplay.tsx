import { useState } from 'react'
import { BookOpen, ChevronDown, ChevronUp, Clock, Languages, FileText } from 'lucide-react'
import { useApp } from '../context/AppContext'
import type { ChatEntry } from '../types'

function SourceCard({ src }: { src: { document_name?: string; section?: string; breadcrumb?: string; snippet?: string; chunk_index?: number } }) {
  return (
    <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-3 space-y-1">
      <div className="flex items-center gap-2">
        <FileText className="w-3.5 h-3.5 text-legal-400 flex-shrink-0" />
        <span className="font-medium text-xs text-slate-700 dark:text-slate-300 truncate">
          {src.document_name ?? 'Unknown document'}
        </span>
      </div>
      {(src.section || src.breadcrumb) && (
        <p className="text-xs text-slate-400 pl-5">{src.breadcrumb ?? src.section}</p>
      )}
      {src.snippet && (
        <p className="text-xs text-slate-500 dark:text-slate-400 pl-5 line-clamp-2 leading-relaxed">
          {src.snippet}
        </p>
      )}
    </div>
  )
}

function AnswerCard({ entry }: { entry: ChatEntry }) {
  const [showSources, setShowSources] = useState(false)
  const [lang, setLang] = useState<'english' | 'hindi'>('english')
  const hasBoth = !!(entry.answer.english && entry.answer.hindi)

  return (
    <div className="space-y-3 animate-slide-up">
      {/* Question bubble */}
      <div className="flex justify-end">
        <div className="max-w-[85%] bg-legal-500 text-white rounded-2xl rounded-tr-sm px-4 py-2.5">
          <p className="text-sm">{entry.question}</p>
        </div>
      </div>

      {/* Answer bubble */}
      <div className="flex gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gold-500 flex items-center justify-center">
          <BookOpen className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 space-y-2">
          {/* Language toggle */}
          {hasBoth && (
            <div className="flex gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg w-fit">
              <button
                onClick={() => setLang('english')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  lang === 'english'
                    ? 'bg-white dark:bg-slate-700 text-legal-600 dark:text-legal-300 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                EN
              </button>
              <button
                onClick={() => setLang('hindi')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  lang === 'hindi'
                    ? 'bg-white dark:bg-slate-700 text-legal-600 dark:text-legal-300 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                हिं
              </button>
            </div>
          )}

          {/* Answer text */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-sm px-4 py-3">
            <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
              {hasBoth
                ? (lang === 'english' ? entry.answer.english : entry.answer.hindi)
                : (entry.answer.english ?? entry.answer.hindi ?? entry.answer.error ?? 'No answer returned.')}
            </p>
          </div>

          {/* Meta row */}
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-1 text-xs text-slate-400">
              <Clock className="w-3 h-3" />
              {entry.elapsed.toFixed(2)}s
            </div>
            {entry.answer.sources.length > 0 && (
              <button
                onClick={() => setShowSources(v => !v)}
                className="flex items-center gap-1 text-xs text-legal-500 hover:text-legal-600 font-medium"
              >
                <Languages className="w-3.5 h-3.5" />
                {entry.answer.sources.length} source{entry.answer.sources.length !== 1 ? 's' : ''}
                {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            )}
          </div>

          {/* Sources */}
          {showSources && entry.answer.sources.length > 0 && (
            <div className="grid gap-2 animate-fade-in">
              {entry.answer.sources.map((src, i) => (
                <SourceCard key={i} src={src} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ResultsDisplay() {
  const { chatHistory, clearChat } = useApp()

  if (chatHistory.length === 0) {
    return (
      <div className="card p-12 flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 bg-legal-50 dark:bg-legal-900/20 rounded-full flex items-center justify-center mb-4">
          <BookOpen className="w-8 h-8 text-legal-300" />
        </div>
        <h3 className="font-medium text-slate-600 dark:text-slate-400 mb-1">No conversations yet</h3>
        <p className="text-sm text-slate-400 dark:text-slate-500">
          Upload a document and ask your first question above.
        </p>
      </div>
    )
  }

  return (
    <div className="card p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-legal-500" />
          <h2 className="font-semibold text-lg text-slate-800 dark:text-slate-100">
            Conversation
          </h2>
        </div>
        <button
          onClick={clearChat}
          className="text-xs text-slate-400 hover:text-red-500 transition-colors"
        >
          Clear
        </button>
      </div>

      <div className="space-y-6 max-h-[600px] overflow-y-auto pr-1">
        {chatHistory.map(entry => (
          <AnswerCard key={entry.id} entry={entry} />
        ))}
      </div>
    </div>
  )
}
