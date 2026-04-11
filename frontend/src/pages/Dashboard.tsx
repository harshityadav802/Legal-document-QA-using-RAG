import DocumentUpload from '../components/DocumentUpload'
import QueryInterface from '../components/QueryInterface'
import ResultsDisplay from '../components/ResultsDisplay'
import SettingsPanel from '../components/SettingsPanel'
import { useApp } from '../context/AppContext'
import { Wifi, WifiOff } from 'lucide-react'

export default function Dashboard() {
  const { connectionStatus } = useApp()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Dashboard</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
          Upload documents and query them in real-time.
        </p>
      </div>

      {/* Offline banner */}
      {connectionStatus === 'disconnected' && (
        <div className="flex items-center gap-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl px-4 py-3">
          <WifiOff className="w-5 h-5 text-amber-500 flex-shrink-0" />
          <div>
            <p className="font-medium text-amber-700 dark:text-amber-300 text-sm">Backend offline</p>
            <p className="text-amber-600 dark:text-amber-400 text-xs">
              Start the API server: <code className="font-mono bg-amber-100 dark:bg-amber-900 px-1 rounded">uvicorn api.main:app --reload</code>
            </p>
          </div>
        </div>
      )}

      {connectionStatus === 'connected' && (
        <div className="flex items-center gap-2 text-xs text-green-600 dark:text-green-400">
          <Wifi className="w-3.5 h-3.5" />
          <span>Backend connected</span>
        </div>
      )}

      {/* Main grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="lg:col-span-1 space-y-6">
          <DocumentUpload />
          <SettingsPanel />
        </div>

        {/* Right column */}
        <div className="lg:col-span-2 space-y-6">
          <QueryInterface />
          <ResultsDisplay />
        </div>
      </div>
    </div>
  )
}
