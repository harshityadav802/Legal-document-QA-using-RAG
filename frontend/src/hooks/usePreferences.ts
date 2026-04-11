import { useApp } from '../context/AppContext'
import type { Language } from '../types'

export function usePreferences() {
  const { preferences, setPreferences } = useApp()

  function setLanguage(language: Language) {
    setPreferences({ language })
  }

  function toggleTheme() {
    setPreferences({ theme: preferences.theme === 'dark' ? 'light' : 'dark' })
  }

  function setNumResults(numResults: number) {
    setPreferences({ numResults })
  }

  return {
    preferences,
    setLanguage,
    toggleTheme,
    setNumResults,
    setPreferences,
  }
}
