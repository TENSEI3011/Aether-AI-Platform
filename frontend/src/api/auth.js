/**
 * Auth API — Login, Register, Refresh, and profile endpoints
 */

import axiosClient from './axiosClient'

export async function loginUser(username, password) {
    const res = await axiosClient.post('/auth/login', { username, password })
    return res.data
}

export async function registerUser(username, email, password) {
    const res = await axiosClient.post('/auth/register', { username, email, password })
    return res.data
}

export async function getMe(token) {
    const res = await axiosClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
    })
    return res.data
}

/**
 * Exchange a refresh token for a new access + refresh token pair.
 */
export async function refreshToken(refreshToken) {
    const res = await axiosClient.post('/auth/refresh', {
        refresh_token: refreshToken,
    })
    return res.data
}
