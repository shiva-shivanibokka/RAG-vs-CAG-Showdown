import { useState } from 'react'
import { PROVIDERS, DEFAULT_PROVIDER_ID } from '../providers'

export default function ApiKeyGate({ onConfigSet }) {
  const [providerId, setProviderId] = useState(DEFAULT_PROVIDER_ID)
  const [modelId, setModelId]       = useState(PROVIDERS[0].models[0].id)
  const [key, setKey]               = useState('')
  const [error, setError]           = useState('')

  const provider = PROVIDERS.find(p => p.id === providerId)
  const model    = provider.models.find(m => m.id === modelId) ?? provider.models[0]

  const handleProviderChange = (id) => {
    const p = PROVIDERS.find(p => p.id === id)
    setProviderId(id)
    setModelId(p.models[0].id)
    setError('')
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = key.trim()
    if (!trimmed) { setError('Please enter an API key.'); return }
    const config = { providerId, baseUrl: provider.baseUrl, model: model.id, key: trimmed }
    localStorage.setItem('llm_config', JSON.stringify(config))
    onConfigSet(config)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 to-white flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-lg space-y-4">

        {/* title */}
        <div className="text-center mb-6">
          <div className="text-5xl mb-3">⚔️</div>
          <h1 className="text-3xl font-black text-gray-900 mb-1">CAG vs RAG Showdown</h1>
          <p className="text-gray-500 text-sm">
            Pick your provider, select a model, and enter your API key.
            <br/>Your key goes straight from your browser to the provider — never stored on the server.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">

          {/* step 1 — provider */}
          <div className="bg-white rounded-2xl border-2 border-gray-200 p-5 shadow-sm">
            <p className="text-sm font-semibold text-gray-700 mb-3">1. Choose provider</p>
            <div className="grid grid-cols-5 gap-2">
              {PROVIDERS.map(p => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleProviderChange(p.id)}
                  className={`py-2 px-1 rounded-xl text-xs font-bold border-2 transition-all ${
                    providerId === p.id
                      ? 'bg-violet-600 text-white border-violet-600 shadow-md shadow-violet-200'
                      : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-violet-300 hover:text-violet-700'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Get your key at {provider.keyHint}</p>
          </div>

          {/* step 2 — model */}
          <div className="bg-white rounded-2xl border-2 border-gray-200 p-5 shadow-sm">
            <p className="text-sm font-semibold text-gray-700 mb-3">2. Select model</p>
            <div className="flex flex-col gap-2">
              {provider.models.map(m => (
                <label
                  key={m.id}
                  className={`flex items-center justify-between gap-3 px-4 py-3 rounded-xl border-2 cursor-pointer transition-all ${
                    modelId === m.id
                      ? 'border-violet-400 bg-violet-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="radio"
                      name="model"
                      value={m.id}
                      checked={modelId === m.id}
                      onChange={() => setModelId(m.id)}
                      className="accent-violet-600"
                    />
                    <span className="text-sm font-mono text-gray-800">{m.label}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                      m.tier === 'free'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {m.tier}
                    </span>
                    {!m.cagSafe && (
                      <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-semibold">
                        CAG ❌
                      </span>
                    )}
                  </div>
                </label>
              ))}
            </div>

            {!model.cagSafe && (
              <div className="mt-3 bg-red-50 border border-red-200 rounded-xl p-3 text-xs text-red-700 leading-relaxed">
                ⚠️ <strong>CAG will fail with this model.</strong> {model.warning}
              </div>
            )}
          </div>

          {/* step 3 — key */}
          <div className="bg-white rounded-2xl border-2 border-gray-200 p-5 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              3. Enter API key
            </label>
            <input
              type="password"
              value={key}
              onChange={e => { setKey(e.target.value); setError('') }}
              placeholder={provider.keyPlaceholder}
              className="w-full bg-gray-50 border-2 border-gray-200 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 font-mono text-sm focus:outline-none focus:border-violet-400 focus:ring-4 focus:ring-violet-100 mb-3 transition-all"
            />
            {error && <p className="text-red-500 text-xs mb-3">{error}</p>}
            <button
              type="submit"
              disabled={!key.trim()}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-bold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity shadow-md shadow-blue-200"
            >
              Enter the Arena →
            </button>
          </div>
        </form>

        {/* cost hint */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-700">
          <p className="font-bold mb-1">⚡ Approximate token usage per session</p>
          <p>⚔️ Single Challenge (CAG + RAG): ~17,000 tokens</p>
          <p>🏆 Full Tournament (10 questions + judge): ~185,000 tokens</p>
          <p className="text-amber-500 mt-1">Rates vary by provider and model. Free tiers with sufficient limits work.</p>
        </div>

      </div>
    </div>
  )
}
