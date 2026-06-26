const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request(path, options = {}, apiKey = '') {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'X-OpenAI-Key': apiKey } : {}),
    },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const getHealth = () => request('/health')

export const queryBoth = (question, apiKey) =>
  request('/query/both', {
    method: 'POST',
    body: JSON.stringify({ question }),
  }, apiKey)

export const runBenchmark = (useJudge = true, apiKey) =>
  request('/benchmark', {
    method: 'POST',
    body: JSON.stringify({ use_judge: useJudge }),
  }, apiKey)
