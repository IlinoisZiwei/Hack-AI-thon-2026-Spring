import { useState } from 'react'
import VoiceInput from './VoiceInput'

export default function FollowUpCard({ questions, onAnswer, onDone }) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [textInput, setTextInput] = useState('')
  const [answered, setAnswered] = useState([])
  const [mode, setMode] = useState(null) // null | 'text' | 'voice'

  const current = questions[currentIdx]
  if (!current) return null

  const handleQuickAnswer = async (label, sentiment) => {
    await onAnswer(current, label, sentiment)
    advance(label)
  }

  const handleTextSubmit = async () => {
    if (!textInput.trim()) return
    const sentiment = guessSentiment(textInput)
    await onAnswer(current, textInput, sentiment)
    advance(textInput)
  }

  const handleVoiceResult = async (transcript) => {
    const sentiment = guessSentiment(transcript)
    await onAnswer(current, transcript, sentiment)
    advance(transcript)
  }

  const advance = (answerText) => {
    setAnswered(prev => [...prev, { question: current.question, answer: answerText }])
    setTextInput('')
    setMode(null)
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1)
    } else {
      onDone()
    }
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
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 bg-green-50 text-green-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Review submitted successfully!
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-1">One Quick Question</h2>
        <p className="text-gray-500">Help future travelers with just a bit more info</p>
      </div>

      <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200">
        {/* Progress */}
        <div className="flex items-center justify-between mb-6">
          <span className="text-sm text-gray-400">
            Question {currentIdx + 1} of {questions.length}
          </span>
          <span className="text-xs bg-orange-50 text-orange-600 px-3 py-1 rounded-full font-medium">
            {current.gap_reason === 'never_mentioned' ? 'No data yet' : 'Needs update'}
          </span>
        </div>

        {/* Question */}
        <div className="mb-8">
          <p className="text-xl font-medium text-gray-900 leading-relaxed">
            "{current.question}"
          </p>
          <p className="text-sm text-gray-400 mt-2">
            About: {current.gap_label}
          </p>
        </div>

        {/* Quick buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => handleQuickAnswer('Great!', 'positive')}
            className="flex-1 py-3 rounded-xl border-2 border-green-200 bg-green-50 text-green-700 font-medium hover:bg-green-100 transition-colors cursor-pointer"
          >
            Great
          </button>
          <button
            onClick={() => handleQuickAnswer('It was okay', 'neutral')}
            className="flex-1 py-3 rounded-xl border-2 border-yellow-200 bg-yellow-50 text-yellow-700 font-medium hover:bg-yellow-100 transition-colors cursor-pointer"
          >
            Okay
          </button>
          <button
            onClick={() => handleQuickAnswer('Not great', 'negative')}
            className="flex-1 py-3 rounded-xl border-2 border-red-200 bg-red-50 text-red-700 font-medium hover:bg-red-100 transition-colors cursor-pointer"
          >
            Not Great
          </button>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400">or share more details</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* Text / Voice input toggle */}
        <div className="flex gap-3 mb-4">
          <button
            onClick={() => setMode('text')}
            className={`flex-1 py-3 rounded-xl border-2 font-medium transition-colors cursor-pointer flex items-center justify-center gap-2 ${
              mode === 'text' ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Type Answer
          </button>
          <button
            onClick={() => setMode('voice')}
            className={`flex-1 py-3 rounded-xl border-2 font-medium transition-colors cursor-pointer flex items-center justify-center gap-2 ${
              mode === 'voice' ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-14 0m14 0a7 7 0 00-14 0m14 0v1a7 7 0 01-14 0v-1m7 8v4m-4 0h8" />
            </svg>
            Voice Answer
          </button>
        </div>

        {/* Text input */}
        {mode === 'text' && (
          <div className="flex gap-2">
            <input
              type="text"
              value={textInput}
              onChange={e => setTextInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleTextSubmit()}
              placeholder="Type your answer..."
              className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={handleTextSubmit}
              disabled={!textInput.trim()}
              className="px-5 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
            >
              Send
            </button>
          </div>
        )}

        {/* Voice input */}
        {mode === 'voice' && (
          <VoiceInput onResult={handleVoiceResult} />
        )}

        {/* Skip */}
        <div className="text-center mt-6">
          <button
            onClick={handleSkip}
            className="text-sm text-gray-400 hover:text-gray-600 cursor-pointer"
          >
            Skip this question
          </button>
        </div>
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
