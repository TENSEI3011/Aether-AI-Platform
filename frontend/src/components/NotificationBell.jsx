/**
 * ============================================================
 * NotificationBell — Alert notification dropdown in Navbar
 * ============================================================
 */

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../api/alerts'

function NotificationBell() {
    const [notifications, setNotifications] = useState([])
    const [unreadCount, setUnreadCount] = useState(0)
    const [isOpen, setIsOpen] = useState(false)
    const dropdownRef = useRef(null)

    // Fetch notifications on mount and every 30 seconds
    const fetchNotifications = useCallback(async () => {
        try {
            const data = await getNotifications()
            setNotifications(data.notifications || [])
            setUnreadCount(data.unread_count || 0)
        } catch {
            // silently fail
        }
    }, [])

    useEffect(() => {
        fetchNotifications()
        const interval = setInterval(fetchNotifications, 30000)
        return () => clearInterval(interval)
    }, [fetchNotifications])

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClick = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setIsOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClick)
        return () => document.removeEventListener('mousedown', handleClick)
    }, [])

    const handleMarkRead = useCallback(async (id) => {
        try {
            await markNotificationRead(id)
            setNotifications(prev => prev.map(n =>
                n.id === id ? { ...n, is_read: true } : n
            ))
            setUnreadCount(prev => Math.max(0, prev - 1))
        } catch { /* ignore */ }
    }, [])

    const handleMarkAllRead = useCallback(async () => {
        try {
            await markAllNotificationsRead()
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
            setUnreadCount(0)
        } catch { /* ignore */ }
    }, [])

    return (
        <div className="notification-bell-container" ref={dropdownRef}>
            <button
                className="notification-bell-btn"
                onClick={() => setIsOpen(v => !v)}
                title="Notifications"
            >
                🔔
                {unreadCount > 0 && (
                    <span className="notification-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
                )}
            </button>

            {isOpen && (
                <div className="notification-dropdown">
                    <div className="notification-header">
                        <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>Notifications</span>
                        {unreadCount > 0 && (
                            <button
                                onClick={handleMarkAllRead}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--color-accent)',
                                    cursor: 'pointer',
                                    fontSize: '0.75rem',
                                }}
                            >
                                Mark all read
                            </button>
                        )}
                    </div>

                    <div className="notification-list">
                        {notifications.length === 0 ? (
                            <div style={{
                                padding: '2rem 1rem',
                                textAlign: 'center',
                                color: 'var(--color-text-muted)',
                                fontSize: '0.85rem',
                            }}>
                                No notifications yet
                            </div>
                        ) : (
                            notifications.slice(0, 10).map(n => (
                                <div
                                    key={n.id}
                                    className={`notification-item ${n.is_read ? '' : 'unread'}`}
                                    onClick={() => !n.is_read && handleMarkRead(n.id)}
                                >
                                    <div className="notification-message">{n.message}</div>
                                    <div className="notification-time">
                                        {n.created_at ? new Date(n.created_at).toLocaleString() : ''}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

export default NotificationBell
