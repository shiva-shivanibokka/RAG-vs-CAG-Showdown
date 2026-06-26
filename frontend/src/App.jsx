import { useState } from 'react'
import Header from './components/Header'
import QueryPanel from './components/QueryPanel'
import BenchmarkPanel from './components/BenchmarkPanel'
import HealthStatus from './components/HealthStatus'

const TABS = [
  { id: 'query', label: 'Query' },
  { id: 'benchmark', label: 'Benchmark' },
  { id: 'health', label: 'Health' },
]

export default function App() {
  const [tab, setTab] = useState('query')

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <Header />

      <nav className="border-b border-gray-200 bg-white">
        <div className="max-w-6xl mx-auto px-4 flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-5 py-3 text-sm font-medium transition-colors ${
                tab === t.id
                  ? 'text-blue-600 border-b-2 border-blue-500'
                  : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {tab === 'query' && <QueryPanel />}
        {tab === 'benchmark' && <BenchmarkPanel />}
        {tab === 'health' && <HealthStatus />}
      </main>
    </div>
  )
}
