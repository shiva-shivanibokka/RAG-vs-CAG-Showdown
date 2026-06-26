import { useState, useEffect, useCallback } from 'react'
import { getHealth } from '../api'

export default function HealthStatus() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const check = useCallback(() => {
    setLoading(true)
    setError(null)
    setData(null)
    getHealth()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { check() }, [check])

  return (
    <div className="space-y-6">
      {/* heading */}
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-black text-gray-900">
          🛡️ <span className="bg-gradient-to-r from-violet-600 to-cyan-600 bg-clip-text text-transparent">
            Battle HQ
          </span>
        </h2>
        <p className="text-sm text-gray-500">System status and arena configuration</p>
      </div>

      {/* status banner */}
      {loading && (
        <div className="rounded-2xl bg-gradient-to-r from-slate-100 to-slate-200 border-2 border-slate-200 p-6 flex items-center gap-4">
          <div className="w-4 h-4 rounded-full bg-amber-400 animate-pulse flex-shrink-0" />
          <div>
            <p className="font-bold text-gray-700">Contacting battle servers…</p>
            <p className="text-xs text-gray-400">Render free tier may take ~30s to wake up</p>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-2xl bg-gradient-to-r from-red-50 to-orange-50 border-2 border-red-200 p-6 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 rounded-full bg-red-500 flex-shrink-0" />
            <p className="font-bold text-red-700">⚠️ API unreachable</p>
          </div>
          <p className="text-red-500 text-sm">{error}</p>
          <p className="text-red-400 text-xs">
            Render free tier spins down after 15 min of inactivity. First request may take ~30s.
          </p>
          <button
            onClick={check}
            className="px-4 py-2 rounded-xl bg-red-100 hover:bg-red-200 text-red-700 text-sm font-semibold transition-colors"
          >
            🔄 Retry
          </button>
        </div>
      )}

      {data && (
        <div className="space-y-4">
          {/* online banner */}
          <div className="rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 p-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-white animate-pulse" />
              <span className="text-white font-black text-lg">🟢 Battle Servers ONLINE</span>
            </div>
            <button
              onClick={check}
              disabled={loading}
              className="px-3 py-1.5 rounded-xl bg-white/20 hover:bg-white/30 text-white text-xs font-semibold transition-colors"
            >
              Refresh
            </button>
          </div>

          {/* stat cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              label="Status"
              value={data.status?.toUpperCase() ?? '—'}
              icon="🔋"
              gradient="from-emerald-400 to-teal-500"
              ok={data.status === 'ok'}
            />
            <StatCard
              label="LLM Model"
              value={data.model ?? '—'}
              icon="🧠"
              gradient="from-blue-400 to-indigo-500"
            />
            <StatCard
              label="Provider"
              value={data.provider ?? '—'}
              icon="☁️"
              gradient="from-violet-400 to-purple-500"
            />
          </div>

          {/* arena info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InfoCard
              icon="🤖"
              title="CAG Fighter"
              color="blue"
              items={[
                'Loads full knowledge base into LLM context',
                'No retrieval step — pure context reasoning',
                'Advantages: multi-hop, consistency',
                'Weakness: lost-in-the-middle on long KBs',
              ]}
            />
            <InfoCard
              icon="🦾"
              title="RAG Fighter"
              color="emerald"
              items={[
                'Embeds query → FAISS similarity search',
                'Top-3 chunks retrieved per query',
                'Advantages: scalable, precise, fast',
                'Weakness: multi-hop, retrieval misses',
              ]}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, icon, gradient, ok }) {
  return (
    <div className="rounded-2xl overflow-hidden border border-gray-100 shadow-sm">
      <div className={`bg-gradient-to-r ${gradient} px-4 py-2`}>
        <span className="text-white text-xs font-bold uppercase tracking-wider">{icon} {label}</span>
      </div>
      <div className="bg-white px-4 py-3">
        <p className={`font-bold text-sm break-all ${ok === false ? 'text-red-500' : 'text-gray-900'}`}>
          {value}
        </p>
      </div>
    </div>
  )
}

function InfoCard({ icon, title, color, items }) {
  const isBlue = color === 'blue'
  const gradient = isBlue ? 'from-blue-500 to-indigo-600' : 'from-emerald-500 to-teal-600'
  const bg = isBlue ? 'bg-blue-50' : 'bg-emerald-50'
  const dot = isBlue ? 'bg-blue-400' : 'bg-emerald-400'

  return (
    <div className={`rounded-2xl overflow-hidden border border-gray-100 shadow-sm`}>
      <div className={`bg-gradient-to-r ${gradient} px-4 py-3`}>
        <span className="text-white font-black">{icon} {title}</span>
      </div>
      <div className={`${bg} px-4 py-3 space-y-1.5`}>
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${dot} mt-1.5 flex-shrink-0`} />
            <p className="text-xs text-gray-600">{item}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
