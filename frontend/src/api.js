const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request(path, options = {}, llmConfig = null) {
  const headers = { 'Content-Type': 'application/json' }
  if (llmConfig?.key) {
    headers['X-OpenAI-Key'] = llmConfig.key
    if (llmConfig.baseUrl) headers['X-OpenAI-Base-URL'] = llmConfig.baseUrl
    if (llmConfig.model)   headers['X-OpenAI-Model']    = llmConfig.model
  }
  const res = await fetch(`${BASE}${path}`, { headers, ...options })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const getHealth = () => request('/health')

export const queryBoth = (question, llmConfig) =>
  request('/query/both', {
    method: 'POST',
    body: JSON.stringify({ question }),
  }, llmConfig)

export const runBenchmark = (useJudge = true, llmConfig) =>
  request('/benchmark', {
    method: 'POST',
    body: JSON.stringify({ use_judge: useJudge }),
  }, llmConfig)
