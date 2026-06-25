import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const CAG_COLOR = '#3b82f6'
const RAG_COLOR = '#10b981'

const tooltipStyle = {
  backgroundColor: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '6px',
  color: '#f1f5f9',
  fontSize: '12px',
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

  return (
    <div className="space-y-6">
      {/* Summary KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="CAG avg score" value={`${summary.cag.avg_judge_score} / 5`} color="blue" />
        <KpiCard label="RAG avg score" value={`${summary.rag.avg_judge_score} / 5`} color="emerald" />
        <KpiCard label="CAG avg latency" value={`${summary.cag.avg_latency_seconds}s`} color="blue" />
        <KpiCard label="RAG avg latency" value={`${summary.rag.avg_latency_seconds}s`} color="emerald" />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <WinCard label="CAG wins" value={summary.cag.wins} color="blue" />
        <WinCard label="RAG wins" value={summary.rag.wins} color="emerald" />
        <WinCard label="Ties" value={summary.ties} color="slate" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Judge Score by Question (0–5)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={scoreData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="id" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 5]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="CAG" fill={CAG_COLOR} radius={[3, 3, 0, 0]} />
              <Bar dataKey="RAG" fill={RAG_COLOR} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Latency by Question (seconds)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={latencyData} margin={{ top: 4, right: 8, bottom: 4, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="id" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="CAG" fill={CAG_COLOR} radius={[3, 3, 0, 0]} />
              <Bar dataKey="RAG" fill={RAG_COLOR} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Results table */}
      <div className="rounded-lg bg-slate-800 border border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 text-slate-400 text-xs">
              <th className="text-left px-4 py-3">ID</th>
              <th className="text-left px-4 py-3">Category</th>
              <th className="text-left px-4 py-3">Question</th>
              <th className="text-right px-4 py-3 text-blue-400">CAG</th>
              <th className="text-right px-4 py-3 text-emerald-400">RAG</th>
              <th className="text-right px-4 py-3">Winner</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => {
              const cs = r.cag.judge_scores?.total ?? 0
              const rs = r.rag.judge_scores?.total ?? 0
              const winner = cs > rs ? 'CAG' : rs > cs ? 'RAG' : 'TIE'
              return (
                <tr
                  key={r.id}
                  onClick={() => setSelected(r.id)}
                  className={`border-b border-slate-700 cursor-pointer transition-colors ${
                    selected === r.id ? 'bg-slate-700' : 'hover:bg-slate-750'
                  }`}
                >
                  <td className="px-4 py-3 font-mono text-xs text-slate-300">{r.id}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{r.category}</td>
                  <td className="px-4 py-3 text-slate-200 max-w-xs truncate">
                    {r.question.length > 60 ? r.question.slice(0, 60) + '…' : r.question}
                  </td>
                  <td className="px-4 py-3 text-right text-blue-400">{cs || '—'}</td>
                  <td className="px-4 py-3 text-right text-emerald-400">{rs || '—'}</td>
                  <td className="px-4 py-3 text-right">
                    <WinnerBadge winner={winner} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Per-question detail */}
      {selectedQ && <QuestionDetail q={selectedQ} />}
    </div>
  )
}

function QuestionDetail({ q }) {
  return (
    <div className="rounded-lg bg-slate-800 border border-slate-700 p-5 space-y-4">
      <div>
        <p className="text-xs text-slate-400 mb-1">
          {q.id} · {q.category}
        </p>
        <p className="text-white font-medium">{q.question}</p>
        {q.expected_concepts?.length > 0 && (
          <p className="text-xs text-slate-500 mt-1">
            Expected: {q.expected_concepts.join(', ')}
          </p>
        )}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DetailCard title="CAG" color="blue" result={q.cag} />
        <DetailCard title="RAG" color="emerald" result={q.rag} />
      </div>
    </div>
  )
}

function DetailCard({ title, color, result }) {
  const titleColor = color === 'blue' ? 'text-blue-400' : 'text-emerald-400'
  const borderColor = color === 'blue' ? 'border-blue-800' : 'border-emerald-800'
  const scores = result.judge_scores ?? {}

  return (
    <div className={`rounded-lg bg-slate-900 border ${borderColor} p-4 space-y-3`}>
      <div className="flex items-center justify-between">
        <span className={`text-sm font-bold ${titleColor}`}>{title}</span>
        <span className="text-xs text-slate-400">{result.latency_seconds}s</span>
      </div>
      <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{result.answer}</p>
      {scores.total !== undefined && (
        <div className="pt-2 border-t border-slate-700 grid grid-cols-2 gap-1 text-xs text-slate-400">
          <span>Correctness: {scores.correctness}</span>
          <span>Completeness: {scores.completeness}</span>
          <span>Coherence: {scores.coherence}</span>
          <span>Groundedness: {scores.groundedness}</span>
          <span className="col-span-2 font-semibold text-white">Total: {scores.total} / 5</span>
        </div>
      )}
      {result.retrieved_chunks?.length > 0 && (
        <p className="text-xs text-slate-500">
          Retrieved: {result.retrieved_chunks.map((c) => c.title).join(', ')}
        </p>
      )}
    </div>
  )
}

function KpiCard({ label, value, color }) {
  const textColor = color === 'blue' ? 'text-blue-400' : 'text-emerald-400'
  return (
    <div className="rounded-lg bg-slate-800 border border-slate-700 p-4">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className={`text-xl font-bold ${textColor}`}>{value}</p>
    </div>
  )
}

function WinCard({ label, value, color }) {
  const textColor =
    color === 'blue' ? 'text-blue-400' : color === 'emerald' ? 'text-emerald-400' : 'text-slate-300'
  return (
    <div className="rounded-lg bg-slate-800 border border-slate-700 p-4 text-center">
      <p className={`text-2xl font-bold ${textColor}`}>{value}</p>
      <p className="text-xs text-slate-400 mt-1">{label}</p>
    </div>
  )
}

function WinnerBadge({ winner }) {
  const styles = {
    CAG: 'bg-blue-900 text-blue-300',
    RAG: 'bg-emerald-900 text-emerald-300',
    TIE: 'bg-slate-700 text-slate-300',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[winner]}`}>{winner}</span>
  )
}
