import { useEffect, useState } from 'react'
import { fetchHotels } from '../api'

// Simulated distances (km) — in production this would use real geolocation
const MOCK_DISTANCES = [0.3, 1.2, 2.8, 4.5, 5.1, 7.3, 8.6, 11.2, 14.0, 18.5, 22.1, 30.4, 45.0]

function distanceLabel(km) {
  if (km < 1) return `${Math.round(km * 1000)}m away`
  return `${km.toFixed(1)} km away`
}

function distanceBadge(km) {
  if (km < 1) return 'bg-green-50 text-green-700 border-green-200'
  if (km < 5) return 'bg-blue-50 text-blue-700 border-blue-200'
  return 'bg-gray-50 text-gray-500 border-gray-200'
}

export default function UserHotelPicker({ onSelect }) {
  const [hotels, setHotels] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHotels().then(data => {
      // Attach mock distances & sort by nearest
      const withDistance = data.map((h, i) => ({
        ...h,
        distance: MOCK_DISTANCES[i % MOCK_DISTANCES.length],
      }))
      withDistance.sort((a, b) => a.distance - b.distance)
      setHotels(withDistance)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Finding nearby hotels...</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-gray-900 mb-2 tracking-tight">Your Recent Stay</h2>
        <p className="text-gray-500">Which hotel did you just visit?</p>
      </div>

      {/* Nearest hotel highlight */}
      {hotels.length > 0 && (
        <button
          onClick={() => onSelect(hotels[0])}
          className="w-full glass-card hover-lift rounded-2xl p-5 sm:p-6 mb-4 border-2 border-teal-300 bg-gradient-to-r from-teal-50/80 to-cyan-50/80 transition-all cursor-pointer text-left group"
        >
          <div className="flex items-center gap-1.5 mb-3">
            <svg className="w-4 h-4 text-teal-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" /></svg>
            <span className="text-xs font-semibold text-teal-600 uppercase tracking-wide">Nearest to you</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-400 to-cyan-400 flex items-center justify-center text-white text-xl shrink-0 shadow-md">
              🏨
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-gray-900 text-lg group-hover:text-teal-600 transition-colors truncate">{hotels[0].name}</h3>
              <div className="flex items-center gap-3 mt-1">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${distanceBadge(hotels[0].distance)}`}>
                  📍 {distanceLabel(hotels[0].distance)}
                </span>
                <span className="text-xs text-gray-400">{hotels[0].review_count.toLocaleString()} reviews</span>
              </div>
            </div>
            <svg className="w-5 h-5 text-teal-400 group-hover:translate-x-1 transition-transform shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>
      )}

      {/* Other hotels */}
      {hotels.length > 1 && (
        <>
          <p className="text-xs text-gray-400 font-medium mb-2 uppercase tracking-wide">Other nearby hotels</p>
          <div className="grid gap-2">
            {hotels.slice(1).map(hotel => (
              <button
                key={hotel.property_id}
                onClick={() => onSelect(hotel)}
                className="glass-card hover-lift rounded-xl p-3.5 sm:p-4 flex items-center gap-3 border border-gray-200/60 transition-all cursor-pointer text-left group"
              >
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-gray-100 to-gray-50 flex items-center justify-center text-base shrink-0">
                  🏨
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 text-sm group-hover:text-teal-600 transition-colors truncate">{hotel.name}</h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full border ${distanceBadge(hotel.distance)}`}>
                      📍 {distanceLabel(hotel.distance)}
                    </span>
                    <span className="text-[10px] text-gray-400">{hotel.review_count.toLocaleString()} reviews</span>
                  </div>
                </div>
                <svg className="w-4 h-4 text-gray-300 group-hover:text-teal-400 group-hover:translate-x-0.5 transition-all shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
