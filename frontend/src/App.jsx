import { useState } from 'react'
import HotelSelector from './components/HotelSelector'
import ReviewForm from './components/ReviewForm'
import FollowUpCard from './components/FollowUpCard'
import HotelDashboard from './components/HotelDashboard'
import { analyzeReview, generateQuestions, submitAnswer, fetchHotelProfile } from './api'

const STEPS = [
  { key: 'select', label: 'Select Hotel', icon: '🏨' },
  { key: 'review', label: 'Write Review', icon: '✍️' },
  { key: 'followup', label: 'Questions', icon: '💬' },
  { key: 'dashboard', label: 'Results', icon: '📊' },
]

export default function App() {
  const [selectedHotel, setSelectedHotel] = useState(null)
  const [step, setStep] = useState('select')
  const [reviewText, setReviewText] = useState('')
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [profile, setProfile] = useState(null)
  const [prevCompleteness, setPrevCompleteness] = useState(null)

  const handleHotelSelect = async (hotel) => {
    setSelectedHotel(hotel)
    setStep('review')
    const p = await fetchHotelProfile(hotel.property_id)
    setProfile(p)
    setPrevCompleteness(p.completeness.score)
  }

  const handleReviewSubmit = async (text) => {
    setReviewText(text)
    setLoading(true)
    try {
      const analysis = await analyzeReview(selectedHotel.property_id, text)
      const result = await generateQuestions(
        selectedHotel.property_id,
        text,
        analysis.covered_dimensions
      )
      setQuestions(result.questions || [])
      setStep(result.questions?.length > 0 ? 'followup' : 'dashboard')
    } catch (err) {
      console.error(err)
      setStep('dashboard')
    }
    setLoading(false)
  }

  const handleAnswer = async (question, answer, sentiment) => {
    await submitAnswer(selectedHotel.property_id, question.gap_dimension, answer, sentiment)
  }

  const handleFollowUpDone = async () => {
    const p = await fetchHotelProfile(selectedHotel.property_id)
    setProfile(p)
    setStep('dashboard')
  }

  const handleRestart = () => {
    setStep('select')
    setSelectedHotel(null)
    setReviewText('')
    setQuestions([])
    setProfile(null)
    setPrevCompleteness(null)
  }

  const currentIdx = STEPS.findIndex(s => s.key === step)

  const goBack = () => {
    if (currentIdx === 1) handleRestart()
    else if (currentIdx === 2) setStep('review')
    else if (currentIdx === 3) setStep('followup')
  }

  const goForward = () => {
    if (currentIdx === 2 && profile) setStep('dashboard')
    if (currentIdx === 3) handleRestart()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 font-sans">
      {/* Header */}
      <header className="bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 shadow-lg">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/25 backdrop-blur rounded-xl flex items-center justify-center text-2xl shadow-inner">
              🎙️
            </div>
            <div>
              <h1 className="text-xl font-bold text-white m-0 tracking-tight">GuestVoice</h1>
              <p className="text-[11px] text-orange-100 font-medium">Smart Hotel Review Assistant</p>
            </div>
          </div>
          {/* Back / Forward nav */}
          {step !== 'select' && (
            <div className="flex items-center gap-2">
              <button
                onClick={goBack}
                className="w-9 h-9 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center cursor-pointer transition-colors"
                title="Back"
              >
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              </button>
              {currentIdx < 3 && (
                <button
                  onClick={goForward}
                  disabled={currentIdx === 1}
                  className="w-9 h-9 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center cursor-pointer transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Forward"
                >
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                </button>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Progress Steps */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 mt-6">
        <div className="flex items-center gap-0 mb-8 bg-white/60 backdrop-blur rounded-2xl p-3 shadow-sm border border-white/80">
          {STEPS.map((s, i) => {
            const isDone = i < currentIdx
            const isActive = i === currentIdx
            return (
              <div key={s.key} className="flex-1 flex items-center">
                <div
                  className={`flex-1 flex flex-col items-center gap-1.5 py-2 rounded-xl transition-all duration-300 ${
                    isActive ? 'bg-orange-50 shadow-sm' : ''
                  } ${isDone ? 'cursor-pointer' : ''}`}
                  onClick={() => {
                    if (isDone && i === 0) handleRestart()
                    else if (isDone && i === 1) setStep('review')
                    else if (isDone && i === 2) setStep('followup')
                    else if (i === 3 && profile && currentIdx >= 3) setStep('dashboard')
                  }}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all duration-300 ${
                    isDone ? 'bg-green-500 text-white shadow-md' :
                    isActive ? 'bg-orange-500 text-white shadow-lg shadow-orange-200' :
                    'bg-gray-200 text-gray-400'
                  }`}>
                    {isDone ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                    ) : (
                      <span>{s.icon}</span>
                    )}
                  </div>
                  <span className={`text-[10px] sm:text-xs font-medium ${
                    isActive ? 'text-orange-700' : isDone ? 'text-green-600' : 'text-gray-400'
                  }`}>
                    {s.label}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`w-6 sm:w-10 h-0.5 rounded-full mx-1 transition-colors duration-500 ${
                    isDone ? 'bg-green-400' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 pb-16">
        <div className="animate-fade-in-up" key={step}>
          {step === 'select' && <HotelSelector onSelect={handleHotelSelect} />}

          {step === 'review' && (
            <ReviewForm
              hotel={selectedHotel}
              onSubmit={handleReviewSubmit}
              loading={loading}
            />
          )}

          {step === 'followup' && (
            <FollowUpCard
              questions={questions}
              onAnswer={handleAnswer}
              onDone={handleFollowUpDone}
            />
          )}

          {step === 'dashboard' && profile && (
            <HotelDashboard
              profile={profile}
              prevScore={prevCompleteness}
            />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-xs text-gray-400">
        Built for Wharton AI Hack-AI-thon 2026
      </footer>
    </div>
  )
}
