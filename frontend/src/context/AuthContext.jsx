/**
 * ============================================================
 * AuthContext — JWT authentication state management
 * ============================================================
 * Provides login, register, logout functions and token state
 * to all components via React Context.
 * ============================================================
 */

import React, { createContext, useState, useEffect } from 'react'
import { loginUser, registerUser, getMe } from '../api/auth'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(localStorage.getItem('token'))
    const [loading, setLoading] = useState(true)

    // On mount, verify existing token
    useEffect(() => {
        if (token) {
            getMe(token)
                .then((userData) => setUser(userData))
                .catch(() => {
                    // Token expired or invalid
                    localStorage.removeItem('token')
                    setToken(null)
                })
                .finally(() => setLoading(false))
        } else {
            setLoading(false)
        }
    }, [])

    const login = async (username, password) => {
        const data = await loginUser(username, password)
        localStorage.setItem('token', data.access_token)
        setToken(data.access_token)
        const userData = await getMe(data.access_token)
        setUser(userData)
        return data
    }

    const register = async (username, email, password) => {
        const data = await registerUser(username, email, password)
        localStorage.setItem('token', data.access_token)
        setToken(data.access_token)
        const userData = await getMe(data.access_token)
        setUser(userData)
        return data
    }

    const logout = () => {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
    }

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    )
}
