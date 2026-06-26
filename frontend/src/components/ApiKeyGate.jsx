import { useState } from 'react'

const COSTS = {
  battle: { tokens: 17000, usd: '~$0.003' },
  tournament: { tokens: 185000, usd: '~$0.036' },
}

export default function ApiKeyGate({ onKeySet }) {
  const [key, setKey] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = key.trim()
    if (!trimmed.startsWith('sk-')) {
      setError('OpenAI keys start with "sk-". Check your key and try again.')
      return
    }
    localStorage.setItem('openai_api_key', trimmed)
    onKeySet(trimmed)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center px-4">
      <div className="w-full max-w-lg">

        {/* Title */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">⚔️</div>
          <h1 className="text-3xl font-black text-white mb-1">CAG vs RAG Showdown</h1>
          <p className="text-slate-400 text-sm">Enter your OpenAI API key to begin — it's used directly from your browser, never stored on our server.</p>
        </div>

        {/* Key input */}
        <form onSubmit={handleSubmit} className="bg-slate-800 rounded-2xl border border-slate-700 p-6 mb-4">
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            OpenAI API Key
          </label>
          <input
            type="password"
            value={key}
            onChange={(e) => { setKey(e.target.value); setError('') }}
            placeholder="sk-..."
            className="w-full bg-slate-900 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-500 font-mono text-sm focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 mb-3"
          />
          {error && (
            <p className="text-red-400 text-xs mb-3">{error}</p>
          )}
          <button
            type="submit"
            disabled={!key.trim()}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-bold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
          >
            Enter the Arena →
          </button>
        </form>

        {/* Token usage warning */}
        <div className="bg-amber-950/40 border border-amber-700/50 rounded-2xl p-5 mb-4">
          <p className="text-amber-400 font-bold text-sm mb-3">⚡ Token Usage Per Session</p>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-slate-300">
              <span>⚔️ Single Challenge (CAG + RAG)</span>
              <span className="font-mono text-amber-300">~{COSTS.battle.tokens.toLocaleString()} tokens &nbsp;{COSTS.battle.usd}</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>🏆 Full Tournament (10 questions + judge)</span>
              <span className="font-mono text-amber-300">~{COSTS.tournament.tokens.toLocaleString()} tokens &nbsp;{COSTS.tournament.usd}</span>
            </div>
          </div>
          <p className="text-amber-500/80 text-xs mt-3">Prices based on OpenAI gpt-4o-mini ($0.15/1M input · $0.60/1M output)</p>
        </div>

        {/* Model requirements */}
        <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-5">
          <p className="text-slate-300 font-bold text-sm mb-3">📋 Why CAG needs a capable model</p>
          <p className="text-slate-400 text-xs mb-3">
            CAG loads the <strong className="text-white">entire knowledge base (~13,500 tokens)</strong> into a single request.
            Your model must support a context window larger than this in one call.
          </p>
          <div className="space-y-1.5 text-xs">
            <div className="flex items-center gap-2 text-green-400">
              <span>✅</span>
              <span>OpenAI (any paid tier) — no per-request token cap</span>
            </div>
            <div className="flex items-center gap-2 text-green-400">
              <span>✅</span>
              <span>Anthropic — 200K context window</span>
            </div>
            <div className="flex items-center gap-2 text-green-400">
              <span>✅</span>
              <span>Google Gemini (paid) — 1M context window</span>
            </div>
            <div className="flex items-center gap-2 text-red-400">
              <span>❌</span>
              <span>Groq free tier — hard 12,000 TPM cap (CAG needs 13,500)</span>
            </div>
            <div className="flex items-center gap-2 text-red-400">
              <span>❌</span>
              <span>Most free-tier APIs — token limits too low for CAG</span>
            </div>
          </div>
        </div>

        <p className="text-center text-slate-600 text-xs mt-4">
          Get an OpenAI key at platform.openai.com → API keys
        </p>
      </div>
    </div>
  )
}
