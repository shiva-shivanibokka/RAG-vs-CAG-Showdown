import { useState, useEffect } from 'react'
import { getHealth } from '../api'

export default function HealthStatus() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getHealth()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-slate-400">Checking API…</p>

  if (error)
    return (
      <div className="rounded-lg bg-red-950 border border-red-800 p-4 text-red-300">
        <strong>API unreachable:</strong> {error}
      </div>
    )

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">System Status</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Status" value={data.status} ok={data.status === 'ok'} />
        <StatCard label="Model" value={data.model} />
        <StatCard label="Ollama Host" value={data.ollama_host} />
      </div>
    </div>
  )
}

function StatCard({ label, value, ok }) {
  return (
    <div className="rounded-lg bg-slate-800 border border-slate-700 p-4">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className={`font-medium text-sm ${ok === false ? 'text-red-400' : 'text-white'}`}>
        {value}
      </p>
    </div>
  )
}
