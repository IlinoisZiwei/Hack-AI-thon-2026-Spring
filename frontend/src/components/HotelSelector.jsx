import { useEffect, useState } from 'react'
import { fetchHotels } from '../api'

const HOTEL_EMOJIS = ['🏨', '🏰', '🌊', '🌿', '✈️', '🌆', '🎭', '☀️', '🏢', '🏖️', '🏠', '📍', '🗺️']

function MiniRing({ score, size = 40 }) {
  const r = (size - 6) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#3b82f6' : '#f59e0b'
  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#e5e7eb" strokeWidth="3" />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="3"
        strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
      <text x={size/2} y={size/2} textAnchor="middle" dominantBaseline="central"
        className="rotate-90 origin-center" fill={color}
        style={{ fontSize: '11px', fontWeight: 700, transform: `rotate(90deg)`, transformOrigin: `${size/2}px ${size/2}px` }}>
        {score}
      </text>
    </svg>
  )
}

export default function HotelSelector({ onSelect }) {
  const [hotels, setHotels] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHotels().then(data => {
      setHotels(data)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Loading hotels...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2 tracking-tight">Select a Hotel</h2>
        <p className="text-gray-500">Choose a property to write your review</p>
      </div>

      <div className="grid gap-3">
        {hotels.map((hotel, idx) => (
          <button
            key={hotel.property_id}
            onClick={() => onSelect(hotel)}
            className="glass-card hover-lift rounded-2xl p-5 flex items-center gap-4 border border-gray-200/60 transition-all cursor-pointer text-left group"
          >
            {/* Emoji avatar */}
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center text-2xl shrink-0 group-hover:scale-110 transition-transform">
              {HOTEL_EMOJIS[idx % HOTEL_EMOJIS.length]}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 truncate group-hover:text-blue-700 transition-colors">{hotel.name}</h3>
              <p className="text-sm text-gray-400 mt-0.5">
                {hotel.review_count.toLocaleString()} reviews
              </p>
            </div>

            {/* Completeness ring */}
            <div className="shrink-0 flex items-center gap-3">
              <MiniRing score={hotel.completeness.score} />
              <svg className="w-5 h-5 text-gray-300 group-hover:text-blue-400 transition-colors group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
