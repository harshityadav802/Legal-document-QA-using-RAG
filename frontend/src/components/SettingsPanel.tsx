import { Settings, Languages, Hash, Cpu, Globe } from 'lucide-react'
import { usePreferences } from '../hooks/usePreferences'
import type { Language } from '../types'

const LANGUAGE_OPTIONS: { value: Language; label: string }[] = [
  { value: 'both', label: 'English + Hindi' },
  { value: 'english', label: 'English only' },
  { value: 'hindi', label: 'Hindi only' },
]

export default function SettingsPanel() {
  const { preferences, setLanguage, setNumResults, setPreferences } = usePreferences()

  return (
    <div className="card p-6 space-y-6">
      <div className="flex items-center gap-2">
        <Settings className="w-5 h-5 text-legal-500" />
        <h2 className="font-semibold text-lg text-slate-800 dark:text-slate-100">Settings</h2>
      </div>

      {/* Language */}
      <div className="space-y-2">
        <label className="flex items-center gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
          <Languages className="w-4 h-4 text-slate-400" />
          Answer Language
        </label>
        <div className="grid grid-cols-1 gap-2">
          {LANGUAGE_OPTIONS.map(opt => (
            <label
              key={opt.value}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${
                preferences.language === opt.value
                  ? 'border-legal-500 bg-legal-50 dark:bg-legal-900/20 text-legal-700 dark:text-legal-300'
                  : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
              }`}
            >
              <input
                type="radio"
                name="language"
                value={opt.value}
                checked={preferences.language === opt.value}
                onChange={() => setLanguage(opt.value)}
                className="sr-only"
              />
              <div className={`w-3.5 h-3.5 rounded-full border-2 flex-shrink-0 ${
                preferences.language === opt.value ? 'border-legal-500 bg-legal-500' : 'border-slate-300 dark:border-slate-600'
              }`} />
              <span className="text-sm">{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Retrieved chunks */}
      <div className="space-y-2">
        <label className="flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300">
          <span className="flex items-center gap-1.5">
            <Hash className="w-4 h-4 text-slate-400" />
            Retrieved Chunks
          </span>
          <span className="font-bold text-legal-600 dark:text-legal-300">{preferences.numResults}</span>
        </label>
        <input
          type="range"
          min={3}
          max={10}
          step={1}
          value={preferences.numResults}
          onChange={e => setNumResults(Number(e.target.value))}
          className="w-full accent-legal-500"
        />
        <div className="flex justify-between text-xs text-slate-400">
          <span>3</span>
          <span>10</span>
        </div>
      </div>

      {/* Ollama model */}
      <div className="space-y-2">
        <label className="flex items-center gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
          <Cpu className="w-4 h-4 text-slate-400" />
          Ollama Model
        </label>
        <input
          type="text"
          value={preferences.ollamaModel}
          onChange={e => setPreferences({ ollamaModel: e.target.value })}
          className="input-base text-sm font-mono"
          placeholder="mistral"
        />
      </div>

      {/* Index name */}
      <div className="space-y-2">
        <label className="flex items-center gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
          <Globe className="w-4 h-4 text-slate-400" />
          Endee Index
        </label>
        <input
          type="text"
          value={preferences.indexName}
          onChange={e => setPreferences({ indexName: e.target.value })}
          className="input-base text-sm font-mono"
          placeholder="legal_docs"
        />
      </div>
    </div>
  )
}
