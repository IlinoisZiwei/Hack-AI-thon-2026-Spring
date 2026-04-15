import { useEffect, useState } from 'react'

export default function HotelDashboard({ profile, prevScore }) {
  const [animatedScore, setAnimatedScore] = useState(prevScore ?? profile.completeness.score)

  useEffect(() => {
    const target = profile.completeness.score
    if (animatedScore === target) return
    const step = target > animatedScore ? 1 : -1
    const timer = setInterval(() => {
      setAnimatedScore(prev => {
        if (prev === target) { clearInterval(timer); return prev }
        return prev + step
      })
    }, 40)
    return () => clearInterval(timer)
  }, [profile.completeness.score])

  const improved = prevScore !== null && profile.completeness.score > prevScore

  const categoryColors = {
    hardware: 'bg-purple-100 text-purple-700',
    service: 'bg-blue-100 text-blue-700',
    surroundings: 'bg-green-100 text-green-700',
    policy: 'bg-orange-100 text-orange-700',
  }

  return (
    <div>
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-1">{profile.name}</h2>
        <p className="text-gray-500">Hotel Information Dashboard</p>
      </div>

      {/* Completeness score */}
      <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200 mb-6">
        <div className="flex items-center justify-center gap-8">
          <div className="relative w-36 h-36">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="52" fill="none" stroke="#e5e7eb" strokeWidth="10" />
              <circle
                cx="60" cy="60" r="52" fill="none"
                stroke={improved ? '#22c55e' : '#3b82f6'}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={`${animatedScore * 3.267} 326.7`}
                className="transition-all duration-700"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-gray-900">{animatedScore}%</span>
              <span className="text-xs text-gray-400">complete</span>
            </div>
          </div>
          <div className="text-left">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-sm text-gray-600">{profile.completeness.covered} covered</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <span className="text-sm text-gray-600">{profile.completeness.missing} missing</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <span className="text-sm text-gray-600">{profile.completeness.stale} stale</span>
              </div>
            </div>
            {improved && (
              <div className="mt-4 bg-green-50 text-green-700 px-3 py-1.5 rounded-lg text-sm font-medium">
                +{profile.completeness.score - prevScore}% improvement!
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dimensions grid */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-4">Information Coverage</h3>
        <div className="space-y-3">
          {profile.dimensions.map(dim => {
            const maxMentions = Math.max(...profile.dimensions.map(d => d.mention_count), 1)
            const width = Math.max((dim.mention_count / maxMentions) * 100, 3)
            const stanceColor = dim.dominant_stance === 'positive' ? 'bg-green-500'
              : dim.dominant_stance === 'negative' ? 'bg-red-400'
              : dim.dominant_stance === 'mixed' ? 'bg-yellow-500'
              : 'bg-gray-300'

            return (
              <div key={dim.key} className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 py-2 sm:py-0">
                <div className="sm:w-44 text-sm text-gray-700 shrink-0 flex items-center gap-2">
                  {dim.label}
                  {dim.mention_count === 0 && (
                    <span className="text-xs bg-red-50 text-red-500 px-1.5 py-0.5 rounded">missing</span>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-1">
                  <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${stanceColor} transition-all duration-700`}
                      style={{ width: `${width}%` }}
                    />
                  </div>
                  <div className="w-20 text-right text-xs text-gray-400 shrink-0">
                    {dim.mention_count > 0 ? (
                      <span>{dim.mention_count} mentions</span>
                    ) : (
                      <span className="text-red-400">no data</span>
                    )}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${categoryColors[dim.category] || 'bg-gray-100 text-gray-600'}`}>
                    {dim.category}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Gaps */}
      {profile.gaps?.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200 mt-6">
          <h3 className="font-semibold text-gray-900 mb-4">
            Remaining Information Gaps ({profile.gaps.length})
          </h3>
          <div className="grid gap-2">
            {profile.gaps.map((gap, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-700">{gap.label}</span>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    gap.reason === 'never_mentioned' ? 'bg-red-50 text-red-600' : 'bg-yellow-50 text-yellow-600'
                  }`}>
                    {gap.reason_label || gap.reason}
                  </span>
                  <span className={`text-xs font-medium ${
                    gap.priority >= 3 ? 'text-red-500' : 'text-yellow-500'
                  }`}>
                    P{gap.priority}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Review count */}
      <div className="text-center mt-6 text-sm text-gray-400">
        Based on {profile.review_count} reviews
      </div>
    </div>
  )
}
