/**
 * ============================================================
 * Register Page — Aether Flow Design
 * ============================================================
 * Premium glassmorphic registration card with gradient
 * headings, password validation, and polished form controls.
 * ============================================================
 */

import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

function Register() {
    const [username, setUsername] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const { register } = useAuth()
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        if (password.length < 6) {
            setError('Password must be at least 6 characters')
            return
        }
        setLoading(true)
        try {
            await register(username, email, password)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed')
        } finally {
            setLoading(false)
        }
    }

    const passwordStrength = password.length === 0 ? 0
        : password.length < 6 ? 1
        : password.length < 10 ? 2
        : 3

    const strengthColors = ['', '#EF4444', '#F59E0B', '#10B981']
    const strengthLabels = ['', 'Weak', 'Fair', 'Strong']

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
                        ✨
                    </div>
                </div>

                <h1>Create Account</h1>
                <p>Get started with AI-powered data analysis</p>

                {error && (
                    <div className="alert alert-error" style={{ animation: 'fadeIn 0.3s ease' }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label>Username</label>
                        <input
                            id="register-username"
                            className="input-field"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Choose a username"
                            required
                            autoComplete="username"
                        />
                    </div>
                    <div className="input-group">
                        <label>Email</label>
                        <input
                            id="register-email"
                            className="input-field"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your email"
                            required
                            autoComplete="email"
                        />
                    </div>
                    <div className="input-group">
                        <label>Password</label>
                        <div style={{ position: 'relative' }}>
                            <input
                                id="register-password"
                                className="input-field"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Create a password (min 6 characters)"
                                required
                                minLength={6}
                                autoComplete="new-password"
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
                                }}
                            >
                                {showPassword ? '🙈' : '👁️'}
                            </button>
                        </div>

                        {/* Password strength indicator */}
                        {password.length > 0 && (
                            <div style={{ marginTop: '8px' }}>
                                <div style={{
                                    display: 'flex',
                                    gap: '4px',
                                    marginBottom: '4px',
                                }}>
                                    {[1, 2, 3].map((level) => (
                                        <div
                                            key={level}
                                            style={{
                                                flex: 1,
                                                height: '3px',
                                                borderRadius: '2px',
                                                background: passwordStrength >= level
                                                    ? strengthColors[passwordStrength]
                                                    : 'rgba(74,68,85,0.3)',
                                                transition: 'background 0.3s ease',
                                            }}
                                        />
                                    ))}
                                </div>
                                <span style={{
                                    fontSize: '0.7rem',
                                    color: strengthColors[passwordStrength],
                                    fontWeight: 600,
                                }}>
                                    {strengthLabels[passwordStrength]}
                                </span>
                            </div>
                        )}
                    </div>

                    <button
                        id="register-submit"
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
                                Creating Account...
                            </span>
                        ) : 'Create Account'}
                    </button>
                </form>

                <div className="auth-footer">
                    Already have an account?{' '}
                    <Link to="/login">Sign In</Link>
                </div>
            </div>
        </div>
    )
}

export default Register
