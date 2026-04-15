import { useEffect, useState } from 'react'
import { fetchHotels } from '../api'

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
      <div className="flex justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div>
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Select a Hotel</h2>
        <p className="text-gray-500">Choose a hotel to write a review for</p>
      </div>

      <div className="grid gap-3">
        {hotels.map(hotel => (
          <button
            key={hotel.property_id}
            onClick={() => onSelect(hotel)}
            className="bg-white rounded-xl p-5 flex items-center justify-between hover:shadow-md hover:border-blue-300 border border-gray-200 transition-all cursor-pointer text-left"
          >
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">{hotel.name}</h3>
              <p className="text-sm text-gray-500 mt-1">
                {hotel.review_count} reviews
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">{hotel.completeness.score}%</div>
                <div className="text-xs text-gray-400">completeness</div>
              </div>
              <svg className="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
