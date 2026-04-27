/**
 * ============================================================
 * App.jsx — Root component with sidebar layout
 * ============================================================
 * Sidebar + main content layout with animated background.
 * ============================================================
 */

import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { DashboardProvider } from './context/DashboardContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import DataCleaning from './pages/DataCleaning'
import Query from './pages/Query'
import History from './pages/History'
import DataProfile from './pages/DataProfile'
import MultiQuery from './pages/MultiQuery'
import Forecast from './pages/Forecast'
import Compare from './pages/Compare'
import Alerts from './pages/Alerts'
import WhatIf from './pages/WhatIf'
import ChatSidebar from './components/ChatSidebar'

function App() {
    return (
        <AuthProvider>
            <DashboardProvider>
                <BrowserRouter>
                    {/* Animated mesh background */}
                    <div className="mesh-bg" />

                    <div className="app-container">
                        <Navbar />
                        <main className="main-content">
                          <ErrorBoundary>
                            <div className="page-animate">
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
                                <Route path="/cleaning" element={
                                    <ProtectedRoute><DataCleaning /></ProtectedRoute>
                                } />
                                <Route path="/query" element={
                                    <ProtectedRoute><Query /></ProtectedRoute>
                                } />
                                <Route path="/history" element={
                                    <ProtectedRoute><History /></ProtectedRoute>
                                } />
                                <Route path="/profile" element={
                                    <ProtectedRoute><DataProfile /></ProtectedRoute>
                                } />
                                <Route path="/multi-query" element={
                                    <ProtectedRoute><MultiQuery /></ProtectedRoute>
                                } />
                                <Route path="/forecast" element={
                                    <ProtectedRoute><Forecast /></ProtectedRoute>
                                } />
                                <Route path="/compare" element={
                                    <ProtectedRoute><Compare /></ProtectedRoute>
                                } />
                                <Route path="/alerts" element={
                                    <ProtectedRoute><Alerts /></ProtectedRoute>
                                } />
                                <Route path="/what-if" element={
                                    <ProtectedRoute><WhatIf /></ProtectedRoute>
                                } />

                                {/* Default redirect */}
                                <Route path="*" element={<Navigate to="/dashboard" replace />} />
                            </Routes>
                            </div>
                          </ErrorBoundary>
                        </main>
                        <ChatSidebar />
                    </div>
                </BrowserRouter>
            </DashboardProvider>
        </AuthProvider>
    )
}

export default App
