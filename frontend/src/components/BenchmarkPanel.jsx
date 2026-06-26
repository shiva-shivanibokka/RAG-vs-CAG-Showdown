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
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Run Benchmark</h2>
        <p className="text-sm text-gray-500">
          Runs all 10 questions through CAG and RAG in parallel and scores each answer with an
          LLM judge (1–5 per dimension). Takes 3–10 minutes depending on your model and hardware.
        </p>
      </div>

      <div className="flex items-center gap-6">
        <label className="flex items-center gap-2 text-sm cursor-pointer text-gray-700">
          <input
            type="checkbox"
            checked={useJudge}
            onChange={(e) => setUseJudge(e.target.checked)}
            className="rounded"
          />
          <span>Enable LLM judge scoring</span>
        </label>

        <button
          onClick={handleRun}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-100 disabled:text-gray-400 text-white text-sm font-medium transition-colors"
        >
          {loading ? 'Running benchmark…' : 'Run benchmark'}
        </button>
      </div>

      {loading && (
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-6 text-center space-y-2">
          <div className="text-2xl animate-pulse">⏳</div>
          <p className="text-gray-700 text-sm">Benchmark running — this takes a few minutes.</p>
          <p className="text-gray-400 text-xs">
            CAG and RAG are queried in parallel for each of 10 questions.
            {useJudge && ' LLM judge scoring is enabled.'}
          </p>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-600 text-sm">
          {error}
        </div>
      )}

      {results && <ResultsView data={results} />}
    </div>
  )
}
