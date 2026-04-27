/**
 * ============================================================
 * Axios Client — Configured HTTP client
 * ============================================================
 * Automatically attaches JWT token to all requests.
 * On 401, attempts a token refresh before redirecting to login.
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

// ── Response interceptor: handle 401 with token refresh ──
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error)
        } else {
            prom.resolve(token)
        }
    })
    failedQueue = []
}

axiosClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // Only attempt refresh for 401 errors, and not for auth endpoints themselves
        if (
            error.response?.status === 401 &&
            !originalRequest._retry &&
            !originalRequest.url?.includes('/auth/')
        ) {
            if (isRefreshing) {
                // Queue this request until refresh completes
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject })
                }).then((token) => {
                    originalRequest.headers.Authorization = `Bearer ${token}`
                    return axiosClient(originalRequest)
                })
            }

            originalRequest._retry = true
            isRefreshing = true

            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
                try {
                    const res = await axios.post(`${API_BASE}/api/auth/refresh`, {
                        refresh_token: refreshToken,
                    })
                    const { access_token, refresh_token: newRefresh } = res.data
                    localStorage.setItem('token', access_token)
                    localStorage.setItem('refresh_token', newRefresh)
                    processQueue(null, access_token)

                    originalRequest.headers.Authorization = `Bearer ${access_token}`
                    return axiosClient(originalRequest)
                } catch (refreshError) {
                    processQueue(refreshError, null)
                    // Refresh failed — clear everything and redirect
                    localStorage.removeItem('token')
                    localStorage.removeItem('refresh_token')
                    window.location.href = '/login'
                    return Promise.reject(refreshError)
                } finally {
                    isRefreshing = false
                }
            }

            // No refresh token available — redirect to login
            localStorage.removeItem('token')
            localStorage.removeItem('refresh_token')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export default axiosClient
