import { useState, useEffect } from 'react'
import VoiceInput from './VoiceInput'

export default function FollowUpCard({ questions, onAnswer, onDone }) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [textInput, setTextInput] = useState('')
  const [answered, setAnswered] = useState([])
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

  const handleQuickAnswer = async (label, sentiment) => {
    await onAnswer(current, label, sentiment)
    showThankAndAdvance(label)
  }

  const handleTextSubmit = async () => {
    if (!textInput.trim()) return
    const sentiment = guessSentiment(textInput)
    await onAnswer(current, textInput, sentiment)
    showThankAndAdvance(textInput)
  }

  const handleVoiceResult = async (transcript) => {
    const sentiment = guessSentiment(transcript)
    await onAnswer(current, transcript, sentiment)
    showThankAndAdvance(transcript)
  }

  const showThankAndAdvance = (answerText) => {
    setAnswered(prev => [...prev, { question: current.question, answer: answerText }])
    setShowThankYou(true)
    setTimeout(() => {
      setShowThankYou(false)
      setTextInput('')
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
      setMode(null)
    } else {
      onDone()
    }
  }

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

            {/* Quick buttons */}
            <div className="flex gap-3 mb-6">
              {[
                { label: 'Great!', emoji: '👍', sentiment: 'positive', colors: 'border-green-200 bg-green-50 text-green-700 hover:bg-green-100 hover:border-green-300' },
                { label: 'Okay', emoji: '👌', sentiment: 'neutral', colors: 'border-yellow-200 bg-yellow-50 text-yellow-700 hover:bg-yellow-100 hover:border-yellow-300' },
                { label: 'Not great', emoji: '👎', sentiment: 'negative', colors: 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100 hover:border-red-300' },
              ].map(opt => (
                <button
                  key={opt.label}
                  onClick={() => handleQuickAnswer(opt.label, opt.sentiment)}
                  className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all cursor-pointer hover:-translate-y-0.5 hover:shadow-md ${opt.colors}`}
                >
                  <span className="text-lg block">{opt.emoji}</span>
                  <span className="text-sm">{opt.label}</span>
                </button>
              ))}
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3 mb-5">
              <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent" />
              <span className="text-xs text-gray-400">or share more details</span>
              <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent" />
            </div>

            {/* Input toggle */}
            <div className="flex gap-3 mb-4">
              <button
                onClick={() => setMode('text')}
                className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all cursor-pointer flex items-center justify-center gap-2 ${
                  mode === 'text' ? 'border-blue-400 bg-blue-50 text-blue-700 shadow-sm' : 'border-gray-200 text-gray-500 hover:border-gray-300'
                }`}
              >
                ✏️ Type Answer
              </button>
              <button
                onClick={() => setMode('voice')}
                className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all cursor-pointer flex items-center justify-center gap-2 ${
                  mode === 'voice' ? 'border-blue-400 bg-blue-50 text-blue-700 shadow-sm' : 'border-gray-200 text-gray-500 hover:border-gray-300'
                }`}
              >
                🎤 Voice Answer
              </button>
            </div>

            {/* Text input */}
            {mode === 'text' && (
              <div className="flex gap-2 animate-fade-in">
                <input
                  type="text"
                  value={textInput}
                  onChange={e => setTextInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleTextSubmit()}
                  placeholder="Type your answer..."
                  className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white/80"
                  autoFocus
                />
                <button
                  onClick={handleTextSubmit}
                  disabled={!textInput.trim()}
                  className="px-5 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 disabled:opacity-40 cursor-pointer shadow-md"
                >
                  Send
                </button>
              </div>
            )}

            {mode === 'voice' && (
              <div className="animate-fade-in">
                <VoiceInput onResult={handleVoiceResult} />
              </div>
            )}

            {/* Skip */}
            <div className="text-center mt-6">
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
