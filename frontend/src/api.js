const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const getHealth = () => request('/health')

export const queryBoth = (question) =>
  request('/query/both', {
    method: 'POST',
    body: JSON.stringify({ question }),
  })

export const runBenchmark = (useJudge = true) =>
  request('/benchmark', {
    method: 'POST',
    body: JSON.stringify({ use_judge: useJudge }),
  })
