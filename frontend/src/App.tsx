import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppProvider } from './context/AppContext'
import Header from './components/Header'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import './styles/globals.css'
import './styles/variables.css'

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col">
          <Header />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/documents" element={<Documents />} />
            </Routes>
          </main>
          <footer className="border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 py-6 mt-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-sm text-slate-400">
                Legal Document QA · powered by Endee + Mistral
              </p>
              <div className="flex items-center gap-4 text-sm text-slate-400">
                <a
                  href="https://github.com/harshityadav802/Legal-document-QA-using-RAG"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-legal-500 transition-colors"
                >
                  GitHub
                </a>
                <span>·</span>
                <a href="/dashboard" className="hover:text-legal-500 transition-colors">Dashboard</a>
                <span>·</span>
                <a href="/documents" className="hover:text-legal-500 transition-colors">Documents</a>
              </div>
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </AppProvider>
  )
}
