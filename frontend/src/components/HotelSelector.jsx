import { useEffect, useState } from 'react'
import { fetchHotels } from '../api'

const HOTEL_EMOJIS = ['🏨', '🏰', '🌊', '🌿', '✈️', '🌆', '🎭', '☀️', '🏢', '🏖️', '🏠', '📍', '🗺️']
const CATEGORIES = ['All', 'Large (500+)', 'Medium (100-499)', 'Small (<100)']

function MiniRing({ score, size = 40 }) {
  const r = (size - 6) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#ea580c' : '#f59e0b'
  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#e5e7eb" strokeWidth="3" />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="3"
        strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
      <text x={size/2} y={size/2} textAnchor="middle" dominantBaseline="central"
        fill={color}
        style={{ fontSize: '11px', fontWeight: 700, transform: `rotate(90deg)`, transformOrigin: `${size/2}px ${size/2}px` }}>
        {score}
      </text>
    </svg>
  )
}

export default function HotelSelector({ onSelect }) {
  const [hotels, setHotels] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All')

  useEffect(() => {
    fetchHotels().then(data => {
      setHotels(data)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Loading hotels...</p>
      </div>
    )
  }

  const filtered = hotels.filter(h => {
    const matchSearch = h.name.toLowerCase().includes(search.toLowerCase())
    const matchCat = category === 'All' ? true
      : category === 'Large (500+)' ? h.review_count >= 500
      : category === 'Medium (100-499)' ? h.review_count >= 100 && h.review_count < 500
      : h.review_count < 100
    return matchSearch && matchCat
  })

  return (
    <div>
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-gray-900 mb-2 tracking-tight">Select a Hotel</h2>
        <p className="text-gray-500">Choose a property to write your review</p>
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <div className="flex-1 relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search hotels..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent text-sm"
          />
        </div>
        <div className="flex gap-1.5 overflow-x-auto pb-1">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
                category === cat
                  ? 'bg-orange-500 text-white shadow-sm'
                  : 'bg-white/70 text-gray-500 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <p className="text-xs text-gray-400 mb-3">{filtered.length} hotels found</p>

      {/* Hotel list */}
      <div className="grid gap-3">
        {filtered.map((hotel, idx) => (
          <button
            key={hotel.property_id}
            onClick={() => onSelect(hotel)}
            className="glass-card hover-lift rounded-2xl p-4 sm:p-5 flex flex-row items-center gap-3 sm:gap-4 border border-gray-200/60 transition-all cursor-pointer text-left group"
          >
            {/* Emoji avatar */}
            <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-orange-100 to-amber-100 flex items-center justify-center text-xl sm:text-2xl shrink-0 group-hover:scale-110 transition-transform">
              {HOTEL_EMOJIS[idx % HOTEL_EMOJIS.length]}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 truncate group-hover:text-orange-600 transition-colors text-sm sm:text-base">{hotel.name}</h3>
              <p className="text-xs sm:text-sm text-gray-400 mt-0.5">
                {hotel.review_count.toLocaleString()} reviews
              </p>
            </div>

            {/* Completeness ring + arrow — always horizontal */}
            <div className="shrink-0 flex flex-row items-center gap-2">
              <MiniRing score={hotel.completeness.score} />
              <svg className="w-5 h-5 text-gray-300 group-hover:text-orange-400 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>
        ))}

        {filtered.length === 0 && (
          <div className="text-center py-10 text-gray-400">
            <p className="text-lg">No hotels match your search</p>
            <button onClick={() => { setSearch(''); setCategory('All') }} className="text-orange-500 text-sm mt-2 cursor-pointer hover:underline">
              Clear filters
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
