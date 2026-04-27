/**
 * ============================================================
 * VoiceRecorder — Microphone recording + browser transcription
 * ============================================================
 * Two-layer approach:
 *   1. PRIMARY: Browser's Web Speech API (instant, no server needed)
 *   2. FALLBACK: Records audio → sends to backend STT endpoint
 *
 * Features:
 *   - Live recording indicator with pulsing animation
 *   - Real-time transcript preview
 *   - Error display
 *   - Auto-stop after silence
 * ============================================================
 */

import React, { useState, useRef, useCallback, useEffect } from 'react'
import { transcribeAudio } from '../api/voice'

// Check if browser supports Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

function VoiceRecorder({ onTranscript }) {
    const [recording, setRecording] = useState(false)
    const [processing, setProcessing] = useState(false)
    const [error, setError] = useState('')
    const [liveTranscript, setLiveTranscript] = useState('')

    // Refs for Web Speech API
    const recognitionRef = useRef(null)

    // Refs for fallback (MediaRecorder)
    const mediaRecorderRef = useRef(null)
    const audioChunksRef = useRef([])
    const streamRef = useRef(null)

    // ── Cleanup on unmount ───────────────────────────────
    useEffect(() => {
        return () => {
            if (recognitionRef.current) {
                try { recognitionRef.current.abort() } catch { }
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((t) => t.stop())
            }
        }
    }, [])

    // ── PRIMARY: Web Speech API ──────────────────────────
    const startWebSpeech = useCallback(() => {
        if (!SpeechRecognition) {
            return false // Not supported, use fallback
        }

        setError('')
        setLiveTranscript('')

        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.interimResults = true
        recognition.lang = 'en-US'

        recognition.onresult = (event) => {
            let final = ''
            let interim = ''
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript
                if (event.results[i].isFinal) {
                    final += transcript
                } else {
                    interim += transcript
                }
            }
            setLiveTranscript(final || interim)
            if (final && onTranscript) {
                onTranscript(final)
            }
        }

        recognition.onerror = (event) => {
            console.error('SpeechRecognition error:', event.error)
            if (event.error === 'no-speech') {
                setError('No speech detected. Try again.')
            } else if (event.error === 'not-allowed') {
                setError('Microphone access denied.')
            } else {
                setError(`Speech error: ${event.error}`)
            }
            setRecording(false)
        }

        recognition.onend = () => {
            setRecording(false)
        }

        recognitionRef.current = recognition
        recognition.start()
        setRecording(true)
        return true
    }, [onTranscript])

    // ── FALLBACK: MediaRecorder + Backend STT ────────────
    const startMediaRecorder = useCallback(async () => {
        setError('')
        setLiveTranscript('')
        audioChunksRef.current = []

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            streamRef.current = stream

            const recorder = new MediaRecorder(stream)
            mediaRecorderRef.current = recorder

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) audioChunksRef.current.push(e.data)
            }

            recorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach((t) => t.stop())
                    streamRef.current = null
                }
                audioChunksRef.current = []

                setProcessing(true)
                try {
                    const result = await transcribeAudio(audioBlob)
                    if (result.error) {
                        setError(result.error)
                    } else if (result.transcript && onTranscript) {
                        setLiveTranscript(result.transcript)
                        onTranscript(result.transcript)
                    } else {
                        setError('No speech detected')
                    }
                } catch (err) {
                    console.error('Transcription failed:', err)
                    setError('Transcription failed. Try again.')
                } finally {
                    setProcessing(false)
                }
            }

            recorder.start()
            setRecording(true)
        } catch (err) {
            console.error('Microphone access denied:', err)
            setError('Microphone access denied')
        }
    }, [onTranscript])

    // ── Start Recording ──────────────────────────────────
    const startRecording = useCallback(() => {
        // Try Web Speech API first
        const webSpeechStarted = startWebSpeech()
        if (!webSpeechStarted) {
            // Fallback to MediaRecorder + backend
            startMediaRecorder()
        }
    }, [startWebSpeech, startMediaRecorder])

    // ── Stop Recording ───────────────────────────────────
    const stopRecording = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop()
            recognitionRef.current = null
        }
        if (mediaRecorderRef.current && recording) {
            mediaRecorderRef.current.stop()
        }
        setRecording(false)
    }, [recording])

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
                className={`voice-btn ${recording ? 'recording' : ''}`}
                onClick={recording ? stopRecording : startRecording}
                disabled={processing}
                title={recording ? 'Stop recording' : 'Start voice input'}
            >
                {processing ? '⏳' : recording ? '⏹' : '🎤'}
            </button>
            {/* Live recording indicator */}
            {recording && (
                <span className="recording-indicator">
                    🔴 Listening...
                </span>
            )}
            {/* Live transcript preview */}
            {liveTranscript && !recording && (
                <span style={{ fontSize: '0.75rem', color: 'var(--color-success)', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    ✓ "{liveTranscript}"
                </span>
            )}
            {/* Error display */}
            {error && (
                <span style={{ color: 'var(--color-error)', fontSize: '0.75rem' }}>
                    {error}
                </span>
            )}
        </div>
    )
}

export default VoiceRecorder
