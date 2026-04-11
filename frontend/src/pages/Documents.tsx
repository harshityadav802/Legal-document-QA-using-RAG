import DocumentList from '../components/DocumentList'
import DocumentUpload from '../components/DocumentUpload'

export default function Documents() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Documents</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
          Manage your ingested legal documents.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <DocumentUpload />
        <DocumentList />
      </div>
    </div>
  )
}
