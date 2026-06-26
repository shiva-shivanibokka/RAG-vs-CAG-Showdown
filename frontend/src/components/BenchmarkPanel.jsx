import { useState } from 'react'
import { runBenchmark } from '../api'
import ResultsView from './ResultsView'

export default function BenchmarkPanel() {
  const [useJudge, setUseJudge] = useState(true)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleRun = async () => {
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const data = await runBenchmark(useJudge)
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* heading */}
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-black text-gray-900">
          🏆 <span className="bg-gradient-to-r from-amber-500 to-orange-500 bg-clip-text text-transparent">
            Full Tournament
          </span>
        </h2>
        <p className="text-sm text-gray-500">
          10 questions · both fighters · LLM judge · complete scorecard
        </p>
      </div>

      {/* controls */}
      <div className="flex flex-col sm:flex-row items-center gap-4 rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200 p-5">
        <label className="flex items-center gap-3 cursor-pointer flex-1">
          <div
            onClick={() => setUseJudge(!useJudge)}
            className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${useJudge ? 'bg-amber-500' : 'bg-gray-300'}`}
          >
            <div className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${useJudge ? 'translate-x-6' : 'translate-x-1'}`} />
          </div>
          <div>
            <p className="text-sm font-bold text-gray-800">LLM Judge Scoring</p>
            <p className="text-xs text-gray-500">Scores each answer on correctness, completeness, coherence & groundedness</p>
          </div>
        </label>

        <button
          onClick={handleRun}
          disabled={loading}
          className="px-7 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 disabled:from-gray-200 disabled:to-gray-200 disabled:text-gray-400 text-white font-black text-sm shadow-lg shadow-orange-200 transition-all whitespace-nowrap"
        >
          {loading ? '⏳ Running…' : '🏁 Start Tournament'}
        </button>
      </div>

      {/* loading arena */}
      {loading && (
        <div className="rounded-2xl bg-gradient-to-br from-slate-900 to-indigo-950 p-10 text-center space-y-6 border border-indigo-800">
          <div className="flex justify-center items-end gap-6">
            <FighterPill color="blue" label="CAG" loading />
            <div className="text-yellow-400 font-black text-4xl animate-pulse pb-2">⚡</div>
            <FighterPill color="emerald" label="RAG" loading />
          </div>
          <div className="space-y-1">
            <p className="text-white font-bold text-lg">Tournament in progress…</p>
            <p className="text-slate-400 text-sm">10 battle rounds · running in parallel</p>
            {useJudge && <p className="text-amber-400 text-xs">🧑‍⚖️ LLM judge is scoring each round</p>}
            <p className="text-slate-500 text-xs pt-2">This takes 3–10 minutes. Grab a ☕</p>
          </div>
          <LoadingBar />
        </div>
      )}

      {/* error */}
      {error && (
        <div className="rounded-xl bg-red-50 border-2 border-red-200 p-4 text-red-600 text-sm flex gap-2 items-start">
          <span className="text-xl">💥</span>
          <div>
            <p className="font-semibold">Tournament error!</p>
            <p className="text-red-400 text-xs mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {results && <ResultsView data={results} />}
    </div>
  )
}

function FighterPill({ color, label, loading }) {
  const isBlue = color === 'blue'
  return (
    <div className={`flex flex-col items-center gap-2`}>
      <div className={`text-4xl ${loading ? 'animate-bounce' : ''}`} style={{animationDelay: isBlue ? '0ms' : '200ms'}}>
        {isBlue ? '🤖' : '🦾'}
      </div>
      <span className={`font-black text-sm px-3 py-1 rounded-full ${isBlue ? 'bg-blue-600 text-white' : 'bg-emerald-600 text-white'}`}>
        {label}
      </span>
    </div>
  )
}

function LoadingBar() {
  return (
    <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
      <div
        className="h-2 bg-gradient-to-r from-blue-500 via-violet-500 to-emerald-500 rounded-full animate-pulse"
        style={{width: '60%'}}
      />
    </div>
  )
}
