import { useState } from 'react'
import HotelSelector from './components/HotelSelector'
import ReviewForm from './components/ReviewForm'
import FollowUpCard from './components/FollowUpCard'
import HotelDashboard from './components/HotelDashboard'
import { analyzeReview, generateQuestions, submitAnswer, fetchHotelProfile } from './api'

export default function App() {
  const [selectedHotel, setSelectedHotel] = useState(null)
  const [step, setStep] = useState('select') // select | review | followup | dashboard
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-blue-100">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
              R
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 m-0">ReviewIQ</h1>
              <p className="text-xs text-gray-500">Smart Hotel Review Assistant</p>
            </div>
          </div>
          {step !== 'select' && (
            <button
              onClick={handleRestart}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium cursor-pointer"
            >
              Start Over
            </button>
          )}
        </div>
      </header>

      {/* Progress bar */}
      <div className="max-w-4xl mx-auto px-6 mt-6">
        <div className="flex items-center gap-1 sm:gap-2 mb-8">
          {['Select Hotel', 'Write Review', 'Questions', 'Dashboard'].map((label, i) => {
            const steps = ['select', 'review', 'followup', 'dashboard']
            const currentIdx = steps.indexOf(step)
            const isActive = i <= currentIdx
            const canGoTo = i <= currentIdx && profile
            return (
              <div
                key={label}
                className={`flex-1 flex flex-col items-center gap-1 ${canGoTo ? 'cursor-pointer' : ''}`}
                onClick={() => {
                  if (i === 0) handleRestart()
                  else if (i === 3 && profile) setStep('dashboard')
                }}
              >
                <div className={`w-full h-2 rounded-full transition-colors duration-500 ${isActive ? 'bg-blue-600' : 'bg-gray-200'}`} />
                <span className={`text-[10px] sm:text-xs ${isActive ? 'text-blue-600 font-medium' : 'text-gray-400'}`}>
                  {label}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-6 pb-12">
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
      </main>
    </div>
  )
}
