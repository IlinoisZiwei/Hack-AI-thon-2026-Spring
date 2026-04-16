import { useEffect, useState } from 'react'

const CATEGORY_CONFIG = {
  hardware: { emoji: '🔧', colors: 'bg-purple-50 text-purple-700 border-purple-200' },
  service: { emoji: '🛎️', colors: 'bg-blue-50 text-blue-700 border-blue-200' },
  surroundings: { emoji: '🌍', colors: 'bg-green-50 text-green-700 border-green-200' },
  policy: { emoji: '📋', colors: 'bg-amber-50 text-amber-700 border-amber-200' },
}

const STANCE_COLORS = {
  positive: { bg: 'bg-green-500', label: 'Positive', text: 'text-green-700' },
  negative: { bg: 'bg-red-500', label: 'Negative', text: 'text-red-700' },
  mixed: { bg: 'bg-yellow-500', label: 'Mixed', text: 'text-yellow-700' },
  neutral: { bg: 'bg-gray-400', label: 'Neutral', text: 'text-gray-600' },
}

export default function HotelDashboard({ profile, prevScore }) {
  const [animatedScore, setAnimatedScore] = useState(prevScore ?? profile.completeness.score)
  const [showBars, setShowBars] = useState(false)
  const [expandedDim, setExpandedDim] = useState(null)

  useEffect(() => {
    const target = profile.completeness.score
    if (animatedScore !== target) {
      const step = target > animatedScore ? 1 : -1
      const timer = setInterval(() => {
        setAnimatedScore(prev => {
          if (prev === target) { clearInterval(timer); return prev }
          return prev + step
        })
      }, 35)
      return () => clearInterval(timer)
    }
  }, [profile.completeness.score])

  useEffect(() => {
    setTimeout(() => setShowBars(true), 300)
  }, [])

  const improved = prevScore !== null && profile.completeness.score > prevScore
  const scoreColor = animatedScore >= 80 ? '#22c55e' : animatedScore >= 60 ? '#3b82f6' : '#f59e0b'

  return (
    <div>
      {/* Header with monitoring badge */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-1 tracking-tight">{profile.name}</h2>
        <code className="inline-block text-[11px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-mono mb-2">{profile.property_id}</code>
        <div className="flex items-center justify-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
          </span>
          <span className="text-xs text-green-600 font-medium">Monitoring active</span>
        </div>
      </div>

      {/* Completeness score */}
      <div className="glass-card rounded-2xl p-8 shadow-lg border border-white/60 mb-6">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-8">
          <div className="relative w-40 h-40">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
              <defs>
                <linearGradient id="ring-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#22c55e" />
                </linearGradient>
              </defs>
              <circle cx="60" cy="60" r="52" fill="none" stroke="#f1f5f9" strokeWidth="10" />
              <circle
                cx="60" cy="60" r="52" fill="none"
                stroke={improved ? 'url(#ring-grad)' : scoreColor}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={`${animatedScore * 3.267} 326.7`}
                className="transition-all duration-500"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-extrabold text-gray-900 animate-count-up">{animatedScore}%</span>
              <span className="text-xs text-gray-400 font-medium">complete</span>
            </div>
          </div>
          <div className="text-left">
            <div className="space-y-3">
              {[
                { label: `${profile.completeness.covered} covered`, emoji: '✅' },
                { label: `${profile.completeness.missing} missing`, emoji: '❌' },
                { label: `${profile.completeness.stale} stale`, emoji: '⏰' },
              ].map(item => (
                <div key={item.label} className="flex items-center gap-2.5">
                  <span className="text-base">{item.emoji}</span>
                  <span className="text-sm text-gray-600 font-medium">{item.label}</span>
                </div>
              ))}
            </div>
            {improved && (
              <div className="mt-5 bg-gradient-to-r from-green-50 to-emerald-50 text-green-700 px-4 py-2.5 rounded-xl text-base font-bold border border-green-200/60 shadow-sm animate-bounce-in">
                🎉 +{profile.completeness.score - prevScore}% improvement!
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dimensions grid — clickable for drill-down */}
      <div className="glass-card rounded-2xl p-6 shadow-md border border-white/60">
        <h3 className="font-bold text-gray-900 mb-2 text-lg flex items-center gap-2">
          📊 Information Coverage
        </h3>
        <p className="text-xs text-gray-400 mb-5">Click a dimension to see review details</p>
        <div className="space-y-2">
          {profile.dimensions.map((dim, i) => {
            const maxMentions = Math.max(...profile.dimensions.map(d => d.mention_count), 1)
            const width = Math.max((dim.mention_count / maxMentions) * 100, 3)
            const stanceColor = dim.dominant_stance === 'positive' ? 'bg-gradient-to-r from-green-400 to-emerald-500'
              : dim.dominant_stance === 'negative' ? 'bg-gradient-to-r from-red-400 to-rose-500'
              : dim.dominant_stance === 'mixed' ? 'bg-gradient-to-r from-yellow-400 to-amber-500'
              : 'bg-gray-300'
            const cat = CATEGORY_CONFIG[dim.category] || { emoji: '📌', colors: 'bg-gray-50 text-gray-600 border-gray-200' }
            const isExpanded = expandedDim === dim.key

            return (
              <div key={dim.key}>
                {/* Row — clickable */}
                <div
                  className={`flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 py-2 sm:py-1.5 px-2 -mx-2 rounded-xl cursor-pointer transition-all ${
                    isExpanded ? 'bg-teal-50/60 ring-1 ring-teal-200' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setExpandedDim(isExpanded ? null : dim.key)}
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <div className="sm:w-44 text-sm text-gray-700 shrink-0 flex items-center gap-2 font-medium">
                    <svg className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                    {dim.label}
                    {dim.mention_count === 0 && (
                      <span className="text-[10px] bg-red-50 text-red-500 px-1.5 py-0.5 rounded-full border border-red-100">missing</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-1">
                    <div className="flex-1 bg-gray-100 rounded-full h-3.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${stanceColor} transition-all duration-1000`}
                        style={{ width: showBars ? `${width}%` : '0%' }}
                      />
                    </div>
                    <div className="w-20 text-right text-xs text-gray-400 shrink-0 font-medium">
                      {dim.mention_count > 0 ? (
                        <span>{dim.mention_count}</span>
                      ) : (
                        <span className="text-red-400">no data</span>
                      )}
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full whitespace-nowrap border font-medium ${cat.colors}`}>
                      {cat.emoji} {dim.category}
                    </span>
                  </div>
                </div>

                {/* Expanded detail panel */}
                {isExpanded && (
                  <div className="ml-2 mr-2 mb-2 mt-1 bg-white rounded-xl border border-gray-200 p-4 animate-fade-in">
                    {/* Sentiment breakdown */}
                    {dim.mention_count > 0 && (
                      <div className="mb-4">
                        <p className="text-xs text-gray-400 font-medium mb-2 uppercase tracking-wide">Sentiment Breakdown</p>
                        <div className="flex items-center gap-1 h-4 rounded-full overflow-hidden bg-gray-100">
                          {['positive', 'negative', 'mixed', 'neutral'].map(stance => {
                            // Estimate from dominant_stance and mention_count
                            const isMain = dim.dominant_stance === stance
                            const pct = isMain ? 70 : 10
                            if (pct <= 0) return null
                            return (
                              <div
                                key={stance}
                                className={`h-full ${STANCE_COLORS[stance]?.bg || 'bg-gray-300'} transition-all duration-500`}
                                style={{ width: `${pct}%` }}
                                title={`${STANCE_COLORS[stance]?.label}: ~${pct}%`}
                              />
                            )
                          })}
                        </div>
                        <div className="flex gap-3 mt-2">
                          {['positive', 'negative', 'mixed', 'neutral'].map(stance => (
                            <span key={stance} className={`text-[10px] font-medium ${STANCE_COLORS[stance]?.text || 'text-gray-500'}`}>
                              {STANCE_COLORS[stance]?.label}
                              {dim.dominant_stance === stance && ' (dominant)'}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Meta info */}
                    <div className="flex flex-wrap gap-3 mb-3">
                      {dim.last_mentioned && (
                        <span className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-mono">
                          Last: {dim.last_mentioned}
                        </span>
                      )}
                      {dim.has_official_info && (
                        <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded border border-blue-100">
                          ✅ Has official info
                        </span>
                      )}
                    </div>

                    {/* Review snippets */}
                    {dim.example_snippets?.length > 0 ? (
                      <div>
                        <p className="text-xs text-gray-400 font-medium mb-2 uppercase tracking-wide">Review Excerpts</p>
                        <div className="space-y-2">
                          {dim.example_snippets.map((snippet, j) => (
                            <div key={j} className="flex items-start gap-2 bg-gray-50 rounded-lg p-3 border border-gray-100">
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-teal-400 to-cyan-400 flex items-center justify-center text-white text-[10px] font-bold shrink-0 mt-0.5">
                                G{j + 1}
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs text-gray-600 leading-relaxed italic">
                                  "{snippet.length > 200 ? snippet.slice(0, 200) + '...' : snippet}"
                                </p>
                                <p className="text-[10px] text-gray-400 mt-1">Guest review excerpt</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic">No review excerpts available for this dimension.</p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Gaps */}
      {profile.gaps?.length > 0 && (
        <div className="glass-card rounded-2xl p-6 shadow-md border border-white/60 mt-6">
          <h3 className="font-bold text-gray-900 mb-4 text-lg flex items-center gap-2">
            🔍 Remaining Information Gaps
            <span className="text-sm font-normal text-gray-400">({profile.gaps.length})</span>
          </h3>
          <div className="grid gap-2">
            {profile.gaps.map((gap, i) => (
              <div key={i} className="flex items-center justify-between py-2.5 px-4 bg-gray-50/80 rounded-xl border border-gray-100 hover:bg-gray-100/80 transition-colors">
                <span className="text-sm text-gray-700 font-medium">{gap.label}</span>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2.5 py-0.5 rounded-full border font-medium ${
                    gap.reason === 'never_mentioned' ? 'bg-red-50 text-red-600 border-red-100' : 'bg-yellow-50 text-yellow-600 border-yellow-100'
                  }`}>
                    {gap.reason === 'never_mentioned' ? '📭' : '🔄'} {gap.reason_label || gap.reason}
                  </span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    gap.priority >= 3 ? 'bg-red-100 text-red-600' : 'bg-yellow-100 text-yellow-600'
                  }`}>
                    P{gap.priority}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-center mt-8 text-sm text-gray-400">
        Based on {profile.review_count.toLocaleString()} reviews
      </div>
    </div>
  )
}
