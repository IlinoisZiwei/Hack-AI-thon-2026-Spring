import { useState, useRef, useCallback } from 'react'

export default function VoiceInput({ onResult }) {
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState('')
  const [permissionState, setPermissionState] = useState(null) // null | 'requesting' | 'granted' | 'denied'
  const recognitionRef = useRef(null)
  const finalTranscriptRef = useRef('')
  const hasResultRef = useRef(false)

  const startListening = useCallback(async () => {
    setError('')
    setTranscript('')
    finalTranscriptRef.current = ''
    hasResultRef.current = false

    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Speech recognition is not supported. Please use Chrome or Edge.')
      return
    }

    // Request microphone permission first
    try {
      setPermissionState('requesting')
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      // Stop the stream immediately — we just needed permission
      stream.getTracks().forEach(t => t.stop())
      setPermissionState('granted')
    } catch (err) {
      setPermissionState('denied')
      setError('Microphone access denied. Please allow microphone in your browser settings.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      let interim = ''
      let final = ''
      for (let i = 0; i < event.results.length; i++) {
        const t = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          final += t
        } else {
          interim += t
        }
      }
      const combined = final || interim
      setTranscript(combined)
      finalTranscriptRef.current = combined
      hasResultRef.current = true
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      if (event.error === 'not-allowed') {
        setError('Microphone access denied.')
        setPermissionState('denied')
      } else if (event.error === 'no-speech') {
        setError('No speech detected. Please try again.')
      } else if (event.error !== 'aborted') {
        setError(`Error: ${event.error}. Please try again.`)
      }
      setListening(false)
    }

    recognition.onend = () => {
      setListening(false)
      // If we got a result, submit it
      if (hasResultRef.current && finalTranscriptRef.current.trim()) {
        onResult(finalTranscriptRef.current.trim())
      }
    }

    recognitionRef.current = recognition
    try {
      recognition.start()
      setListening(true)
    } catch (err) {
      setError('Failed to start speech recognition. Please try again.')
    }
  }, [onResult])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
  }, [])

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
          <div className="flex gap-1 items-end">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="w-1 bg-white rounded-full"
                style={{
                  height: `${10 + Math.random() * 14}px`,
                  animation: `pulse 0.${4 + i}s ease-in-out infinite alternate`,
                }}
              />
            ))}
          </div>
        ) : (
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-14 0m14 0a7 7 0 00-14 0m14 0v1a7 7 0 01-14 0v-1m7 8v4m-4 0h8" />
          </svg>
        )}
      </button>

      <p className="mt-3 text-sm text-gray-500 font-medium">
        {listening
          ? '🔴 Listening... tap to finish'
          : permissionState === 'requesting'
          ? '🔐 Requesting microphone access...'
          : '🎤 Tap to speak'}
      </p>

      {/* Live transcript */}
      {transcript && (
        <div className="mt-3 glass-card rounded-xl p-3 text-sm text-gray-700 max-w-xs mx-auto animate-fade-in border border-blue-100">
          <span className="text-gray-400 text-xs block mb-1">You said:</span>
          "{transcript}"
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mt-3 bg-red-50 rounded-xl p-3 text-sm text-red-600 max-w-xs mx-auto animate-fade-in border border-red-100">
          {error}
        </div>
      )}

      {/* Hint */}
      {!listening && !error && !transcript && (
        <p className="mt-2 text-xs text-gray-400">
          Works best in Chrome. Make sure your microphone is enabled.
        </p>
      )}
    </div>
  )
}
