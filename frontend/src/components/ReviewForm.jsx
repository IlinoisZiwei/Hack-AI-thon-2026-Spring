import { useState } from 'react'

export default function ReviewForm({ hotel, onSubmit, loading }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (text.trim().length < 1) return
    onSubmit(text)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Write Your Review</h2>
        <p className="text-gray-500">
          Share your experience at <span className="font-medium text-blue-600">{hotel.name}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Tell us about your stay... How was the room? The service? Location? Any tips for future travelers?"
          className="w-full h-40 p-4 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 placeholder-gray-400"
          disabled={loading}
        />

        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-400">
            {text.length} characters
          </span>
          <button
            type="submit"
            disabled={loading || text.trim().length < 1}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                Analyzing...
              </>
            ) : (
              'Submit Review'
            )}
          </button>
        </div>
      </form>

      <div className="mt-4 bg-blue-50 rounded-xl p-4 border border-blue-100">
        <p className="text-sm text-blue-700">
          After submitting, we may ask 1-2 quick follow-up questions to help future travelers.
          You can always skip them!
        </p>
      </div>
    </div>
  )
}
