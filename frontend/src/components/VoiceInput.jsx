import { useState, useRef } from 'react'

export default function VoiceInput({ onResult }) {
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const recognitionRef = useRef(null)

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event) => {
      const result = Array.from(event.results)
        .map(r => r[0].transcript)
        .join('')
      setTranscript(result)
      if (event.results[0].isFinal) {
        setListening(false)
        onResult(result)
      }
    }

    recognition.onerror = () => setListening(false)
    recognition.onend = () => setListening(false)

    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
    setTranscript('')
  }

  const stopListening = () => {
    if (recognitionRef.current) recognitionRef.current.stop()
    setListening(false)
  }

  return (
    <div className="text-center py-4">
      <button
        onClick={listening ? stopListening : startListening}
        className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto transition-all cursor-pointer ${
          listening
            ? 'bg-gradient-to-br from-red-500 to-pink-500 animate-pulse shadow-xl shadow-red-200/50'
            : 'bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 shadow-xl shadow-blue-200/50'
        }`}
      >
        {listening ? (
          <div className="flex gap-1">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="w-1 bg-white rounded-full animate-pulse" style={{ height: `${12 + i * 6}px`, animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
        ) : (
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-14 0m14 0a7 7 0 00-14 0m14 0v1a7 7 0 01-14 0v-1m7 8v4m-4 0h8" />
          </svg>
        )}
      </button>
      <p className="mt-3 text-sm text-gray-500 font-medium">
        {listening ? '🔴 Listening... tap to stop' : '🎤 Tap to speak'}
      </p>
      {transcript && (
        <div className="mt-3 glass-card rounded-xl p-3 text-sm text-gray-700 max-w-xs mx-auto animate-fade-in">
          "{transcript}"
        </div>
      )}
    </div>
  )
}
