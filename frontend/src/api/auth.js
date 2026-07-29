/**
 * Auth API — Login, Register, and profile endpoints
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
