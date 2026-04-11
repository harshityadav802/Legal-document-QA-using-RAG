import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { ReactNode } from 'react'
import { checkHealth, listDocuments } from '../services/api'
import type {
  ChatEntry,
  ConnectionStatus,
  DocumentMeta,
  Language,
  UploadState,
  UserPreferences,
} from '../types'

// ─── State shape ─────────────────────────────────────────────────────────────

interface AppState {
  // Backend connectivity
  connectionStatus: ConnectionStatus

  // Document management
  documents: DocumentMeta[]
  refreshDocuments: () => Promise<void>

  // Upload
  uploadState: UploadState
  setUploadState: (s: UploadState) => void

  // Chat / Query
  chatHistory: ChatEntry[]
  addChatEntry: (e: ChatEntry) => void
  clearChat: () => void

  // User preferences
  preferences: UserPreferences
  setPreferences: (p: Partial<UserPreferences>) => void
}

// ─── Defaults ────────────────────────────────────────────────────────────────

const defaultPreferences: UserPreferences = {
  language: 'both',
  theme: 'light',
  numResults: 5,
  ollamaModel: import.meta.env.VITE_OLLAMA_MODEL ?? 'mistral',
  ollamaUrl: import.meta.env.VITE_OLLAMA_URL ?? 'http://localhost:11434',
  indexName: import.meta.env.VITE_INDEX_NAME ?? 'legal_docs',
}

const AppContext = createContext<AppState | undefined>(undefined)

// ─── Provider ────────────────────────────────────────────────────────────────

export function AppProvider({ children }: { children: ReactNode }) {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('unknown')
  const [documents, setDocuments] = useState<DocumentMeta[]>([])
  const [uploadState, setUploadState] = useState<UploadState>({
    status: 'idle',
    progress: 0,
    message: '',
  })
  const [chatHistory, setChatHistory] = useState<ChatEntry[]>([])
  const [preferences, setPreferencesState] = useState<UserPreferences>(() => {
    try {
      const stored = localStorage.getItem('legalqa-preferences')
      return stored ? { ...defaultPreferences, ...JSON.parse(stored) } : defaultPreferences
    } catch {
      return defaultPreferences
    }
  })

  // Apply dark-mode class on html element
  useEffect(() => {
    if (preferences.theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [preferences.theme])

  const setPreferences = useCallback((partial: Partial<UserPreferences>) => {
    setPreferencesState(prev => {
      const next = { ...prev, ...partial }
      localStorage.setItem('legalqa-preferences', JSON.stringify(next))
      return next
    })
  }, [])

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch {
      // Silently ignore – backend may not be available yet
    }
  }, [])

  const addChatEntry = useCallback((entry: ChatEntry) => {
    setChatHistory(prev => [...prev, entry])
  }, [])

  const clearChat = useCallback(() => setChatHistory([]), [])

  // Poll health on mount
  useEffect(() => {
    let cancelled = false
    async function ping() {
      const ok = await checkHealth()
      if (!cancelled) setConnectionStatus(ok ? 'connected' : 'disconnected')
    }
    ping()
    const interval = setInterval(ping, 30_000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  // Load documents once connected
  useEffect(() => {
    if (connectionStatus === 'connected') {
      refreshDocuments()
    }
  }, [connectionStatus, refreshDocuments])

  const value: AppState = {
    connectionStatus,
    documents,
    refreshDocuments,
    uploadState,
    setUploadState,
    chatHistory,
    addChatEntry,
    clearChat,
    preferences,
    setPreferences,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useApp(): AppState {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}

export type { Language }
