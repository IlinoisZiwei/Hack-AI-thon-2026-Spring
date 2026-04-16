import { useState } from 'react'
import HotelSelector from './components/HotelSelector'
import UserHotelPicker from './components/UserHotelPicker'
import ReviewForm from './components/ReviewForm'
import FollowUpCard from './components/FollowUpCard'
import HotelDashboard from './components/HotelDashboard'
import { analyzeReview, generateQuestions, submitAnswer, fetchHotelProfile } from './api'

const isAdmin = window.location.pathname.startsWith('/admin')

const ADMIN_STEPS = [
  { key: 'select', label: 'Select Hotel', icon: '🏨' },
  { key: 'review', label: 'Write Review', icon: '✍️' },
  { key: 'followup', label: 'Questions', icon: '💬' },
  { key: 'dashboard', label: 'Results', icon: '📊' },
]

const USER_STEPS = [
  { key: 'pick', label: 'Your Hotel', icon: '📍' },
  { key: 'review', label: 'Your Review', icon: '✍️' },
  { key: 'followup', label: 'Quick Questions', icon: '💬' },
  { key: 'thankyou', label: 'Done', icon: '✅' },
]

export default function App() {
  const STEPS = isAdmin ? ADMIN_STEPS : USER_STEPS

  const [selectedHotel, setSelectedHotel] = useState(null)
  const [step, setStep] = useState(isAdmin ? 'select' : 'pick')
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
      if (result.questions?.length > 0) {
        setStep('followup')
      } else {
        setStep(isAdmin ? 'dashboard' : 'thankyou')
      }
    } catch (err) {
      console.error(err)
      setStep(isAdmin ? 'dashboard' : 'thankyou')
    }
    setLoading(false)
  }

  const handleAnswer = async (question, answer, sentiment) => {
    await submitAnswer(selectedHotel.property_id, question.gap_dimension, answer, sentiment)
  }

  const handleFollowUpDone = async () => {
    if (isAdmin) {
      const p = await fetchHotelProfile(selectedHotel.property_id)
      setProfile(p)
      setStep('dashboard')
    } else {
      setStep('thankyou')
    }
  }

  const handleRestart = () => {
    setStep(isAdmin ? 'select' : 'pick')
    setSelectedHotel(null)
    setReviewText('')
    setQuestions([])
    setProfile(null)
    setPrevCompleteness(null)
  }

  const currentIdx = STEPS.findIndex(s => s.key === step)

  // Admin nav helpers
  const goBack = () => {
    if (!isAdmin) return
    if (currentIdx === 1) handleRestart()
    else if (currentIdx === 2) setStep('review')
    else if (currentIdx === 3) setStep('followup')
  }

  const goForward = () => {
    if (!isAdmin) return
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
              <p className="text-[11px] text-orange-100 font-medium">
                {isAdmin ? 'Admin Dashboard' : 'Smart Hotel Review Assistant'}
              </p>
            </div>
          </div>
          {/* Back / Forward nav — admin only */}
          {isAdmin && step !== 'select' && (
            <div className="flex items-center gap-2">
              <button
                onClick={goBack}
                className="w-9 h-9 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center cursor-pointer transition-colors"
                title="Back"
              >
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              </button>
              {currentIdx < STEPS.length - 1 && (
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
                  }`}
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
          {step === 'select' && isAdmin && <HotelSelector onSelect={handleHotelSelect} />}

          {step === 'pick' && !isAdmin && <UserHotelPicker onSelect={handleHotelSelect} />}

          {step === 'review' && (
            <ReviewForm
              hotel={selectedHotel}
              onSubmit={handleReviewSubmit}
              loading={loading}
              isAdmin={isAdmin}
            />
          )}

          {step === 'followup' && (
            <FollowUpCard
              questions={questions}
              onAnswer={handleAnswer}
              onDone={handleFollowUpDone}
            />
          )}

          {step === 'dashboard' && isAdmin && profile && (
            <HotelDashboard
              profile={profile}
              prevScore={prevCompleteness}
            />
          )}

          {step === 'thankyou' && !isAdmin && (
            <div className="max-w-2xl mx-auto text-center animate-fade-in-up">
              <div className="glass-card rounded-2xl p-10 sm:p-14 shadow-lg border border-white/60">
                <div className="text-6xl mb-6">🎉</div>
                <h2 className="text-3xl font-bold text-gray-900 mb-3 tracking-tight">Thank You!</h2>
                <p className="text-gray-500 text-lg leading-relaxed mb-2">
                  Your feedback means the world to us.
                </p>
                <p className="text-gray-400 text-sm leading-relaxed mb-8">
                  You're helping us improve the experience for future guests
                  {selectedHotel ? <> at <span className="font-semibold text-orange-600">{selectedHotel.name}</span></> : ''}.
                  Every review makes a difference!
                </p>
                <div className="inline-flex items-center gap-2 bg-gradient-to-r from-green-50 to-emerald-50 text-green-700 px-5 py-2.5 rounded-full text-sm font-semibold border border-green-200/60 shadow-sm">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Feedback submitted successfully
                </div>
              </div>
            </div>
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
