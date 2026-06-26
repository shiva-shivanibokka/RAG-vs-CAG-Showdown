import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts'

const CAG_COLOR = '#6366f1'
const RAG_COLOR = '#10b981'

const tooltipStyle = {
  backgroundColor: '#fff',
  border: '1px solid #e5e7eb',
  borderRadius: '8px',
  color: '#111827',
  fontSize: '12px',
  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
}

export default function ResultsView({ data }) {
  const { summary, results } = data
  const [selected, setSelected] = useState(results[0]?.id ?? null)

  const scoreData = results.map((r) => ({
    id: r.id,
    CAG: r.cag.judge_scores?.total ?? 0,
    RAG: r.rag.judge_scores?.total ?? 0,
  }))

  const latencyData = results.map((r) => ({
    id: r.id,
    CAG: r.cag.latency_seconds,
    RAG: r.rag.latency_seconds,
  }))

  const selectedQ = results.find((r) => r.id === selected)
  const cagWon = summary.cag.wins > summary.rag.wins
  const ragWon = summary.rag.wins > summary.cag.wins

  return (
    <div className="space-y-6">

      {/* overall winner banner */}
      {(cagWon || ragWon) && (
        <div className={`rounded-2xl p-5 text-center border-2 ${
          cagWon
            ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200'
            : 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200'
        }`}>
          <p className="text-3xl mb-1">🏆</p>
          <p className={`font-black text-xl ${cagWon ? 'text-blue-700' : 'text-emerald-700'}`}>
            {cagWon ? 'CAG' : 'RAG'} wins the tournament!
          </p>
          <p className="text-gray-500 text-sm mt-1">
            {cagWon ? summary.cag.wins : summary.rag.wins} wins vs {cagWon ? summary.rag.wins : summary.cag.wins} — {summary.ties} tie{summary.ties !== 1 ? 's' : ''}
          </p>
        </div>
      )}
      {!cagWon && !ragWon && (
        <div className="rounded-2xl p-5 text-center border-2 bg-amber-50 border-amber-200">
          <p className="text-3xl mb-1">🤝</p>
          <p className="font-black text-xl text-amber-700">Even match — it&apos;s a draw!</p>
        </div>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="CAG avg score" value={`${summary.cag.avg_judge_score}`} max="/5" color="blue" icon="🤖" />
        <KpiCard label="RAG avg score" value={`${summary.rag.avg_judge_score}`} max="/5" color="emerald" icon="🦾" />
        <KpiCard label="CAG avg latency" value={`${summary.cag.avg_latency_seconds}`} max="s" color="indigo" icon="⚡" />
        <KpiCard label="RAG avg latency" value={`${summary.rag.avg_latency_seconds}`} max="s" color="teal" icon="⚡" />
      </div>

      {/* wins row */}
      <div className="grid grid-cols-3 gap-3">
        <WinCard label="CAG wins" value={summary.cag.wins} color="blue" emoji="🤖" />
        <WinCard label="RAG wins" value={summary.rag.wins} color="emerald" emoji="🦾" />
        <WinCard label="Ties" value={summary.ties} color="amber" emoji="🤝" />
      </div>

      {/* charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="⚔️ Judge Score by Question" subtitle="Higher = better (max 5)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={scoreData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="id" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis domain={[0, 5]} tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="CAG" fill={CAG_COLOR} radius={[4, 4, 0, 0]} />
              <Bar dataKey="RAG" fill={RAG_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="⏱️ Latency by Question" subtitle="Lower = faster (seconds)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={latencyData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="id" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="CAG" fill={CAG_COLOR} radius={[4, 4, 0, 0]} />
              <Bar dataKey="RAG" fill={RAG_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* results table */}
      <div className="rounded-2xl overflow-hidden border border-gray-200 shadow-sm">
        <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-4 py-3">
          <p className="text-white font-bold text-sm">📋 Round-by-Round Results</p>
          <p className="text-slate-400 text-xs">Click a row to see full answers</p>
        </div>
        <table className="w-full text-sm bg-white">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-xs font-bold text-gray-500 uppercase tracking-wide">
              <th className="text-left px-4 py-3">Round</th>
              <th className="text-left px-4 py-3 hidden sm:table-cell">Category</th>
              <th className="text-left px-4 py-3">Question</th>
              <th className="text-right px-4 py-3 text-indigo-500">🤖 CAG</th>
              <th className="text-right px-4 py-3 text-emerald-500">🦾 RAG</th>
              <th className="text-right px-4 py-3">Winner</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => {
              const cs = r.cag.judge_scores?.total ?? 0
              const rs = r.rag.judge_scores?.total ?? 0
              const winner = cs > rs ? 'CAG' : rs > cs ? 'RAG' : 'TIE'
              const isSelected = selected === r.id
              return (
                <tr
                  key={r.id}
                  onClick={() => setSelected(r.id)}
                  className={`border-b border-gray-100 cursor-pointer transition-colors ${
                    isSelected ? 'bg-violet-50' : 'hover:bg-gray-50'
                  }`}
                >
                  <td className="px-4 py-3 font-mono text-xs text-gray-400 font-bold">{r.id}</td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">
                      {r.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 max-w-xs">
                    <span className="line-clamp-1 text-xs">
                      {r.question.length > 55 ? r.question.slice(0, 55) + '…' : r.question}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-bold text-indigo-600">{cs || '—'}</td>
                  <td className="px-4 py-3 text-right font-bold text-emerald-600">{rs || '—'}</td>
                  <td className="px-4 py-3 text-right">
                    <WinnerBadge winner={winner} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* per-question detail */}
      {selectedQ && <QuestionDetail q={selectedQ} />}
    </div>
  )
}

function QuestionDetail({ q }) {
  return (
    <div className="rounded-2xl overflow-hidden border-2 border-violet-200 shadow-sm">
      <div className="bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-4">
        <p className="text-violet-200 text-xs font-mono">{q.id} · {q.category}</p>
        <p className="text-white font-bold mt-1">{q.question}</p>
        {q.expected_concepts?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {q.expected_concepts.map((c) => (
              <span key={c} className="bg-white/20 text-white text-xs px-2 py-0.5 rounded-full">{c}</span>
            ))}
          </div>
        )}
      </div>
      <div className="bg-white p-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DetailCard title="🤖 CAG" color="blue" result={q.cag} />
        <DetailCard title="🦾 RAG" color="emerald" result={q.rag} />
      </div>
    </div>
  )
}

function DetailCard({ title, color, result }) {
  const isBlue = color === 'blue'
  const headerGrad = isBlue ? 'from-blue-500 to-indigo-600' : 'from-emerald-500 to-teal-600'
  const scoreBg = isBlue ? 'bg-blue-50' : 'bg-emerald-50'
  const scoreText = isBlue ? 'text-blue-700' : 'text-emerald-700'
  const scores = result.judge_scores ?? {}

  return (
    <div className={`rounded-xl overflow-hidden border ${isBlue ? 'border-blue-200' : 'border-emerald-200'}`}>
      <div className={`bg-gradient-to-r ${headerGrad} px-4 py-2.5 flex justify-between items-center`}>
        <span className="text-white font-bold text-sm">{title}</span>
        <span className="text-white/70 text-xs font-mono">{result.latency_seconds}s</span>
      </div>
      <div className="bg-white p-4 space-y-3">
        <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{result.answer}</p>

        {scores.total !== undefined && (
          <div className={`${scoreBg} rounded-lg p-3 space-y-1.5 text-xs ${scoreText}`}>
            {[
              ['Correctness',  scores.correctness],
              ['Completeness', scores.completeness],
              ['Coherence',    scores.coherence],
              ['Groundedness', scores.groundedness],
            ].map(([label, val]) => (
              <div key={label} className="flex items-center justify-between gap-2">
                <span className="opacity-70 shrink-0">{label}</span>
                <div className="flex items-center gap-1.5 shrink-0">
                  <div className="flex gap-0.5">
                    {[1,2,3,4,5].map(i => (
                      <div key={i} className={`w-2 h-2 rounded-full ${i <= (val ?? 0) ? 'bg-current' : 'bg-current opacity-20'}`} />
                    ))}
                  </div>
                  <span className="font-black w-3 text-right">{val ?? '—'}</span>
                </div>
              </div>
            ))}
            <div className="border-t border-current/20 pt-1.5 flex justify-between font-black text-sm">
              <span>Total</span>
              <span>{scores.total} / 5</span>
            </div>
          </div>
        )}

        {result.retrieved_chunks?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {result.retrieved_chunks.map((c) => (
              <span key={c.title} className="bg-violet-100 text-violet-700 text-xs px-2 py-0.5 rounded-full">
                🔍 {c.title}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function KpiCard({ label, value, max, color, icon }) {
  const colors = {
    blue:    { grad: 'from-blue-500 to-indigo-600',   ring: 'ring-blue-100' },
    emerald: { grad: 'from-emerald-500 to-teal-600',  ring: 'ring-emerald-100' },
    indigo:  { grad: 'from-indigo-500 to-violet-600', ring: 'ring-indigo-100' },
    teal:    { grad: 'from-teal-500 to-cyan-600',     ring: 'ring-teal-100' },
  }
  const { grad, ring } = colors[color] ?? colors.blue
  return (
    <div className={`rounded-2xl overflow-hidden shadow-sm ring-4 ${ring}`}>
      <div className={`bg-gradient-to-br ${grad} p-4 text-white`}>
        <p className="text-xs font-semibold opacity-80">{icon} {label}</p>
        <p className="text-3xl font-black mt-1">
          {value}<span className="text-base font-normal opacity-70">{max}</span>
        </p>
      </div>
    </div>
  )
}

function WinCard({ label, value, color, emoji }) {
  const colors = {
    blue:    'from-blue-50 to-indigo-50 border-blue-200 text-blue-700',
    emerald: 'from-emerald-50 to-teal-50 border-emerald-200 text-emerald-700',
    amber:   'from-amber-50 to-orange-50 border-amber-200 text-amber-700',
  }
  return (
    <div className={`rounded-2xl bg-gradient-to-br ${colors[color]} border-2 p-4 text-center`}>
      <p className="text-3xl font-black">{value}</p>
      <p className="text-xs font-semibold mt-1 opacity-80">{emoji} {label}</p>
    </div>
  )
}

function ChartCard({ title, subtitle, children }) {
  return (
    <div className="rounded-2xl bg-white border border-gray-200 p-4 shadow-sm">
      <p className="text-sm font-bold text-gray-800">{title}</p>
      {subtitle && <p className="text-xs text-gray-400 mb-3">{subtitle}</p>}
      {children}
    </div>
  )
}

function WinnerBadge({ winner }) {
  const styles = {
    CAG: 'bg-indigo-100 text-indigo-700 border border-indigo-200',
    RAG: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
    TIE: 'bg-amber-100 text-amber-700 border border-amber-200',
  }
  const emojis = { CAG: '🤖', RAG: '🦾', TIE: '🤝' }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${styles[winner]}`}>
      {emojis[winner]} {winner}
    </span>
  )
}
