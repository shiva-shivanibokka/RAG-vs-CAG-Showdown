import { useState } from 'react'
import ApiKeyGate from './components/ApiKeyGate'
import Header from './components/Header'
import QueryPanel from './components/QueryPanel'
import BenchmarkPanel from './components/BenchmarkPanel'
import HealthStatus from './components/HealthStatus'

const TABS = [
  { id: 'query',     label: '⚔️ Challenge',   desc: 'Ask a question' },
  { id: 'benchmark', label: '🏆 Tournament',   desc: 'Full benchmark' },
  { id: 'health',    label: '🛡️ Battle HQ',    desc: 'System status' },
]

export default function App() {
  const [tab, setTab] = useState('query')
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('openai_api_key') || '')

  if (!apiKey) {
    return <ApiKeyGate onKeySet={setApiKey} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 to-white text-gray-900">
      <Header onClearKey={() => { localStorage.removeItem('openai_api_key'); setApiKey('') }} />

      {/* tab bar */}
      <div className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 flex gap-1 py-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                tab === t.id
                  ? 'bg-gradient-to-r from-violet-600 to-blue-600 text-white shadow-md shadow-blue-200'
                  : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div style={{ display: tab === 'query'     ? 'block' : 'none' }}><QueryPanel apiKey={apiKey} /></div>
        <div style={{ display: tab === 'benchmark' ? 'block' : 'none' }}><BenchmarkPanel apiKey={apiKey} /></div>
        <div style={{ display: tab === 'health'    ? 'block' : 'none' }}><HealthStatus /></div>
      </main>
    </div>
  )
}
