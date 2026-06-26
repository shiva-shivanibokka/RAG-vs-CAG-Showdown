import { useState } from 'react'
import { queryBoth } from '../api'

const SUGGESTIONS = [
  'What is the KV cache and how does CAG exploit it?',
  'How does tokenization affect CAG context window capacity?',
  'When does RAG outperform CAG in production?',
  'Compare multi-hop reasoning in CAG vs RAG',
]

export default function QueryPanel() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (q) => {
    const text = q ?? question
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await queryBoth(text.trim())
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => { e.preventDefault(); submit() }

  return (
    <div className="space-y-6">
      {/* heading */}
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-black text-gray-900">
          🎯 <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
            Throw a Challenge
          </span>
        </h2>
        <p className="text-sm text-gray-500">Both fighters answer simultaneously — may the best AI win</p>
      </div>

      {/* input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question and let the battle begin…"
          disabled={loading}
          className="flex-1 rounded-xl border-2 border-gray-200 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-violet-400 focus:ring-4 focus:ring-violet-100 transition-all"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700 disabled:from-gray-200 disabled:to-gray-200 disabled:text-gray-400 text-white text-sm font-bold shadow-lg shadow-blue-200 transition-all"
        >
          {loading ? '⚡ Fighting…' : '⚔️ Fight!'}
        </button>
      </form>

      {/* suggestions */}
      {!result && !loading && (
        <div className="space-y-2">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Suggested battle questions</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => { setQuestion(s); submit(s) }}
                className="text-xs bg-white border border-gray-200 hover:border-violet-300 hover:bg-violet-50 text-gray-600 hover:text-violet-700 px-3 py-1.5 rounded-full transition-all"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* loading arena */}
      {loading && (
        <div className="rounded-2xl bg-gradient-to-br from-slate-900 to-indigo-950 p-8 text-center space-y-4 border border-indigo-800">
          <div className="flex justify-center items-center gap-8">
            <div className="text-4xl animate-bounce" style={{animationDelay:'0ms'}}>🤖</div>
            <div className="text-yellow-400 font-black text-2xl animate-pulse">⚡ VS ⚡</div>
            <div className="text-4xl animate-bounce" style={{animationDelay:'150ms'}}>🤖</div>
          </div>
          <p className="text-white font-bold">Battle in progress…</p>
          <p className="text-slate-400 text-xs">Both CAG and RAG are computing their answers simultaneously</p>
        </div>
      )}

      {/* error */}
      {error && (
        <div className="rounded-xl bg-red-50 border-2 border-red-200 p-4 text-red-600 text-sm flex gap-2 items-start">
          <span className="text-xl">💥</span>
          <div>
            <p className="font-semibold">Battle error!</p>
            <p className="text-red-400 text-xs mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* results */}
      {result && (
        <div className="space-y-4">
          {/* battle verdict */}
          <BattleVerdict cag={result.cag} rag={result.rag} />

          {/* answer cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <AnswerCard fighter="CAG" color="blue" data={result.cag} />
            <AnswerCard fighter="RAG" color="emerald" data={result.rag} />
          </div>
        </div>
      )}
    </div>
  )
}

function BattleVerdict({ cag, rag }) {
  const cagScore = cag.judge_scores?.total ?? null
  const ragScore = rag.judge_scores?.total ?? null
  const cagFaster = cag.latency_seconds < rag.latency_seconds

  if (cagScore !== null && ragScore !== null) {
    const winner = cagScore > ragScore ? 'CAG' : ragScore > cagScore ? 'RAG' : null
    if (winner) {
      const isCAG = winner === 'CAG'
      return (
        <div className={`rounded-2xl p-4 text-center border-2 ${isCAG ? 'bg-blue-50 border-blue-200' : 'bg-emerald-50 border-emerald-200'}`}>
          <span className={`font-black text-lg ${isCAG ? 'text-blue-700' : 'text-emerald-700'}`}>
            🏆 {winner} wins this round!
          </span>
        </div>
      )
    }
    return (
      <div className="rounded-2xl p-4 text-center bg-amber-50 border-2 border-amber-200">
        <span className="font-black text-lg text-amber-700">🤝 It&apos;s a tie!</span>
      </div>
    )
  }

  return (
    <div className="rounded-2xl p-3 text-center bg-gray-50 border border-gray-200">
      <span className="text-sm text-gray-500">
        {cagFaster ? '⚡ CAG was faster' : '⚡ RAG was faster'} &nbsp;·&nbsp;
        Scores available after running the benchmark with LLM judge
      </span>
    </div>
  )
}

function AnswerCard({ fighter, color, data }) {
  const isBlue = color === 'blue'
  const gradient = isBlue
    ? 'from-blue-600 to-indigo-600'
    : 'from-emerald-500 to-teal-600'
  const badge = isBlue ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'
  const border = isBlue ? 'border-blue-200' : 'border-emerald-200'
  const tokenText = isBlue ? 'text-blue-400' : 'text-emerald-400'

  return (
    <div className={`rounded-2xl overflow-hidden border-2 ${border} shadow-sm`}>
      {/* card header */}
      <div className={`bg-gradient-to-r ${gradient} px-5 py-3 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <span className="text-white font-black text-base">{fighter}</span>
          {fighter === 'CAG' && <span className="text-blue-200 text-xs">📜 full context</span>}
          {fighter === 'RAG' && <span className="text-emerald-200 text-xs">🔍 retrieval</span>}
        </div>
        <span className="text-white/80 text-xs font-mono bg-black/20 px-2 py-0.5 rounded-full">
          {data.latency_seconds}s
        </span>
      </div>

      {/* answer body */}
      <div className="bg-white p-5 space-y-3">
        <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{data.answer}</p>

        {/* meta row */}
        <div className={`flex flex-wrap gap-3 text-xs ${tokenText} pt-2 border-t border-gray-100`}>
          <span className={`${badge} px-2 py-0.5 rounded-full font-medium`}>
            in: {data.input_tokens.toLocaleString()} tok
          </span>
          <span className={`${badge} px-2 py-0.5 rounded-full font-medium`}>
            out: {data.output_tokens.toLocaleString()} tok
          </span>
          {data.retrieved_chunks?.length > 0 && (
            <span className="bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full font-medium">
              🔍 {data.retrieved_chunks.map((c) => c.title).join(', ')}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
