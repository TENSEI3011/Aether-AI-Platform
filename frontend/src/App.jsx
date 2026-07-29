/**
 * ============================================================
 * App.jsx — Root component with routing and providers
 * ============================================================
 * Wraps the app in AuthProvider and DashboardProvider.
 * ============================================================
 */

import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { DashboardProvider } from './context/DashboardContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Query from './pages/Query'
import History from './pages/History'

function App() {
    return (
        <AuthProvider>
            <DashboardProvider>
                <BrowserRouter>
                    <div className="app-container">
                        <Navbar />
                        <main className="main-content">
                            <Routes>
                                {/* Public routes */}
                                <Route path="/login" element={<Login />} />
                                <Route path="/register" element={<Register />} />

                                {/* Protected routes — require JWT */}
                                <Route path="/dashboard" element={
                                    <ProtectedRoute><Dashboard /></ProtectedRoute>
                                } />
                                <Route path="/upload" element={
                                    <ProtectedRoute><Upload /></ProtectedRoute>
                                } />
                                <Route path="/query" element={
                                    <ProtectedRoute><Query /></ProtectedRoute>
                                } />
                                <Route path="/history" element={
                                    <ProtectedRoute><History /></ProtectedRoute>
                                } />

                                {/* Default redirect */}
                                <Route path="*" element={<Navigate to="/dashboard" replace />} />
                            </Routes>
                        </main>
                    </div>
                </BrowserRouter>
            </DashboardProvider>
        </AuthProvider>
    )
}

export default App
