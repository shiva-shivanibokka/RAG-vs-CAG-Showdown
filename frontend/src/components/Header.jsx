function CagRobot() {
  return (
    <svg width="90" height="150" viewBox="0 0 100 165" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* antenna */}
      <line x1="50" y1="2" x2="50" y2="18" stroke="#93c5fd" strokeWidth="4" strokeLinecap="round"/>
      <circle cx="50" cy="2" r="6" fill="#60a5fa"/>
      {/* head */}
      <rect x="18" y="18" width="64" height="50" rx="8" fill="#3b82f6"/>
      <rect x="18" y="18" width="64" height="50" rx="8" fill="url(#cagHeadGrad)"/>
      {/* visor band */}
      <rect x="22" y="28" width="56" height="24" rx="5" fill="#1e3a8a" opacity="0.85"/>
      {/* eyes glow */}
      <rect x="27" y="32" width="18" height="14" rx="3" fill="#bfdbfe"/>
      <rect x="27" y="32" width="18" height="14" rx="3" fill="#60a5fa" opacity="0.6"/>
      <circle cx="36" cy="39" r="4" fill="white" opacity="0.9"/>
      <circle cx="38" cy="37" r="1.5" fill="#1e40af"/>
      <rect x="55" y="32" width="18" height="14" rx="3" fill="#bfdbfe"/>
      <rect x="55" y="32" width="18" height="14" rx="3" fill="#60a5fa" opacity="0.6"/>
      <circle cx="64" cy="39" r="4" fill="white" opacity="0.9"/>
      <circle cx="66" cy="37" r="1.5" fill="#1e40af"/>
      {/* mouth */}
      <rect x="28" y="56" width="44" height="7" rx="3" fill="#93c5fd" opacity="0.7"/>
      <rect x="31" y="58" width="6" height="3" rx="1" fill="#1e40af"/>
      <rect x="40" y="58" width="6" height="3" rx="1" fill="#1e40af"/>
      <rect x="49" y="58" width="6" height="3" rx="1" fill="#1e40af"/>
      <rect x="58" y="58" width="6" height="3" rx="1" fill="#1e40af"/>
      {/* neck */}
      <rect x="38" y="68" width="24" height="10" rx="4" fill="#2563eb"/>
      {/* body */}
      <rect x="10" y="78" width="80" height="58" rx="10" fill="#2563eb"/>
      {/* chest panel */}
      <rect x="22" y="88" width="56" height="32" rx="6" fill="#1d4ed8"/>
      <circle cx="35" cy="97" r="5" fill="#60a5fa" opacity="0.9"/>
      <circle cx="50" cy="97" r="5" fill="#34d399" opacity="0.9"/>
      <circle cx="65" cy="97" r="5" fill="#f59e0b" opacity="0.9"/>
      <rect x="28" y="108" width="44" height="4" rx="2" fill="#3b82f6" opacity="0.5"/>
      <rect x="28" y="114" width="30" height="4" rx="2" fill="#3b82f6" opacity="0.3"/>
      {/* left arm */}
      <rect x="-2" y="82" width="16" height="44" rx="7" fill="#3b82f6"/>
      <rect x="-4" y="118" width="20" height="12" rx="5" fill="#1d4ed8"/>
      {/* right arm holding scroll */}
      <rect x="86" y="82" width="16" height="44" rx="7" fill="#3b82f6"/>
      <rect x="84" y="118" width="20" height="12" rx="5" fill="#1d4ed8"/>
      {/* scroll */}
      <rect x="99" y="100" width="14" height="34" rx="4" fill="#fef9c3"/>
      <rect x="97" y="98" width="18" height="5" rx="2.5" fill="#fde68a"/>
      <rect x="97" y="131" width="18" height="5" rx="2.5" fill="#fde68a"/>
      <line x1="102" y1="107" x2="110" y2="107" stroke="#d97706" strokeWidth="1.5"/>
      <line x1="102" y1="112" x2="110" y2="112" stroke="#d97706" strokeWidth="1.5"/>
      <line x1="102" y1="117" x2="110" y2="117" stroke="#d97706" strokeWidth="1.5"/>
      <line x1="102" y1="122" x2="108" y2="122" stroke="#d97706" strokeWidth="1.5"/>
      {/* legs */}
      <rect x="18" y="136" width="28" height="28" rx="7" fill="#1d4ed8"/>
      <rect x="54" y="136" width="28" height="28" rx="7" fill="#1d4ed8"/>
      {/* feet */}
      <rect x="13" y="157" width="36" height="8" rx="4" fill="#1e3a8a"/>
      <rect x="49" y="157" width="36" height="8" rx="4" fill="#1e3a8a"/>
      <defs>
        <linearGradient id="cagHeadGrad" x1="18" y1="18" x2="82" y2="68" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="white" stopOpacity="0.2"/>
          <stop offset="100%" stopColor="white" stopOpacity="0"/>
        </linearGradient>
      </defs>
    </svg>
  )
}

function RagRobot() {
  return (
    <svg width="90" height="150" viewBox="0 0 100 165" fill="none" xmlns="http://www.w3.org/2000/svg" style={{transform:'scaleX(-1)'}}>
      {/* antenna */}
      <line x1="50" y1="2" x2="50" y2="18" stroke="#6ee7b7" strokeWidth="4" strokeLinecap="round"/>
      <circle cx="50" cy="2" r="6" fill="#34d399"/>
      {/* head */}
      <rect x="18" y="18" width="64" height="50" rx="8" fill="#10b981"/>
      <rect x="18" y="18" width="64" height="50" rx="8" fill="url(#ragHeadGrad)"/>
      {/* visor band */}
      <rect x="22" y="28" width="56" height="24" rx="5" fill="#064e3b" opacity="0.85"/>
      {/* eyes glow */}
      <rect x="27" y="32" width="18" height="14" rx="3" fill="#a7f3d0"/>
      <rect x="27" y="32" width="18" height="14" rx="3" fill="#34d399" opacity="0.6"/>
      <circle cx="36" cy="39" r="4" fill="white" opacity="0.9"/>
      <circle cx="38" cy="37" r="1.5" fill="#064e3b"/>
      <rect x="55" y="32" width="18" height="14" rx="3" fill="#a7f3d0"/>
      <rect x="55" y="32" width="18" height="14" rx="3" fill="#34d399" opacity="0.6"/>
      <circle cx="64" cy="39" r="4" fill="white" opacity="0.9"/>
      <circle cx="66" cy="37" r="1.5" fill="#064e3b"/>
      {/* mouth */}
      <rect x="28" y="56" width="44" height="7" rx="3" fill="#6ee7b7" opacity="0.7"/>
      <rect x="31" y="58" width="6" height="3" rx="1" fill="#064e3b"/>
      <rect x="40" y="58" width="6" height="3" rx="1" fill="#064e3b"/>
      <rect x="49" y="58" width="6" height="3" rx="1" fill="#064e3b"/>
      <rect x="58" y="58" width="6" height="3" rx="1" fill="#064e3b"/>
      {/* neck */}
      <rect x="38" y="68" width="24" height="10" rx="4" fill="#059669"/>
      {/* body */}
      <rect x="10" y="78" width="80" height="58" rx="10" fill="#059669"/>
      {/* chest panel */}
      <rect x="22" y="88" width="56" height="32" rx="6" fill="#047857"/>
      <circle cx="35" cy="97" r="5" fill="#34d399" opacity="0.9"/>
      <circle cx="50" cy="97" r="5" fill="#60a5fa" opacity="0.9"/>
      <circle cx="65" cy="97" r="5" fill="#f59e0b" opacity="0.9"/>
      <rect x="28" y="108" width="44" height="4" rx="2" fill="#10b981" opacity="0.5"/>
      <rect x="28" y="114" width="30" height="4" rx="2" fill="#10b981" opacity="0.3"/>
      {/* left arm — holds magnifying glass */}
      <rect x="-2" y="82" width="16" height="44" rx="7" fill="#10b981"/>
      <rect x="-4" y="118" width="20" height="12" rx="5" fill="#047857"/>
      {/* mag glass */}
      <circle cx="-2" cy="106" r="13" stroke="#fef9c3" strokeWidth="3.5"/>
      <circle cx="-2" cy="106" r="8" fill="#bfdbfe" opacity="0.45"/>
      <line x1="8" y1="116" x2="16" y2="124" stroke="#fef9c3" strokeWidth="3.5" strokeLinecap="round"/>
      {/* right arm */}
      <rect x="86" y="82" width="16" height="44" rx="7" fill="#10b981"/>
      <rect x="84" y="118" width="20" height="12" rx="5" fill="#047857"/>
      {/* legs */}
      <rect x="18" y="136" width="28" height="28" rx="7" fill="#047857"/>
      <rect x="54" y="136" width="28" height="28" rx="7" fill="#047857"/>
      {/* feet */}
      <rect x="13" y="157" width="36" height="8" rx="4" fill="#065f46"/>
      <rect x="49" y="157" width="36" height="8" rx="4" fill="#065f46"/>
      <defs>
        <linearGradient id="ragHeadGrad" x1="18" y1="18" x2="82" y2="68" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="white" stopOpacity="0.2"/>
          <stop offset="100%" stopColor="white" stopOpacity="0"/>
        </linearGradient>
      </defs>
    </svg>
  )
}

export default function Header({ onClearKey }) {
  return (
    <header className="relative overflow-hidden bg-gradient-to-b from-indigo-950 via-slate-900 to-slate-800">
      {/* stars */}
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="absolute rounded-full bg-white"
          style={{
            width: i % 3 === 0 ? '3px' : '2px',
            height: i % 3 === 0 ? '3px' : '2px',
            top: `${(i * 37) % 60}%`,
            left: `${(i * 61 + 7) % 95}%`,
            opacity: 0.4 + (i % 3) * 0.2,
          }}
        />
      ))}

      {/* light beams from center */}
      <div className="absolute inset-0 flex justify-center pointer-events-none">
        <div className="w-px h-full bg-gradient-to-b from-yellow-400/0 via-yellow-300/20 to-yellow-400/0" style={{width:'200px'}}/>
      </div>

      <div className="relative max-w-5xl mx-auto px-4 pt-6 pb-0">
        <div className="flex items-end justify-between">

          {/* CAG fighter */}
          <div className="flex flex-col items-center gap-1 min-w-[110px]">
            <div className="text-xs font-bold tracking-widest text-blue-300 uppercase mb-1">Challenger</div>
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-blue-500/20 blur-xl scale-150" />
              <CagRobot />
            </div>
            <div className="bg-blue-600 text-white text-sm font-black px-4 py-1 rounded-full tracking-wide shadow-lg shadow-blue-900/50">
              CAG
            </div>
            <div className="text-blue-300 text-xs text-center">Full Context</div>
          </div>

          {/* VS center */}
          <div className="flex flex-col items-center gap-2 pb-6 flex-1">
            <div className="text-white/60 text-xs tracking-widest uppercase font-semibold">AI Battle Arena</div>
            <div className="relative">
              <div className="absolute inset-0 bg-yellow-400/30 blur-2xl rounded-full scale-150"/>
              <div className="relative bg-gradient-to-br from-yellow-400 to-orange-500 text-gray-900 font-black text-3xl px-6 py-2 rounded-2xl shadow-2xl shadow-yellow-500/40 border-4 border-yellow-300">
                ⚔️ VS ⚔️
              </div>
            </div>
            <div className="text-yellow-300/70 text-xs font-semibold tracking-wider">WHO WINS?</div>
          </div>

          {/* RAG fighter */}
          <div className="flex flex-col items-center gap-1 min-w-[110px]">
            <div className="text-xs font-bold tracking-widest text-emerald-300 uppercase mb-1">Defender</div>
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-emerald-500/20 blur-xl scale-150" />
              <RagRobot />
            </div>
            <div className="bg-emerald-600 text-white text-sm font-black px-4 py-1 rounded-full tracking-wide shadow-lg shadow-emerald-900/50">
              RAG
            </div>
            <div className="text-emerald-300 text-xs text-center">Smart Retrieval</div>
          </div>

        </div>
      </div>

      {/* change key button */}
      {onClearKey && (
        <div className="absolute top-3 right-4">
          <button
            onClick={onClearKey}
            className="text-xs text-slate-400 hover:text-white border border-slate-600 hover:border-slate-400 px-3 py-1 rounded-lg transition-colors"
          >
            🔑 Change Key
          </button>
        </div>
      )}

      {/* ground strip */}
      <div className="relative h-5 bg-gradient-to-r from-green-800 via-green-600 to-green-800 border-t-4 border-green-500 mt-2">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-green-400/20 to-transparent" />
      </div>
    </header>
  )
}
