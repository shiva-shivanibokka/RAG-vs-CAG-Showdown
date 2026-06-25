export default function Header() {
  return (
    <header className="bg-slate-900 border-b border-slate-800">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
        <span className="text-2xl">⚔️</span>
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight">CAG vs RAG Showdown</h1>
          <p className="text-xs text-slate-400">
            Context Augmented Generation vs Retrieval Augmented Generation
          </p>
        </div>
      </div>
    </header>
  )
}
