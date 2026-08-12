/**
 * ============================================================
 * Dashboard — InsightAI glassmorphic analytics workspace
 * ============================================================
 * All logic preserved: DashboardContext, KPI calcs, filter,
 * ChartRenderer, InsightDisplay, removePanel, clearPanels
 * ============================================================
 */

import React, { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useDashboard } from '../hooks/useDashboard'
import ChartRenderer from '../components/ChartRenderer'
import InsightDisplay from '../components/InsightDisplay'

const FILTER_OPTIONS = [
    { value: 'all',   label: 'All' },
    { value: 'bar',   label: '📊 Bar' },
    { value: 'line',  label: '📈 Line' },
    { value: 'pie',   label: '🥧 Pie' },
    { value: 'table', label: '📋 Table' },
]

function Dashboard() {
    const { user } = useAuth()
    const { panels, removePanel, clearPanels } = useDashboard()
    const [filterType, setFilterType] = useState('all')

    const filteredPanels = useMemo(() => {
        if (filterType === 'all') return panels
        return panels.filter((p) => p.visualization?.chart_type === filterType)
    }, [panels, filterType])

    const kpis = useMemo(() => {
        const totalPanels = panels.length
        const chartTypes  = panels.reduce((acc, p) => {
            const type = p.visualization?.chart_type || 'unknown'
            acc[type] = (acc[type] || 0) + 1
            return acc
        }, {})
        const avgDataSize = panels.length > 0
            ? Math.round(panels.reduce((sum, p) => sum + (p.data?.length || 0), 0) / panels.length)
            : 0
        return { totalPanels, chartTypes, avgDataSize }
    }, [panels])

    const mostUsed = Object.entries(kpis.chartTypes).sort((a, b) => b[1] - a[1])[0]?.[0] || '—'
    const hour = new Date().getHours()
    const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'

    return (
        <div style={{ position: 'relative' }}>
            {/* Background orbs */}
            <div className="bg-orb bg-orb-1" />
            <div className="bg-orb bg-orb-2" />

            {/* Header */}
            <div style={{ marginBottom: 'var(--space-xl)' }}>
                <h1 className="page-title">{greeting}, {user?.username} 👋</h1>
                <p className="page-subtitle">Your AI analytics workspace — pin charts, track queries, explore your data.</p>
            </div>

            {/* ── KPI Cards ── */}
            <div className="grid-4" style={{ marginBottom: 'var(--space-xl)' }}>
                <div className="card kpi-card">
                    <div className="kpi-icon">📌</div>
                    <div className="kpi-value">{kpis.totalPanels}</div>
                    <div className="kpi-label">Pinned Charts</div>
                </div>
                <div className="card kpi-card">
                    <div className="kpi-icon">🎨</div>
                    <div className="kpi-value">{Object.keys(kpis.chartTypes).length}</div>
                    <div className="kpi-label">Chart Types</div>
                </div>
                <div className="card kpi-card">
                    <div className="kpi-icon">📐</div>
                    <div className="kpi-value">{kpis.avgDataSize.toLocaleString()}</div>
                    <div className="kpi-label">Avg Data Rows</div>
                </div>
                <div className="card kpi-card">
                    <div className="kpi-icon">🏆</div>
                    <div className="kpi-value">{mostUsed}</div>
                    <div className="kpi-label">Most Used Type</div>
                </div>
            </div>

            {/* ── Quick Actions ── */}
            <div className="grid-3" style={{ marginBottom: 'var(--space-md)' }}>
                <Link to="/upload" className="card action-card" style={{ color: 'inherit' }}>
                    <div className="action-icon">📁</div>
                    <div className="action-label">Upload Dataset</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        CSV or Excel files
                    </span>
                </Link>
                <Link to="/query" className="card action-card" style={{ color: 'inherit' }}>
                    <div className="action-icon">🔍</div>
                    <div className="action-label">Run a Query</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        Ask in plain English
                    </span>
                </Link>
                <Link to="/history" className="card action-card" style={{ color: 'inherit' }}>
                    <div className="action-icon">📜</div>
                    <div className="action-label">Query History</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        Last 50 queries
                    </span>
                </Link>
            </div>

            {/* ── ML Tools Row ── */}
            <div className="grid-3" style={{ marginBottom: 'var(--space-xl)' }}>
                <Link to="/anomalies" className="card action-card" style={{ color: 'inherit' }}>
                    <div className="action-icon" style={{ background: 'rgba(231,76,60,0.1)', border: '1px solid rgba(231,76,60,0.25)' }}>🚨</div>
                    <div className="action-label">Anomaly Detection</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        Isolation Forest ML
                    </span>
                </Link>
                <Link to="/cluster" className="card action-card" style={{ color: 'inherit' }}>
                    <div className="action-icon" style={{ background: 'rgba(241,196,15,0.1)', border: '1px solid rgba(241,196,15,0.25)' }}>🎯</div>
                    <div className="action-label">K-Means Clustering</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        Elbow method auto-K
                    </span>
                </Link>
                <Link to="/forecast" className="card action-card" style={{ color: 'inherit' }}>
                    <div className="action-icon" style={{ background: 'rgba(46,204,113,0.1)', border: '1px solid rgba(46,204,113,0.25)' }}>📈</div>
                    <div className="action-label">Time-Series Forecast</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        Prophet AI model
                    </span>
                </Link>
            </div>

            {/* ── Filter & Controls Bar ── */}
            {panels.length > 0 && (
                <div className="dashboard-controls" style={{ marginBottom: 'var(--space-lg)' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-secondary)', flexShrink: 0 }}>
                        Pinned Charts
                    </span>
                    <div className="filter-pills">
                        {FILTER_OPTIONS.map((f) => (
                            <button
                                key={f.value}
                                className={`filter-pill ${filterType === f.value ? 'active' : ''}`}
                                onClick={() => setFilterType(f.value)}
                            >
                                {f.label}
                            </button>
                        ))}
                    </div>
                    <button
                        className="btn btn-danger"
                        onClick={clearPanels}
                        style={{ marginLeft: 'auto', padding: '0.3rem 0.9rem', fontSize: '0.8rem' }}
                    >
                        🗑 Clear All
                    </button>
                </div>
            )}

            {/* ── Chart Grid ── */}
            {filteredPanels.length > 0 ? (
                <div className="dashboard-grid">
                    {filteredPanels.map((panel) => (
                        <div key={panel.id} className="card dashboard-panel">
                            <div className="panel-header">
                                <div>
                                    <div className="panel-title">{panel.query}</div>
                                    <div className="panel-meta">
                                        {panel.visualization?.chart_type} • {panel.data?.length || 0} rows
                                    </div>
                                </div>
                                <button
                                    className="btn-icon"
                                    onClick={() => removePanel(panel.id)}
                                    title="Remove from dashboard"
                                >
                                    ✕
                                </button>
                            </div>
                            {panel.data && panel.visualization && (
                                <ChartRenderer data={panel.data} visualization={panel.visualization} />
                            )}
                            {panel.insights && (
                                <div style={{ marginTop: 'var(--space-sm)' }}>
                                    <InsightDisplay insights={panel.insights} />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            ) : panels.length === 0 ? (
                <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem', marginTop: 'var(--space-lg)' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
                    <h3 style={{ color: 'var(--color-text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                        No charts pinned yet
                    </h3>
                    <p style={{ color: 'var(--color-text-muted)', maxWidth: 400, margin: '0 auto 1.5rem' }}>
                        Go to the <Link to="/query">Query page</Link>, run an analysis, and click <strong>"Add to Dashboard"</strong> to pin results here.
                    </p>
                    <Link to="/query" className="btn btn-primary" style={{ display: 'inline-flex' }}>
                        Run First Query →
                    </Link>
                </div>
            ) : (
                <div className="card" style={{ textAlign: 'center', padding: '2rem', marginTop: 'var(--space-lg)' }}>
                    <p style={{ color: 'var(--color-text-muted)' }}>
                        No "{filterType}" charts found. Try a different filter.
                    </p>
                </div>
            )}
        </div>
    )
}

export default Dashboard
