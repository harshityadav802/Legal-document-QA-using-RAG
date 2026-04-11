import { Link } from 'react-router-dom'
import { Scale, FileSearch, Zap, Globe, ArrowRight, CheckCircle } from 'lucide-react'

const features = [
  {
    icon: FileSearch,
    title: 'Semantic Search',
    description: 'Hybrid dense + BM25 retrieval across all ingested documents.',
  },
  {
    icon: Globe,
    title: 'Bilingual Answers',
    description: 'Responses in English and Hindi with a single toggle.',
  },
  {
    icon: Zap,
    title: 'Fast & Accurate',
    description: 'Powered by Mistral LLM via Ollama and the Endee vector store.',
  },
]

const supportedTypes = [
  'Court Judgments',
  'NDAs',
  'MOUs',
  'Service Agreements',
  'Employment Contracts',
  'Lease Agreements',
  'Partnership Deeds',
  'General Contracts',
]

export default function Home() {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero */}
      <section className="relative bg-gradient-to-br from-legal-500 to-legal-700 text-white overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-5">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 mb-6">
              <div className="p-2 bg-white/10 rounded-lg">
                <Scale className="w-6 h-6 text-gold-300" />
              </div>
              <span className="text-white/70 text-sm font-medium">Legal Document QA System</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
              Intelligent Answers<br />
              <span className="text-gold-300">from Legal Documents</span>
            </h1>

            <p className="text-lg text-white/80 leading-relaxed mb-8 max-w-xl">
              Upload legal documents, ask questions in plain language, and get accurate
              bilingual answers with cited sources — powered by RAG and Mistral.
            </p>

            <div className="flex flex-wrap gap-3">
              <Link to="/dashboard" className="btn-primary bg-gold-500 hover:bg-gold-600 text-white border-0 px-6 py-3 text-base">
                Open Dashboard
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link to="/documents" className="btn-secondary bg-white/10 hover:bg-white/20 text-white border-white/20 px-6 py-3 text-base">
                Manage Documents
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800 dark:text-slate-100 mb-3">
            How it Works
          </h2>
          <p className="text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            A modern RAG pipeline that makes legal documents searchable and understandable.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {features.map(({ icon: Icon, title, description }) => (
            <div key={title} className="card p-6 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 bg-legal-50 dark:bg-legal-900/20 rounded-lg flex items-center justify-center mb-4">
                <Icon className="w-5 h-5 text-legal-500" />
              </div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">{title}</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Supported document types */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="card p-8">
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-2">
            Supported Document Types
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mb-6">
            The system automatically detects the type of legal document and segments it intelligently.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {supportedTypes.map(type => (
              <div
                key={type}
                className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-slate-900 rounded-lg"
              >
                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{type}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-legal-500 to-legal-600 rounded-2xl p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-2">Ready to get started?</h2>
          <p className="text-white/70 mb-6">Upload your first document and ask a question in seconds.</p>
          <Link to="/dashboard" className="inline-flex items-center gap-2 px-6 py-3 bg-white text-legal-600 font-semibold rounded-xl hover:bg-slate-50 transition-colors">
            Go to Dashboard <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  )
}
