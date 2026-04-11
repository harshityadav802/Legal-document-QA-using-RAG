import { useState } from 'react'
import { FolderOpen, Trash2, RefreshCw, FileText, AlertCircle, Loader2 } from 'lucide-react'
import { useDocuments } from '../hooks/useDocuments'
import { useApp } from '../context/AppContext'

export default function DocumentList() {
  const { documents, remove, refresh } = useDocuments()
  const { connectionStatus } = useApp()
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const handleDelete = async (id: string) => {
    if (!window.confirm('Remove this document from the registry?')) return
    setDeletingId(id)
    await remove(id)
    setDeletingId(null)
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await refresh()
    setRefreshing(false)
  }

  return (
    <div className="card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderOpen className="w-5 h-5 text-legal-500" />
          <h2 className="font-semibold text-lg text-slate-800 dark:text-slate-100">Documents</h2>
          <span className="badge bg-legal-50 dark:bg-legal-900/30 text-legal-600 dark:text-legal-300">
            {documents.length}
          </span>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 transition-colors"
          aria-label="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {connectionStatus === 'disconnected' && (
        <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg px-3 py-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          Backend offline – showing cached list
        </div>
      )}

      {documents.length === 0 ? (
        <div className="text-center py-10 text-slate-400">
          <FolderOpen className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p className="text-sm">No documents ingested yet.</p>
        </div>
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-slate-700/50">
          {documents.map(doc => (
            <li
              key={doc.id}
              className="flex items-center gap-3 py-3 group"
            >
              <div className="p-2 bg-legal-50 dark:bg-legal-900/20 rounded-lg flex-shrink-0">
                <FileText className="w-4 h-4 text-legal-500" />
              </div>

              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-slate-800 dark:text-slate-200 truncate">
                  {doc.name}
                </p>
                <p className="text-xs text-slate-400 truncate">
                  {doc.filename} · {doc.chunk_count} chunks · {doc.index_name}
                </p>
              </div>

              <button
                onClick={() => handleDelete(doc.id)}
                disabled={deletingId === doc.id}
                className="btn-danger opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                aria-label="Delete document"
              >
                {deletingId === doc.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5" />
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
