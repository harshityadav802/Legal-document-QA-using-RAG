import { useCallback, useRef, useState } from 'react'
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { useDocuments } from '../hooks/useDocuments'
import { useApp } from '../context/AppContext'

export default function DocumentUpload() {
  const { upload, error } = useDocuments()
  const { uploadState, setUploadState, preferences } = useApp()
  const [dragging, setDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [docName, setDocName] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const handleFile = (file: File) => {
    setSelectedFile(file)
    setUploadState({ status: 'idle', progress: 0, message: '' })
  }

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const file = e.dataTransfer.files[0]
      if (file) handleFile(file)
    },
    [],
  )

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }
  const onDragLeave = () => setDragging(false)

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const handleSubmit = async () => {
    if (!selectedFile) return
    const result = await upload(selectedFile, docName || undefined, preferences.indexName)
    if (result) {
      setSelectedFile(null)
      setDocName('')
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const clearSelection = () => {
    setSelectedFile(null)
    setDocName('')
    setUploadState({ status: 'idle', progress: 0, message: '' })
    if (fileRef.current) fileRef.current.value = ''
  }

  const isUploading = uploadState.status === 'uploading'

  return (
    <div className="card p-6 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <Upload className="w-5 h-5 text-legal-500" />
        <h2 className="font-semibold text-lg text-slate-800 dark:text-slate-100">Upload Document</h2>
      </div>
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Supported formats: PDF, DOCX, TXT
      </p>

      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => !selectedFile && fileRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
          ${dragging ? 'border-legal-500 bg-legal-50 dark:bg-legal-900/20' : 'border-slate-200 dark:border-slate-700 hover:border-legal-400'}
          ${selectedFile ? 'cursor-default' : ''}`}
      >
        {selectedFile ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-legal-50 dark:bg-legal-900/30 rounded-lg">
                <FileText className="w-6 h-6 text-legal-500" />
              </div>
              <div className="text-left">
                <p className="font-medium text-sm text-slate-800 dark:text-slate-200">{selectedFile.name}</p>
                <p className="text-xs text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); clearSelection() }}
              className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="mx-auto w-12 h-12 flex items-center justify-center rounded-full bg-legal-50 dark:bg-legal-900/20">
              <Upload className="w-6 h-6 text-legal-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
                Drag & drop or <span className="text-legal-500">browse</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">PDF, DOCX, or TXT up to 50 MB</p>
            </div>
          </div>
        )}
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={onFileChange}
          className="hidden"
        />
      </div>

      {/* Document name input */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Document name <span className="text-slate-400 font-normal">(optional)</span>
        </label>
        <input
          type="text"
          placeholder="e.g. Smith v. Jones 2024"
          value={docName}
          onChange={e => setDocName(e.target.value)}
          className="input-base text-sm"
        />
      </div>

      {/* Progress */}
      {isUploading && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-slate-500">
            <span>{uploadState.message}</span>
            <span>{uploadState.progress}%</span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
            <div
              className="bg-legal-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${uploadState.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Feedback messages */}
      {uploadState.status === 'success' && (
        <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 rounded-lg px-3 py-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          {uploadState.message}
        </div>
      )}
      {(uploadState.status === 'error' || error) && (
        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg px-3 py-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {uploadState.message || error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!selectedFile || isUploading}
        className="btn-primary w-full justify-center"
      >
        {isUploading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Ingesting…
          </>
        ) : (
          <>
            <Upload className="w-4 h-4" />
            Ingest Document
          </>
        )}
      </button>
    </div>
  )
}
