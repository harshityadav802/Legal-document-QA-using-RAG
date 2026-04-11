import type { DocumentMeta, QueryRequest, QueryResponse } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options)
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const body = await res.json()
      message = body.detail ?? body.message ?? message
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

// ─── Documents ───────────────────────────────────────────────────────────────

export async function uploadDocument(
  file: File,
  documentName?: string,
  indexName?: string,
): Promise<DocumentMeta> {
  const form = new FormData()
  form.append('file', file)
  if (documentName) form.append('document_name', documentName)
  if (indexName) form.append('index_name', indexName)

  return request<DocumentMeta>('/api/documents/upload', {
    method: 'POST',
    body: form,
  })
}

export async function listDocuments(): Promise<DocumentMeta[]> {
  return request<DocumentMeta[]>('/api/documents')
}

export async function deleteDocument(id: string): Promise<void> {
  await request(`/api/documents/${id}`, { method: 'DELETE' })
}

// ─── Query ───────────────────────────────────────────────────────────────────

export async function queryDocuments(req: QueryRequest): Promise<QueryResponse> {
  return request<QueryResponse>('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export async function getSuggestions(q: string): Promise<string[]> {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  return request<string[]>(`/api/query/suggestions?${params.toString()}`)
}

// ─── Health ──────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`)
    return res.ok
  } catch {
    return false
  }
}
