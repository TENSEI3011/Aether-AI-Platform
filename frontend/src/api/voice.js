/**
 * Voice API — Transcribe audio and synthesize speech
 */

import axiosClient from './axiosClient'

export async function transcribeAudio(audioBlob) {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')
    const res = await axiosClient.post('/voice/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
}

export async function synthesizeSpeech(text) {
    const res = await axiosClient.post('/voice/synthesize', { text })
    return res.data
}
