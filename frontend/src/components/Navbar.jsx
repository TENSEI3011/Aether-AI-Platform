/**
 * ============================================================
 * Sidebar Navigation — Aether Flow V2
 * ============================================================
 * Collapsible vertical sidebar with:
 *   - Icon + label nav items grouped by function
 *   - Collapse to icon-only (64px) mode
 *   - Active glow indicator
 *   - Theme toggle + notification bell + user section
 *   - Graceful mobile overlay
 * ============================================================
 */

import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import NotificationBell from './NotificationBell'

const NAV_GROUPS = [
    {
        title: 'Overview',
        items: [
            { to: '/dashboard', label: 'Dashboard', icon: '◻️' },
            { to: '/upload', label: 'Upload', icon: '⬆' },
            { to: '/cleaning', label: 'Cleaning', icon: '🧹' },
        ]
    },
    {
        title: 'Analysis',
        items: [
            { to: '/query', label: 'Query', icon: '✦' },
            { to: '/multi-query', label: 'Join', icon: '⟐' },
            { to: '/forecast', label: 'Forecast', icon: '◈' },
            { to: '/compare', label: 'Compare', icon: '⇄' },
            { to: '/what-if', label: 'What-If', icon: '◇' },
        ]
    },
    {
        title: 'Monitor',
        items: [
            { to: '/alerts', label: 'Alerts', icon: '◉' },
            { to: '/history', label: 'History', icon: '↻' },
            { to: '/profile', label: 'Profile', icon: '▦' },
        ]
    }
]

function Navbar() {
    const { user, logout } = useAuth()
    const location = useLocation()
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)

    // ── Theme Toggle ──────────────────────────────────────
    const [isDark, setIsDark] = useState(() => {
        return localStorage.getItem('theme') !== 'light'
    })

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', isDark ? '' : 'light')
        localStorage.setItem('theme', isDark ? 'dark' : 'light')
    }, [isDark])

    useEffect(() => {
        const saved = localStorage.getItem('theme')
        if (saved === 'light') {
            setIsDark(false)
            document.documentElement.setAttribute('data-theme', 'light')
        }
    }, [])

    // Close mobile menu on route change
    useEffect(() => {
        setMobileOpen(false)
    }, [location.pathname])

    const isActive = (path) => location.pathname === path

    // Non-authenticated: show minimal top bar
    if (!user) {
        return (
            <nav className="topbar-auth">
                <Link to="/login" className="navbar-brand">🧠 AI Analysis Platform</Link>
                <div className="topbar-auth-links">
                    <Link to="/login" className={`btn ${location.pathname === '/login' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '0.4rem 1.2rem', fontSize: '0.85rem' }}>Login</Link>
                    <Link to="/register" className={`btn ${location.pathname === '/register' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '0.4rem 1.2rem', fontSize: '0.85rem' }}>Register</Link>
                </div>
            </nav>
        )
    }

    return (
        <>
            {/* Mobile toggle */}
            <button className="sidebar-mobile-toggle" onClick={() => setMobileOpen(v => !v)} aria-label="Toggle menu">
                <span className={`hamburger-icon ${mobileOpen ? 'open' : ''}`}>
                    <span /><span /><span />
                </span>
            </button>

            {/* Mobile overlay */}
            {mobileOpen && <div className="sidebar-overlay" onClick={() => setMobileOpen(false)} />}

            {/* Sidebar */}
            <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
                {/* Brand */}
                <div className="sidebar-brand">
                    <Link to="/dashboard" style={{ textDecoration: 'none' }}>
                        <span className="sidebar-brand-icon">🧠</span>
                        {!collapsed && <span className="sidebar-brand-text">Aether AI</span>}
                    </Link>
                </div>

                {/* Collapse Toggle */}
                <button className="sidebar-collapse-btn" onClick={() => setCollapsed(c => !c)} title={collapsed ? 'Expand' : 'Collapse'}>
                    {collapsed ? '▸' : '◂'}
                </button>

                {/* Navigation Groups */}
                <nav className="sidebar-nav">
                    {NAV_GROUPS.map((group) => (
                        <div key={group.title} className="sidebar-group">
                            {!collapsed && <div className="sidebar-group-title">{group.title}</div>}
                            {group.items.map((item) => (
                                <Link
                                    key={item.to}
                                    to={item.to}
                                    className={`sidebar-item ${isActive(item.to) ? 'active' : ''}`}
                                    title={collapsed ? item.label : undefined}
                                >
                                    <span className="sidebar-item-icon">{item.icon}</span>
                                    {!collapsed && <span className="sidebar-item-label">{item.label}</span>}
                                    {isActive(item.to) && <span className="sidebar-active-dot" />}
                                </Link>
                            ))}
                        </div>
                    ))}
                </nav>

                {/* Bottom Actions */}
                <div className="sidebar-footer">
                    <div className="sidebar-footer-actions">
                        <NotificationBell />
                        <button
                            className="sidebar-theme-btn"
                            onClick={() => setIsDark(d => !d)}
                            title={isDark ? 'Light mode' : 'Dark mode'}
                        >
                            {isDark ? '☀' : '🌙'}
                        </button>
                    </div>

                    {/* User */}
                    {!collapsed && (
                        <div className="sidebar-user">
                            <div className="sidebar-user-avatar">
                                {user.username?.[0]?.toUpperCase() || '?'}
                            </div>
                            <div className="sidebar-user-info">
                                <div className="sidebar-user-name">{user.username}</div>
                                <button className="sidebar-logout" onClick={logout}>Sign out</button>
                            </div>
                        </div>
                    )}
                    {collapsed && (
                        <button className="sidebar-theme-btn" onClick={logout} title="Sign out" style={{ color: 'var(--color-danger)', marginTop: '0.5rem' }}>
                            ⏻
                        </button>
                    )}
                </div>
            </aside>
        </>
    )
}

export default Navbar
