/**
 * ProtectedRoute — Wraps routes that require authentication
 */

import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

function ProtectedRoute({ children }) {
    const { user, loading } = useAuth()

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '4rem' }}>
                <div className="spinner" />
            </div>
        )
    }

    if (!user) {
        return <Navigate to="/login" replace />
    }

    return children
}

export default ProtectedRoute
