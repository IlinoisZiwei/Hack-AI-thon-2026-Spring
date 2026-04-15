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
        <h2 className="text-3xl font-bold text-gray-900 mb-2 tracking-tight">Write Your Review</h2>
        <p className="text-gray-500">
          Share your experience at <span className="font-semibold gradient-text">{hotel.name}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-card rounded-2xl p-6 sm:p-8 shadow-md border border-white/60">
        {/* User avatar hint */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
            U
          </div>
          <span className="text-sm text-gray-500">Writing as a guest...</span>
        </div>

        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Tell us about your stay... How was the room? The service? Location? Any tips for future travelers?"
          className="w-full h-36 p-4 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 placeholder-gray-400 bg-white/80 transition-shadow"
          disabled={loading}
        />

        {/* AI analysis hint */}
        {text.length > 3 && !loading && (
          <div className="flex items-center gap-2 mt-3 text-xs text-blue-500 animate-fade-in">
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
            AI will analyze your review to ask relevant follow-up questions
          </div>
        )}

        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-400">
            {text.length} characters
          </span>
          <button
            type="submit"
            disabled={loading || text.trim().length < 1}
            className="px-7 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer flex items-center gap-2 shadow-lg shadow-blue-200/50 hover:shadow-blue-300/60"
          >
            {loading ? (
              <>
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                Analyzing...
              </>
            ) : (
              <>
                Submit Review
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
              </>
            )}
          </button>
        </div>
      </form>

      <div className="mt-4 glass-card rounded-xl p-4 border border-blue-200/40">
        <div className="flex items-start gap-2">
          <span className="text-lg">💡</span>
          <p className="text-sm text-blue-700/80">
            After submitting, we may ask 1-2 quick follow-up questions to help future travelers.
            You can always skip them!
          </p>
        </div>
      </div>
    </div>
  )
}
