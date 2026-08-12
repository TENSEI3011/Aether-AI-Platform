/**
 * Voice API — Transcribe audio and synthesize speech
 */

import axiosClient from './axiosClient'

export async function transcribeAudio(audioBlob, mimeType = 'audio/webm') {
    // Infer file extension from MIME type so the backend picks the right STT path
    const extMap = {
        'audio/webm': 'webm',
        'audio/wav': 'wav',
        'audio/ogg': 'ogg',
        'audio/mp3': 'mp3',
        'audio/mpeg': 'mp3',
    }
    const ext = extMap[mimeType] || 'webm'
    const formData = new FormData()
    formData.append('audio', audioBlob, `recording.${ext}`)
    // Clear the global JSON Content-Type so axios can auto-set multipart/form-data
    const res = await axiosClient.post('/voice/transcribe', formData, {
        headers: { 'Content-Type': undefined },
    })
    return res.data
}

export async function synthesizeSpeech(text) {
    const res = await axiosClient.post('/voice/synthesize', { text })
    return res.data
}
