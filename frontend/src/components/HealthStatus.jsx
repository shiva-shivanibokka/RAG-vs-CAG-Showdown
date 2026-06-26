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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
        <button
          onClick={check}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-xs font-medium text-gray-600 transition-colors"
        >
          {loading ? 'Checking…' : 'Refresh'}
        </button>
      </div>

      {loading && <p className="text-gray-400 text-sm">Checking API…</p>}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-600 text-sm">
          <strong>API unreachable:</strong> {error}
          <p className="mt-1 text-red-400 text-xs">
            Render free tier may be cold-starting (~30s). Try refreshing in a moment.
          </p>
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Status" value={data.status} ok={data.status === 'ok'} />
          <StatCard label="Model" value={data.model} />
          <StatCard label="Provider" value={data.provider} />
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, ok }) {
  return (
    <div className="rounded-lg bg-white border border-gray-200 p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`font-medium text-sm ${ok === false ? 'text-red-500' : 'text-gray-900'}`}>
        {value ?? '—'}
      </p>
    </div>
  )
}
