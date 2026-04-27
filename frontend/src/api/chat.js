/**
 * Chat API — AI assistant conversational messaging
 */

import axiosClient from './axiosClient'

export async function sendChatMessage(message, sessionId, datasetId = null) {
    const res = await axiosClient.post('/chat', {
        message,
        session_id: sessionId,
        dataset_id: datasetId,
    })
    return res.data
}

export async function getChatHistory(sessionId) {
    const res = await axiosClient.get(`/chat/history/${sessionId}`)
    return res.data
}
