import { useCallback, useState } from 'react'
import { uploadDocument, deleteDocument } from '../services/api'
import { useApp } from '../context/AppContext'
import type { DocumentMeta } from '../types'

export function useDocuments() {
  const { documents, refreshDocuments, setUploadState } = useApp()
  const [error, setError] = useState<string | null>(null)

  const upload = useCallback(
    async (
      file: File,
      documentName?: string,
      indexName?: string,
    ): Promise<DocumentMeta | null> => {
      setError(null)
      setUploadState({ status: 'uploading', progress: 10, message: 'Uploading…' })
      try {
        setUploadState({ status: 'uploading', progress: 50, message: 'Ingesting document…' })
        const doc = await uploadDocument(file, documentName, indexName)
        setUploadState({ status: 'success', progress: 100, message: 'Document ingested successfully!' })
        await refreshDocuments()
        return doc
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Upload failed'
        setError(msg)
        setUploadState({ status: 'error', progress: 0, message: msg })
        return null
      }
    },
    [refreshDocuments, setUploadState],
  )

  const remove = useCallback(
    async (id: string): Promise<boolean> => {
      setError(null)
      try {
        await deleteDocument(id)
        await refreshDocuments()
        return true
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Delete failed'
        setError(msg)
        return false
      }
    },
    [refreshDocuments],
  )

  return { documents, upload, remove, refresh: refreshDocuments, error }
}
