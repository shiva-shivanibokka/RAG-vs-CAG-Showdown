import { useState } from 'react'
import { queryBoth } from '../api'

export default function QueryPanel() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await queryBoth(question.trim())
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Ask a Question</h2>
        <p className="text-sm text-gray-500">
          Sends your question to both CAG and RAG simultaneously and shows the answers side by side.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What is the KV cache and how does CAG exploit it?"
          className="flex-1 rounded-lg bg-white border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-gray-100 disabled:text-gray-400 text-white text-sm font-medium transition-colors"
        >
          {loading ? 'Querying…' : 'Ask'}
        </button>
      </form>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-600 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AnswerCard title="CAG" color="blue" data={result.cag} />
          <AnswerCard title="RAG" color="emerald" data={result.rag} />
        </div>
      )}
    </div>
  )
}

function AnswerCard({ title, color, data }) {
  const borderColor = color === 'blue' ? 'border-blue-300' : 'border-emerald-300'
  const titleColor = color === 'blue' ? 'text-blue-600' : 'text-emerald-600'

  return (
    <div className={`rounded-lg bg-white border ${borderColor} p-5 space-y-3`}>
      <div className="flex items-center justify-between">
        <span className={`text-sm font-bold ${titleColor}`}>{title}</span>
        <span className="text-xs text-gray-400">{data.latency_seconds}s</span>
      </div>
      <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{data.answer}</p>
      <div className="flex gap-4 text-xs text-gray-400 pt-1 border-t border-gray-100">
        <span>in: {data.input_tokens.toLocaleString()} tok</span>
        <span>out: {data.output_tokens.toLocaleString()} tok</span>
        {data.retrieved_chunks?.length > 0 && (
          <span>retrieved: {data.retrieved_chunks.map((c) => c.title).join(', ')}</span>
        )}
      </div>
    </div>
  )
}
