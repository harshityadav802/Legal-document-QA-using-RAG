// ─── Document types ──────────────────────────────────────────────────────────

export interface DocumentMeta {
  id: string
  name: string
  filename: string
  index_name: string
  chunk_count: number
}

// ─── Query types ─────────────────────────────────────────────────────────────

export type Language = 'both' | 'english' | 'hindi'

export interface Source {
  document_name: string
  section?: string
  section_type?: string
  breadcrumb?: string
  chunk_index?: number
  snippet?: string
}

export interface QueryRequest {
  question: string
  language: Language
  k: number
  index_name?: string
}

export interface QueryResponse {
  english?: string
  hindi?: string
  sources: Source[]
  error?: string
}

// ─── Chat history ────────────────────────────────────────────────────────────

export interface ChatEntry {
  id: string
  question: string
  answer: QueryResponse
  elapsed: number
  timestamp: Date
}

// ─── User preferences ────────────────────────────────────────────────────────

export interface UserPreferences {
  language: Language
  theme: 'light' | 'dark'
  numResults: number
  ollamaModel: string
  ollamaUrl: string
  indexName: string
}

// ─── Upload state ────────────────────────────────────────────────────────────

export type UploadStatus = 'idle' | 'uploading' | 'success' | 'error'

export interface UploadState {
  status: UploadStatus
  progress: number
  message: string
}

// ─── API connection state ────────────────────────────────────────────────────

export type ConnectionStatus = 'unknown' | 'connected' | 'disconnected'
