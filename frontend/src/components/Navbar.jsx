/**
 * ============================================================
 * Navbar — InsightAI glassmorphic sticky navigation bar
 * ============================================================
 */

import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

function Navbar() {
    const { user, logout } = useAuth()
    const location = useLocation()

    const isActive = (path) => location.pathname === path ? 'active' : ''

    return (
        <nav className="navbar">
            {/* Brand */}
            <Link to="/dashboard" className="navbar-brand">
                ✦ InsightAI
            </Link>

            {user ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {/* Nav links */}
                    <div className="navbar-links">
                        <Link to="/dashboard" className={isActive('/dashboard')}>Dashboard</Link>
                        <Link to="/upload"    className={isActive('/upload')}>Upload</Link>
                        <Link to="/query"     className={isActive('/query')}>Query</Link>
                        <Link to="/history"  className={isActive('/history')}>History</Link>
                    </div>

                    {/* User chip */}
                    <div className="navbar-user-chip">
                        <div className="navbar-avatar">
                            {user.username?.charAt(0) || 'U'}
                        </div>
                        <span style={{ fontSize: '0.8rem' }}>{user.username}</span>
                    </div>

                    {/* Logout */}
                    <button className="navbar-logout" onClick={logout}>
                        Logout
                    </button>
                </div>
            ) : (
                <div className="navbar-links">
                    <Link to="/login"    className={isActive('/login')}>Login</Link>
                    <Link to="/register" className={isActive('/register')}>Register</Link>
                </div>
            )}
        </nav>
    )
}

export default Navbar
