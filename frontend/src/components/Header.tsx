import { Link, useLocation } from 'react-router-dom'
import { Scale, Moon, Sun, Wifi, WifiOff, Loader2, FileText, LayoutDashboard, Home } from 'lucide-react'
import { useApp } from '../context/AppContext'
import { usePreferences } from '../hooks/usePreferences'

export default function Header() {
  const { connectionStatus } = useApp()
  const { preferences, toggleTheme } = usePreferences()
  const location = useLocation()

  const navLinks = [
    { to: '/', label: 'Home', icon: Home },
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/documents', label: 'Documents', icon: FileText },
  ]

  return (
    <header className="sticky top-0 z-40 bg-legal-500 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 flex-shrink-0">
            <div className="flex items-center justify-center w-8 h-8 bg-white/10 rounded-lg">
              <Scale className="w-5 h-5 text-gold-400" />
            </div>
            <div className="hidden sm:block">
              <div className="font-bold text-sm leading-tight">Legal Document QA</div>
              <div className="text-white/50 text-xs leading-tight">powered by Endee</div>
            </div>
          </Link>

          {/* Nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname === to
                    ? 'bg-white/20 text-white'
                    : 'text-white/70 hover:text-white hover:bg-white/10'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            ))}
          </nav>

          {/* Right side controls */}
          <div className="flex items-center gap-2">
            {/* Connection status */}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/10 text-xs">
              {connectionStatus === 'unknown' && (
                <Loader2 className="w-3 h-3 animate-spin text-white/70" />
              )}
              {connectionStatus === 'connected' && (
                <Wifi className="w-3 h-3 text-green-400" />
              )}
              {connectionStatus === 'disconnected' && (
                <WifiOff className="w-3 h-3 text-red-400" />
              )}
              <span className="hidden sm:inline text-white/70 capitalize">{connectionStatus}</span>
            </div>

            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              aria-label="Toggle theme"
            >
              {preferences.theme === 'dark' ? (
                <Sun className="w-4 h-4 text-gold-300" />
              ) : (
                <Moon className="w-4 h-4 text-white/80" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="md:hidden border-t border-white/10">
        <div className="flex">
          {navLinks.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`flex-1 flex flex-col items-center gap-1 py-2 text-xs font-medium transition-colors ${
                location.pathname === to
                  ? 'text-white bg-white/10'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </div>
      </div>
    </header>
  )
}
