import { useEffect, useState } from 'react'

const CATEGORY_CONFIG = {
  hardware: { emoji: '🔧', colors: 'bg-purple-50 text-purple-700 border-purple-200' },
  service: { emoji: '🛎️', colors: 'bg-blue-50 text-blue-700 border-blue-200' },
  surroundings: { emoji: '🌍', colors: 'bg-green-50 text-green-700 border-green-200' },
  policy: { emoji: '📋', colors: 'bg-orange-50 text-orange-700 border-orange-200' },
}

export default function HotelDashboard({ profile, prevScore }) {
  const [animatedScore, setAnimatedScore] = useState(prevScore ?? profile.completeness.score)
  const [showBars, setShowBars] = useState(false)

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
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-1 tracking-tight">{profile.name}</h2>
        <code className="inline-block text-[11px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-mono mb-1">{profile.property_id}</code>
        <p className="text-gray-500">Hotel Information Overview</p>
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
                { color: 'bg-green-500', label: `${profile.completeness.covered} covered`, emoji: '✅' },
                { color: 'bg-red-400', label: `${profile.completeness.missing} missing`, emoji: '❌' },
                { color: 'bg-yellow-400', label: `${profile.completeness.stale} stale`, emoji: '⏰' },
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

      {/* Dimensions grid */}
      <div className="glass-card rounded-2xl p-6 shadow-md border border-white/60">
        <h3 className="font-bold text-gray-900 mb-5 text-lg flex items-center gap-2">
          📊 Information Coverage
        </h3>
        <div className="space-y-3">
          {profile.dimensions.map((dim, i) => {
            const maxMentions = Math.max(...profile.dimensions.map(d => d.mention_count), 1)
            const width = Math.max((dim.mention_count / maxMentions) * 100, 3)
            const stanceColor = dim.dominant_stance === 'positive' ? 'bg-gradient-to-r from-green-400 to-emerald-500'
              : dim.dominant_stance === 'negative' ? 'bg-gradient-to-r from-red-400 to-rose-500'
              : dim.dominant_stance === 'mixed' ? 'bg-gradient-to-r from-yellow-400 to-amber-500'
              : 'bg-gray-300'
            const cat = CATEGORY_CONFIG[dim.category] || { emoji: '📌', colors: 'bg-gray-50 text-gray-600 border-gray-200' }

            return (
              <div key={dim.key} className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 py-1.5 sm:py-0"
                style={{ animationDelay: `${i * 50}ms` }}>
                <div className="sm:w-44 text-sm text-gray-700 shrink-0 flex items-center gap-2 font-medium">
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

      {/* Recent Activity */}
      {(() => {
        // Build activity feed from dimensions that have snippets & dates
        const activities = profile.dimensions
          .filter(d => d.mention_count > 0 && d.last_mentioned)
          .map(d => ({
            dimension: d.label,
            category: d.category,
            date: d.last_mentioned,
            stance: d.dominant_stance,
            snippets: d.example_snippets || [],
            mentions: d.mention_count,
          }))
          .sort((a, b) => b.date.localeCompare(a.date))

        if (activities.length === 0) return null

        return (
          <div className="glass-card rounded-2xl p-6 shadow-md border border-white/60 mt-6">
            <h3 className="font-bold text-gray-900 mb-4 text-lg flex items-center gap-2">
              🕐 Recent Review Activity
              <span className="text-sm font-normal text-gray-400">({activities.length} dimensions with data)</span>
            </h3>
            <div className="space-y-3">
              {activities.slice(0, 10).map((act, i) => {
                const cat = CATEGORY_CONFIG[act.category] || { emoji: '📌', colors: 'bg-gray-50 text-gray-600 border-gray-200' }
                const stanceIcon = act.stance === 'positive' ? '🟢' : act.stance === 'negative' ? '🔴' : act.stance === 'mixed' ? '🟡' : '⚪'
                return (
                  <div key={i} className="bg-white/60 rounded-xl border border-gray-100 p-4 hover:bg-white/80 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs">{stanceIcon}</span>
                        <span className="text-sm font-semibold text-gray-800">{act.dimension}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${cat.colors}`}>
                          {cat.emoji} {act.category}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400 font-medium">{act.mentions} mentions</span>
                        <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-mono">{act.date}</span>
                      </div>
                    </div>
                    {act.snippets.length > 0 && (
                      <div className="space-y-1.5 ml-5">
                        {act.snippets.slice(0, 2).map((snippet, j) => (
                          <p key={j} className="text-xs text-gray-500 leading-relaxed flex items-start gap-1.5">
                            <span className="text-gray-300 shrink-0 mt-0.5">›</span>
                            <span className="italic">"{snippet.length > 120 ? snippet.slice(0, 120) + '...' : snippet}"</span>
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )
      })()}

      <div className="text-center mt-8 text-sm text-gray-400">
        Based on {profile.review_count.toLocaleString()} reviews
      </div>
    </div>
  )
}
