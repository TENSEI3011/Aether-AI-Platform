/**
 * ============================================================
 * Login Page — Aether Flow Design
 * ============================================================
 * Premium glassmorphic auth card with gradient headings,
 * ambient glow effects, and polished form controls.
 * ============================================================
 */

import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const { login } = useAuth()
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            await login(username, password)
            navigate('/dashboard')
        } catch (err) {
            const detail = err.response?.data?.detail
            if (typeof detail === 'string') {
                setError(detail)
            } else if (Array.isArray(detail)) {
                setError(detail.map(d => d.msg || JSON.stringify(d)).join(', '))
            } else {
                setError('Login failed')
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="card auth-card" style={{ animation: 'fadeIn 0.5s ease' }}>
                {/* Top accent line */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '2px',
                    background: 'linear-gradient(90deg, #7C3AED, #A855F7, #DB2777)',
                    borderRadius: '12px 12px 0 0',
                }} />

                <div style={{ textAlign: 'center', marginBottom: '0.5rem' }}>
                    <div style={{
                        width: '52px',
                        height: '52px',
                        borderRadius: '14px',
                        background: 'linear-gradient(135deg, rgba(124,58,237,0.15), rgba(219,39,119,0.10))',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.5rem',
                        margin: '0 auto 1rem',
                        border: '1px solid rgba(124,58,237,0.15)',
                    }}>
                        🧠
                    </div>
                </div>

                <h1>Welcome Back</h1>
                <p>Sign in to your analysis platform</p>

                {error && (
                    <div className="alert alert-error" style={{ animation: 'fadeIn 0.3s ease' }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label>Username</label>
                        <input
                            id="login-username"
                            className="input-field"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter your username"
                            required
                            autoComplete="username"
                        />
                    </div>
                    <div className="input-group">
                        <label>Password</label>
                        <div style={{ position: 'relative' }}>
                            <input
                                id="login-password"
                                className="input-field"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                required
                                autoComplete="current-password"
                                style={{ paddingRight: '3rem' }}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword((v) => !v)}
                                aria-label={showPassword ? 'Hide password' : 'Show password'}
                                style={{
                                    position: 'absolute',
                                    right: 12,
                                    top: '50%',
                                    transform: 'translateY(-50%)',
                                    background: 'none',
                                    border: 'none',
                                    cursor: 'pointer',
                                    fontSize: '1.1rem',
                                    color: '#958DA1',
                                    padding: '4px',
                                    transition: 'color 0.15s ease',
                                }}
                            >
                                {showPassword ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>
                    <button
                        id="login-submit"
                        className="btn btn-primary"
                        style={{
                            width: '100%',
                            padding: '0.85rem',
                            fontSize: '0.95rem',
                            borderRadius: '10px',
                        }}
                        disabled={loading}
                    >
                        {loading ? (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span className="spinner" style={{ width: 18, height: 18 }} />
                                Signing in...
                            </span>
                        ) : 'Sign In'}
                    </button>
                </form>

                <div className="auth-footer">
                    Don't have an account?{' '}
                    <Link to="/register">Register</Link>
                </div>
            </div>
        </div>
    )
}

export default Login
