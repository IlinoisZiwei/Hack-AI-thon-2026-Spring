import { useState, useEffect, useRef, useCallback } from 'react'

const QUICK_OPTIONS = [
  { label: 'Great!', emoji: '👍', sentiment: 'positive', colors: 'border-green-200 bg-green-50 text-green-700 hover:bg-green-100 hover:border-green-300', selectedBg: 'border-green-400 bg-green-100 text-green-800 ring-2 ring-green-300' },
  { label: 'Okay', emoji: '👌', sentiment: 'neutral', colors: 'border-yellow-200 bg-yellow-50 text-yellow-700 hover:bg-yellow-100 hover:border-yellow-300', selectedBg: 'border-yellow-400 bg-yellow-100 text-yellow-800 ring-2 ring-yellow-300' },
  { label: 'Not great', emoji: '👎', sentiment: 'negative', colors: 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100 hover:border-red-300', selectedBg: 'border-red-400 bg-red-100 text-red-800 ring-2 ring-red-300' },
]

export default function FollowUpCard({ questions, onAnswer, onDone }) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [textInput, setTextInput] = useState('')
  const [selectedQuick, setSelectedQuick] = useState(null) // {label, sentiment}
  const [listening, setListening] = useState(false)
  const [showThankYou, setShowThankYou] = useState(false)
  const [displayedText, setDisplayedText] = useState('')
  const recognitionRef = useRef(null)
  const finalTranscriptRef = useRef('')

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

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    setListening(false)
  }, [])

  const startListening = useCallback(async () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(t => t.stop())
    } catch {
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event) => {
      let text = ''
      for (let i = 0; i < event.results.length; i++) {
        text += event.results[i][0].transcript
      }
      finalTranscriptRef.current = text
      setTextInput(prev => {
        // Replace with latest voice transcript
        return text
      })
    }

    recognition.onerror = () => setListening(false)
    recognition.onend = () => setListening(false)

    recognitionRef.current = recognition
    finalTranscriptRef.current = ''
    recognition.start()
    setListening(true)
  }, [])

  const toggleVoice = useCallback(() => {
    if (listening) {
      stopListening()
    } else {
      startListening()
    }
  }, [listening, startListening, stopListening])

  const showThankAndAdvance = (answerText) => {
    setShowThankYou(true)
    setTimeout(() => {
      setShowThankYou(false)
      setTextInput('')
      setSelectedQuick(null)
      stopListening()
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
      stopListening()
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
                      i < currentIdx ? 'bg-green-400' : i === currentIdx ? 'bg-orange-500' : 'bg-gray-200'
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
                <span className="inline-block w-0.5 h-6 bg-orange-500 ml-0.5 animate-pulse" />
              </p>
              <p className="text-sm text-gray-400 mt-2 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-orange-400 inline-block" />
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

            {/* Text input with inline voice button */}
            <div className="relative mb-3">
              <input
                type="text"
                value={textInput}
                onChange={e => setTextInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && hasAnswer && handleSubmit()}
                placeholder={listening ? 'Listening... tap mic to stop' : 'Type or tap mic to speak (optional)'}
                className={`w-full pl-4 pr-12 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white/80 text-sm transition-colors ${
                  listening ? 'border-red-300 bg-red-50/40' : 'border-gray-200'
                }`}
                readOnly={listening}
              />
              <button
                onClick={toggleVoice}
                className={`absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer ${
                  listening
                    ? 'bg-red-500 text-white shadow-md shadow-red-200/50 animate-pulse'
                    : 'bg-gray-100 text-gray-500 hover:bg-orange-100 hover:text-orange-600'
                }`}
                title={listening ? 'Stop listening' : 'Voice input'}
              >
                {listening ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-14 0m14 0a7 7 0 00-14 0m14 0v1a7 7 0 01-14 0v-1m7 8v4m-4 0h8" /></svg>
                )}
              </button>
            </div>

            {/* Submit button */}
            <button
              onClick={handleSubmit}
              disabled={!hasAnswer}
              className="w-full py-3 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-xl font-semibold hover:from-orange-600 hover:to-amber-600 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer shadow-lg shadow-orange-200/50 transition-all flex items-center justify-center gap-2 mt-2"
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
