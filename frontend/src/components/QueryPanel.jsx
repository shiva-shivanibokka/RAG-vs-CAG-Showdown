import { useState } from 'react'
import { queryBoth } from '../api'

const KB_TOPICS = [
  { label: 'Transformer Architecture',         emoji: '🏗️' },
  { label: 'RAG (Retrieval Augmented Gen.)',    emoji: '🔍' },
  { label: 'CAG (Context Augmented Gen.)',      emoji: '📜' },
  { label: 'Large Language Models',             emoji: '🧠' },
  { label: 'Vector Databases & Embeddings',     emoji: '🗄️' },
  { label: 'Hallucination in LLMs',             emoji: '👻' },
  { label: 'Prompt Engineering',                emoji: '✍️' },
  { label: 'Fine-Tuning vs In-Context Learning',emoji: '🎛️' },
  { label: 'Evaluation Metrics for LLMs',       emoji: '📊' },
  { label: 'Agentic AI & Tool Use',             emoji: '🤖' },
  { label: 'Attention Mechanisms & KV Cache',   emoji: '⚡' },
  { label: 'Neural Network Fundamentals',       emoji: '🕸️' },
  { label: 'Tokenization',                      emoji: '🔤' },
  { label: 'RLHF',                              emoji: '🏆' },
  { label: 'Encoder / Decoder Architectures',   emoji: '🔄' },
  { label: 'Chunking Strategies for RAG',       emoji: '✂️' },
  { label: 'Mixture of Experts (MoE)',          emoji: '🧩' },
  { label: 'Constitutional AI & Safety',        emoji: '🛡️' },
  { label: 'Scaling Laws & Emergent Abilities', emoji: '📈' },
  { label: 'Advanced RAG Techniques',           emoji: '🚀' },
  { label: 'Lost-in-the-Middle Problem',        emoji: '🎯' },
  { label: 'Position Encoding (RoPE, ALiBi)',   emoji: '📐' },
  { label: 'Inference Optimization (vLLM)',     emoji: '⚙️' },
  { label: 'Quantization & Compression',        emoji: '🗜️' },
  { label: 'Production Deployment Trade-offs',  emoji: '🏭' },
  { label: 'When RAG Beats CAG',                emoji: '🥊' },
  { label: 'Embedding Model Selection & MTEB',  emoji: '🎖️' },
  { label: 'Multi-Hop Reasoning',               emoji: '🔗' },
  { label: 'Faithfulness & Hallucination',      emoji: '✅' },
  { label: 'Benchmark Evaluation Design',       emoji: '📋' },
]

const LOW_CONFIDENCE_THRESHOLD = 0.30

export default function QueryPanel({ llmConfig }) {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTopic, setActiveTopic] = useState(null)

  const submit = async (q) => {
    const text = (q ?? question).trim()
    if (!text) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await queryBoth(text, llmConfig)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleTopicClick = (topic) => {
    setActiveTopic(topic.label)
    setResult(null)
    setError(null)
    const q = `Explain ${topic.label} and how it relates to CAG and RAG systems.`
    setQuestion(q)
    submit(q)
  }

  const handleSubmit = (e) => { e.preventDefault(); submit() }

  const ragTopScore = result?.rag?.retrieved_chunks?.[0]?.similarity_score ?? null
  const lowConfidence = ragTopScore !== null && ragTopScore < LOW_CONFIDENCE_THRESHOLD

  return (
    <div className="space-y-6">

      {/* heading */}
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-black text-gray-900">
          🎯 <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
            Pick a Topic or Ask Anything
          </span>
        </h2>
        <p className="text-sm text-gray-500">
          Click any topic below — or type your own question about AI/ML
        </p>
      </div>

      {/* topic grid */}
      <div className="rounded-2xl border border-gray-200 bg-white p-4 space-y-3">
        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">
          📚 30 topics in the knowledge base — click to battle
        </p>
        <div className="flex flex-wrap gap-2">
          {KB_TOPICS.map((t) => {
            const isActive = activeTopic === t.label && loading
            const wasActive = activeTopic === t.label && !loading && result
            return (
              <button
                key={t.label}
                onClick={() => handleTopicClick(t)}
                disabled={loading}
                className={`text-xs px-3 py-1.5 rounded-full font-medium border transition-all ${
                  isActive
                    ? 'bg-violet-600 text-white border-violet-600 animate-pulse'
                    : wasActive
                    ? 'bg-violet-100 text-violet-700 border-violet-300'
                    : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-violet-50 hover:text-violet-700 hover:border-violet-300'
                } disabled:opacity-50`}
              >
                {t.emoji} {t.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* custom question input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => { setQuestion(e.target.value); setActiveTopic(null) }}
          placeholder="Or type your own question about AI/ML…"
          disabled={loading}
          className="flex-1 rounded-xl border-2 border-gray-200 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-violet-400 focus:ring-4 focus:ring-violet-100 transition-all"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700 disabled:from-gray-200 disabled:to-gray-200 disabled:text-gray-400 text-white text-sm font-bold shadow-lg shadow-blue-200 transition-all whitespace-nowrap"
        >
          {loading ? '⚡ Fighting…' : '⚔️ Fight!'}
        </button>
      </form>

      {/* loading arena */}
      {loading && (
        <div className="rounded-2xl bg-gradient-to-br from-slate-900 to-indigo-950 p-8 text-center space-y-4 border border-indigo-800">
          <div className="flex justify-center items-center gap-8">
            <div className="text-4xl animate-bounce" style={{animationDelay:'0ms'}}>🤖</div>
            <div className="text-yellow-400 font-black text-2xl animate-pulse">⚡ VS ⚡</div>
            <div className="text-4xl animate-bounce" style={{animationDelay:'150ms'}}>🤖</div>
          </div>
          {activeTopic && (
            <p className="text-violet-300 text-sm font-semibold">Topic: {activeTopic}</p>
          )}
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
          {lowConfidence && (
            <div className="rounded-xl bg-orange-50 border-2 border-orange-200 p-3 flex gap-2 items-start">
              <span className="text-lg">⚠️</span>
              <div>
                <p className="text-orange-700 text-sm font-semibold">Low retrieval confidence (score: {ragTopScore})</p>
                <p className="text-orange-500 text-xs mt-0.5">
                  This question may not be well-covered in the knowledge base. Try one of the topic buttons above for best results.
                </p>
              </div>
            </div>
          )}

          <BattleVerdict cag={result.cag} rag={result.rag} />

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
        Run the Tournament tab with LLM judge to get scores
      </span>
    </div>
  )
}

function AnswerCard({ fighter, color, data }) {
  const isBlue = color === 'blue'
  const gradient = isBlue ? 'from-blue-600 to-indigo-600' : 'from-emerald-500 to-teal-600'
  const badge   = isBlue ? 'bg-blue-100 text-blue-700'   : 'bg-emerald-100 text-emerald-700'
  const border  = isBlue ? 'border-blue-200'              : 'border-emerald-200'

  return (
    <div className={`rounded-2xl overflow-hidden border-2 ${border} shadow-sm`}>
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
      <div className="bg-white p-5 space-y-3">
        <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{data.answer}</p>
        <div className="flex flex-wrap gap-2 text-xs pt-2 border-t border-gray-100">
          <span className={`${badge} px-2 py-0.5 rounded-full font-medium`}>
            in: {data.input_tokens.toLocaleString()} tok
          </span>
          <span className={`${badge} px-2 py-0.5 rounded-full font-medium`}>
            out: {data.output_tokens.toLocaleString()} tok
          </span>
          {data.retrieved_chunks?.map((c) => (
            <span key={c.title} className="bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full font-medium">
              🔍 {c.title} <span className="opacity-60">({c.similarity_score})</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
