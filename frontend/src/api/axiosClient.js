/**
 * ============================================================
 * Axios Client — Configured HTTP client
 * ============================================================
 * Automatically attaches JWT token to all requests.
 * ============================================================
 */

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

const axiosClient = axios.create({
    baseURL: `${API_BASE}/api`,
    headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: attach JWT ──────────────────────
axiosClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// ── Response interceptor: handle 401 ─────────────────────
axiosClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export default axiosClient
