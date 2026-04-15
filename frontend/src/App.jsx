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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 font-sans">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 shadow-lg">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-inner">
              R
            </div>
            <div>
              <h1 className="text-xl font-bold text-white m-0 tracking-tight">ReviewIQ</h1>
              <p className="text-[11px] text-blue-200 font-medium">Smart Hotel Review Assistant</p>
            </div>
          </div>
          {step !== 'select' && (
            <button
              onClick={handleRestart}
              className="text-sm text-blue-100 hover:text-white font-medium cursor-pointer transition-colors flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              Restart
            </button>
          )}
        </div>
      </header>

      {/* Progress Steps */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 mt-6">
        <div className="flex items-center gap-0 mb-8 bg-white/60 backdrop-blur rounded-2xl p-3 shadow-sm border border-white/80">
          {STEPS.map((s, i) => {
            const isDone = i < currentIdx
            const isActive = i === currentIdx
            const isFuture = i > currentIdx
            return (
              <div key={s.key} className="flex-1 flex items-center">
                <div
                  className={`flex-1 flex flex-col items-center gap-1.5 py-2 rounded-xl transition-all duration-300 ${
                    isActive ? 'bg-blue-50 shadow-sm' : ''
                  } ${isDone ? 'cursor-pointer' : ''}`}
                  onClick={() => {
                    if (i === 0) handleRestart()
                    else if (i === 3 && profile) setStep('dashboard')
                  }}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all duration-300 ${
                    isDone ? 'bg-green-500 text-white shadow-md' :
                    isActive ? 'bg-blue-600 text-white shadow-lg shadow-blue-200' :
                    'bg-gray-200 text-gray-400'
                  }`}>
                    {isDone ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                    ) : (
                      <span>{s.icon}</span>
                    )}
                  </div>
                  <span className={`text-[10px] sm:text-xs font-medium ${
                    isActive ? 'text-blue-700' : isDone ? 'text-green-600' : 'text-gray-400'
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
