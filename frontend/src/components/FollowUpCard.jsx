import { useState, useEffect } from 'react'
import VoiceInput from './VoiceInput'

const QUICK_OPTIONS = [
  { label: 'Great!', emoji: '👍', sentiment: 'positive', colors: 'border-green-200 bg-green-50 text-green-700 hover:bg-green-100 hover:border-green-300', selectedBg: 'border-green-400 bg-green-100 text-green-800 ring-2 ring-green-300' },
  { label: 'Okay', emoji: '👌', sentiment: 'neutral', colors: 'border-yellow-200 bg-yellow-50 text-yellow-700 hover:bg-yellow-100 hover:border-yellow-300', selectedBg: 'border-yellow-400 bg-yellow-100 text-yellow-800 ring-2 ring-yellow-300' },
  { label: 'Not great', emoji: '👎', sentiment: 'negative', colors: 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100 hover:border-red-300', selectedBg: 'border-red-400 bg-red-100 text-red-800 ring-2 ring-red-300' },
]

export default function FollowUpCard({ questions, onAnswer, onDone }) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [textInput, setTextInput] = useState('')
  const [selectedQuick, setSelectedQuick] = useState(null) // {label, sentiment}
  const [mode, setMode] = useState(null)
  const [showThankYou, setShowThankYou] = useState(false)
  const [displayedText, setDisplayedText] = useState('')

  const current = questions[currentIdx]

  // Typewriter effect
  useEffect(() => {
    if (!current) return
    setDisplayedText('')
    let i = 0
    const text = current.question
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayedText(text.slice(0, i + 1))
        i++
      } else {
        clearInterval(timer)
      }
    }, 25)
    return () => clearInterval(timer)
  }, [currentIdx, current?.question])

  if (!current) return null

  const handleQuickSelect = (label, sentiment) => {
    // Toggle selection — clicking again deselects
    if (selectedQuick?.label === label) {
      setSelectedQuick(null)
    } else {
      setSelectedQuick({ label, sentiment })
    }
  }

  const handleSubmit = async () => {
    // Combine quick selection + detail text
    const parts = []
    let sentiment = 'neutral'

    if (selectedQuick) {
      parts.push(selectedQuick.label)
      sentiment = selectedQuick.sentiment
    }
    if (textInput.trim()) {
      parts.push(textInput.trim())
      // If there's text, let text sentiment override if no quick selected
      if (!selectedQuick) {
        sentiment = guessSentiment(textInput)
      }
    }

    if (parts.length === 0) return

    const fullAnswer = parts.join(' — ')
    await onAnswer(current, fullAnswer, sentiment)
    showThankAndAdvance(fullAnswer)
  }

  const handleVoiceResult = (transcript) => {
    // Append voice result to text input instead of submitting immediately
    setTextInput(prev => prev ? `${prev} ${transcript}` : transcript)
    setMode(null) // Close voice mode, show the text
  }

  const showThankAndAdvance = (answerText) => {
    setShowThankYou(true)
    setTimeout(() => {
      setShowThankYou(false)
      setTextInput('')
      setSelectedQuick(null)
      setMode(null)
      if (currentIdx < questions.length - 1) {
        setCurrentIdx(currentIdx + 1)
      } else {
        onDone()
      }
    }, 800)
  }

  const handleSkip = () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1)
      setTextInput('')
      setSelectedQuick(null)
      setMode(null)
    } else {
      onDone()
    }
  }

  const hasAnswer = selectedQuick || textInput.trim()

  return (
    <div className="max-w-2xl mx-auto">
      {/* Success badge */}
      <div className="text-center mb-6 animate-bounce-in">
        <div className="inline-flex items-center gap-2 bg-gradient-to-r from-green-50 to-emerald-50 text-green-700 px-5 py-2.5 rounded-full text-sm font-semibold border border-green-200/60 shadow-sm">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Review submitted successfully!
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mt-4 mb-1 tracking-tight">One Quick Question</h2>
        <p className="text-gray-500">Help future travelers with just a bit more info</p>
      </div>

      <div className={`glass-card rounded-2xl p-6 sm:p-8 shadow-lg border border-white/60 ${showThankYou ? '' : 'animate-pulse-glow'}`}>
        {showThankYou ? (
          <div className="flex flex-col items-center justify-center py-10 animate-bounce-in">
            <div className="text-5xl mb-3">🎉</div>
            <p className="text-lg font-semibold text-gray-900">Thank you!</p>
            <p className="text-sm text-gray-500">Your answer helps future travelers</p>
          </div>
        ) : (
          <>
            {/* Progress */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">
                  Question {currentIdx + 1} of {questions.length}
                </span>
                <div className="flex gap-1">
                  {questions.map((_, i) => (
                    <div key={i} className={`w-2 h-2 rounded-full transition-colors ${
                      i < currentIdx ? 'bg-green-400' : i === currentIdx ? 'bg-blue-500' : 'bg-gray-200'
                    }`} />
                  ))}
                </div>
              </div>
              <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                current.gap_reason === 'never_mentioned'
                  ? 'bg-red-50 text-red-600 border border-red-100'
                  : 'bg-amber-50 text-amber-600 border border-amber-100'
              }`}>
                {current.gap_reason === 'never_mentioned' ? '📭 No data yet' : '🔄 Needs update'}
              </span>
            </div>

            {/* Question with typewriter */}
            <div className="mb-8">
              <p className="text-xl sm:text-2xl font-semibold text-gray-900 leading-relaxed">
                "{displayedText}"
                <span className="inline-block w-0.5 h-6 bg-blue-500 ml-0.5 animate-pulse" />
              </p>
              <p className="text-sm text-gray-400 mt-2 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
                About: {current.gap_label}
              </p>
            </div>

            {/* Step 1: Quick rating (select, don't submit) */}
            <p className="text-xs text-gray-400 font-medium mb-2 uppercase tracking-wide">Step 1: Quick rating</p>
            <div className="flex gap-3 mb-5">
              {QUICK_OPTIONS.map(opt => {
                const isSelected = selectedQuick?.label === opt.label
                return (
                  <button
                    key={opt.label}
                    onClick={() => handleQuickSelect(opt.label, opt.sentiment)}
                    className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all cursor-pointer hover:-translate-y-0.5 hover:shadow-md ${
                      isSelected ? opt.selectedBg : opt.colors
                    }`}
                  >
                    <span className="text-lg block">{opt.emoji}</span>
                    <span className="text-sm">{opt.label}</span>
                    {isSelected && <span className="block text-[10px] mt-0.5">✓ selected</span>}
                  </button>
                )
              })}
            </div>

            {/* Step 2: Optional details */}
            <p className="text-xs text-gray-400 font-medium mb-2 uppercase tracking-wide">Step 2: Add details (optional)</p>

            {/* Text input always visible */}
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={textInput}
                onChange={e => setTextInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && hasAnswer && handleSubmit()}
                placeholder="Add more details... (optional)"
                className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white/80 text-sm"
              />
              <button
                onClick={() => setMode(mode === 'voice' ? null : 'voice')}
                className={`px-4 py-3 rounded-xl border-2 transition-all cursor-pointer ${
                  mode === 'voice' ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-400 hover:border-gray-300'
                }`}
                title="Voice input"
              >
                🎤
              </button>
            </div>

            {/* Voice input */}
            {mode === 'voice' && (
              <div className="animate-fade-in mb-4">
                <VoiceInput onResult={handleVoiceResult} />
              </div>
            )}

            {/* Submit button */}
            <button
              onClick={handleSubmit}
              disabled={!hasAnswer}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer shadow-lg shadow-blue-200/50 transition-all flex items-center justify-center gap-2 mt-2"
            >
              {hasAnswer ? (
                <>
                  Submit Answer
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
                </>
              ) : (
                'Select a rating or type your answer'
              )}
            </button>

            {/* What you're submitting */}
            {hasAnswer && (
              <div className="mt-3 bg-gray-50 rounded-xl p-3 text-xs text-gray-500 animate-fade-in">
                <span className="font-medium">Your answer: </span>
                {selectedQuick && <span className="text-gray-700">{selectedQuick.emoji} {selectedQuick.label}</span>}
                {selectedQuick && textInput.trim() && <span> — </span>}
                {textInput.trim() && <span className="text-gray-700">"{textInput.trim()}"</span>}
              </div>
            )}

            {/* Skip */}
            <div className="text-center mt-4">
              <button
                onClick={handleSkip}
                className="text-sm text-gray-400 hover:text-gray-600 cursor-pointer transition-colors"
              >
                Skip this question →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function guessSentiment(text) {
  const lower = text.toLowerCase()
  const positive = ['great', 'good', 'excellent', 'amazing', 'love', 'perfect', 'nice', 'clean', 'fast', 'quiet', 'comfortable', 'friendly']
  const negative = ['bad', 'poor', 'terrible', 'awful', 'slow', 'dirty', 'noisy', 'loud', 'broken', 'worst', 'horrible', 'not great']
  const posCount = positive.filter(w => lower.includes(w)).length
  const negCount = negative.filter(w => lower.includes(w)).length
  if (posCount > negCount) return 'positive'
  if (negCount > posCount) return 'negative'
  return 'neutral'
}
