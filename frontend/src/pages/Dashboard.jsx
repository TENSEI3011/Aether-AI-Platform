/**
 * ============================================================
 * Dashboard — Aether Flow Power BI–Style Analytics
 * ============================================================
 * Premium dark-mode analytics dashboard with:
 *   - Drag & drop panel reordering (react-grid-layout)
 *   - Resizable chart panels with corner handles
 *   - Glassmorphic KPI cards with gradient values
 *   - Quick action cards with hover glow effects
 *   - Chart filter controls bar
 *   - Pinned chart panels with export options
 *   - Confirm modal for destructive actions
 *   - Layout persistence across sessions
 * ============================================================
 */

import React, { useState, useMemo, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ResponsiveGridLayout } from 'react-grid-layout'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'
import { useAuth } from '../hooks/useAuth'
import { useDashboard } from '../hooks/useDashboard'
import { exportExcel } from '../api/datasets'
import ChartRenderer from '../components/ChartRenderer'
import InsightDisplay from '../components/InsightDisplay'
import ConfirmModal from '../components/ConfirmModal'

// Filter options for chart types
const FILTER_OPTIONS = [
    { value: 'all',       label: 'All Charts' },
    { value: 'bar',       label: 'Bar' },
    { value: 'line',      label: 'Line' },
    { value: 'pie',       label: 'Pie' },
    { value: 'scatter',   label: 'Scatter' },
    { value: 'histogram', label: 'Histogram' },
    { value: 'heatmap',   label: 'Heatmap' },
    { value: 'table',     label: 'Table' },
]

const QUICK_ACTIONS = [
    { to: '/upload', icon: '📁', label: 'Upload Dataset', desc: 'Import CSV or Excel files' },
    { to: '/query', icon: '🔍', label: 'Ask a Question', desc: 'Natural language analysis' },
    { to: '/history', icon: '📜', label: 'Query History', desc: 'Review past analyses' },
]

function Dashboard() {
    const { user } = useAuth()
    const {
        panels,
        removePanel,
        clearPanels,
        getGridLayout,
        onLayoutChange,
    } = useDashboard()
    const [filterType, setFilterType] = useState('all')
    const [showClearConfirm, setShowClearConfirm] = useState(false)
    const [isDragging, setIsDragging] = useState(false)

    // ── Filtered panels ──────────────────────────────────
    const filteredPanels = useMemo(() => {
        if (filterType === 'all') return panels
        return panels.filter((p) => p.visualization?.chart_type === filterType)
    }, [panels, filterType])

    // ── KPI calculations ─────────────────────────────────
    const kpis = useMemo(() => {
        const totalPanels = panels.length
        const chartTypes = panels.reduce((acc, p) => {
            const type = p.visualization?.chart_type || 'unknown'
            acc[type] = (acc[type] || 0) + 1
            return acc
        }, {})
        const avgDataSize = panels.length > 0
            ? Math.round(panels.reduce((sum, p) => sum + (p.data?.length || 0), 0) / panels.length)
            : 0
        return { totalPanels, chartTypes, avgDataSize }
    }, [panels])

    // ── Grid layout for visible panels ───────────────────
    const currentLayout = useMemo(() => {
        const fullLayout = getGridLayout()
        const visibleIds = new Set(filteredPanels.map((p) => p.id))
        return fullLayout.filter((l) => visibleIds.has(l.i))
    }, [getGridLayout, filteredPanels])

    const dashboardRef = useRef(null)

    // ── Export: PDF ──────────────────────────────────────
    const handleExportPDF = useCallback(async () => {
        const html2canvas = (await import('html2canvas')).default
        const { jsPDF } = await import('jspdf')
        const element = dashboardRef.current
        if (!element) return

        const canvas = await html2canvas(element, { backgroundColor: '#0E0E13', scale: 2 })
        const imgData = canvas.toDataURL('image/png')
        const pdf = new jsPDF('l', 'mm', 'a4')
        const pdfWidth = pdf.internal.pageSize.getWidth()
        const pdfHeight = (canvas.height * pdfWidth) / canvas.width
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
        pdf.save('dashboard-report.pdf')
    }, [])

    // ── Export: Excel ────────────────────────────────────
    const handleExportExcel = useCallback(async (panel) => {
        if (!panel?.data) return
        const columns = panel.visualization ? [panel.visualization.x_axis, panel.visualization.y_axis].filter(Boolean) : Object.keys(panel.data[0] || {})
        await exportExcel(panel.data, columns, `${panel.query?.slice(0, 30) || 'data'}.xlsx`)
    }, [])

    // ── Export: Image ────────────────────────────────────
    const handleExportImage = useCallback(async (panelId) => {
        const html2canvas = (await import('html2canvas')).default
        const element = document.getElementById(`panel-${panelId}`)
        if (!element) return
        const canvas = await html2canvas(element, { backgroundColor: '#0E0E13', scale: 2 })
        const link = document.createElement('a')
        link.download = `chart-${panelId}.png`
        link.href = canvas.toDataURL('image/png')
        link.click()
    }, [])

    return (
        <div>
            {/* ── Page Header ──────────────────────────────── */}
            <div style={{ marginBottom: 'var(--space-xl)' }}>
                <h1 className="page-title" style={{ animation: 'fadeIn 0.4s ease' }}>Dashboard</h1>
                <p className="page-subtitle" style={{ animation: 'fadeIn 0.6s ease' }}>
                    Welcome back, <strong style={{ color: '#D2BBFF', fontWeight: 700 }}>{user?.username}</strong>. Your analytics workspace.
                </p>
            </div>

            {/* ── KPI Cards ───────────────────────────────────── */}
            <div className="grid-4" style={{ animation: 'fadeIn 0.5s ease' }}>
                {[
                    { value: kpis.totalPanels, label: 'Pinned Charts', icon: '📊' },
                    { value: Object.keys(kpis.chartTypes).length, label: 'Chart Types', icon: '📈' },
                    { value: kpis.avgDataSize, label: 'Avg Data Rows', icon: '📋' },
                    { value: Object.entries(kpis.chartTypes).sort((a, b) => b[1] - a[1])[0]?.[0] || '—', label: 'Most Used Type', icon: '⭐' },
                ].map((kpi, i) => (
                    <div key={i} className="card kpi-card" style={{ animation: `fadeIn ${0.3 + i * 0.1}s ease` }}>
                        <div style={{
                            fontSize: '1.2rem',
                            marginBottom: '0.5rem',
                            opacity: 0.7,
                        }}>
                            {kpi.icon}
                        </div>
                        <div className="kpi-value">{kpi.value}</div>
                        <div className="kpi-label">{kpi.label}</div>
                    </div>
                ))}
            </div>

            {/* ── Quick Actions ────────────────────────────────── */}
            <div className="grid-3" style={{ marginTop: 'var(--space-xl)', animation: 'fadeIn 0.7s ease' }}>
                {QUICK_ACTIONS.map((action) => (
                    <Link key={action.to} to={action.to} style={{ textDecoration: 'none' }}>
                        <div className="card stat-card" style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '0.5rem',
                        }}>
                            <div style={{
                                fontSize: '2rem',
                                width: '52px',
                                height: '52px',
                                borderRadius: '14px',
                                background: 'rgba(124,58,237,0.10)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}>
                                {action.icon}
                            </div>
                            <div className="stat-label" style={{
                                color: '#E4E1E9',
                                fontWeight: 600,
                                fontSize: '0.9rem',
                            }}>
                                {action.label}
                            </div>
                            <div style={{
                                color: '#958DA1',
                                fontSize: '0.75rem',
                            }}>
                                {action.desc}
                            </div>
                        </div>
                    </Link>
                ))}
            </div>

            {/* ── Filter & Controls Bar ───────────────────────── */}
            {panels.length > 0 && (
                <div className="dashboard-controls" style={{ marginTop: 'var(--space-xl)', animation: 'fadeIn 0.8s ease' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <h3 style={{
                            margin: 0,
                            fontSize: '0.95rem',
                            fontWeight: 700,
                            background: 'linear-gradient(135deg, #7C3AED, #A855F7)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text',
                        }}>
                            📊 Pinned Charts
                        </h3>

                        {/* Drag hint */}
                        <span style={{
                            fontSize: '0.7rem',
                            color: '#958DA1',
                            background: 'rgba(124,58,237,0.08)',
                            padding: '3px 10px',
                            borderRadius: '20px',
                            border: '1px solid rgba(124,58,237,0.12)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                        }}>
                            <span style={{ fontSize: '0.8rem' }}>⇔</span> Drag &amp; resize panels
                        </span>

                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                            {FILTER_OPTIONS.map((f) => (
                                <button
                                    key={f.value}
                                    className={`btn ${filterType === f.value ? 'btn-primary' : 'btn-secondary'}`}
                                    onClick={() => setFilterType(f.value)}
                                    style={{
                                        padding: '0.3rem 0.75rem',
                                        fontSize: '0.75rem',
                                        borderRadius: '6px',
                                    }}
                                >
                                    {f.label}
                                </button>
                            ))}
                        </div>
                        <button
                            className="btn btn-secondary"
                            onClick={handleExportPDF}
                            style={{ padding: '0.3rem 0.75rem', fontSize: '0.75rem', borderRadius: '6px' }}
                        >
                            📥 Export PDF
                        </button>
                        <button
                            className="btn btn-secondary"
                            onClick={() => setShowClearConfirm(true)}
                            style={{
                                marginLeft: 'auto',
                                padding: '0.3rem 0.75rem',
                                fontSize: '0.75rem',
                                borderRadius: '6px',
                                color: '#EF4444',
                                borderColor: 'rgba(239,68,68,0.2)',
                            }}
                        >
                            🗑 Clear All
                        </button>
                    </div>
                </div>
            )}

            {/* ── Draggable / Resizable Chart Grid ─────────────── */}
            {filteredPanels.length > 0 ? (
                <div
                    ref={dashboardRef}
                    className={`rgl-dashboard${isDragging ? ' rgl-dragging' : ''}`}
                    style={{ marginTop: 'var(--space-lg)' }}
                >
                    <ResponsiveGridLayout
                        className="dashboard-rgl"
                        layouts={{ lg: currentLayout }}
                        breakpoints={{ lg: 1200, md: 900, sm: 600, xs: 0 }}
                        cols={{ lg: 12, md: 8, sm: 4, xs: 2 }}
                        rowHeight={100}
                        margin={[16, 16]}
                        containerPadding={[0, 0]}
                        onLayoutChange={onLayoutChange}
                        onDragStart={() => setIsDragging(true)}
                        onDragStop={() => setIsDragging(false)}
                        onResizeStart={() => setIsDragging(true)}
                        onResizeStop={() => setIsDragging(false)}
                        draggableHandle=".panel-drag-handle"
                        isResizable={true}
                        isDraggable={true}
                        useCSSTransforms={true}
                        compactType="vertical"
                    >
                        {filteredPanels.map((panel, i) => (
                            <div
                                key={panel.id}
                                id={`panel-${panel.id}`}
                                className="card dashboard-panel rgl-panel"
                                style={{ animation: `fadeIn ${0.3 + i * 0.05}s ease` }}
                            >
                                {/* Panel Header — acts as drag handle */}
                                <div className="panel-header panel-drag-handle">
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 0 }}>
                                        {/* Drag grip icon */}
                                        <div className="drag-grip" title="Drag to reorder">
                                            <span></span><span></span><span></span>
                                            <span></span><span></span><span></span>
                                        </div>
                                        <div style={{ minWidth: 0 }}>
                                            <h4 className="panel-title">{panel.query}</h4>
                                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '4px' }}>
                                                <span className="badge badge-success" style={{
                                                    background: 'rgba(124,58,237,0.12)',
                                                    color: '#D2BBFF',
                                                    fontSize: '0.65rem',
                                                }}>
                                                    {panel.visualization?.chart_type}
                                                </span>
                                                <span className="panel-meta">
                                                    {panel.data?.length || 0} rows
                                                </span>
                                            </div>
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

                                {/* Panel Export Buttons */}
                                <div style={{ display: 'flex', gap: '4px', marginBottom: 'var(--space-sm)' }}>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => handleExportExcel(panel)}
                                        style={{ padding: '3px 10px', fontSize: '0.65rem', borderRadius: '6px' }}
                                    >
                                        📊 Excel
                                    </button>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => handleExportImage(panel.id)}
                                        style={{ padding: '3px 10px', fontSize: '0.65rem', borderRadius: '6px' }}
                                    >
                                        🖼️ Image
                                    </button>
                                </div>

                                {/* Panel Chart — fills remaining space */}
                                <div className="panel-chart-area">
                                    {panel.data && panel.visualization && (
                                        <ChartRenderer data={panel.data} visualization={panel.visualization} />
                                    )}
                                </div>

                                {/* Panel Insights (collapsed) */}
                                {panel.insights && (
                                    <div style={{ marginTop: 'var(--space-sm)' }}>
                                        <InsightDisplay insights={panel.insights} />
                                    </div>
                                )}
                            </div>
                        ))}
                    </ResponsiveGridLayout>
                </div>
            ) : panels.length === 0 ? (
                <div className="card" style={{
                    marginTop: 'var(--space-xl)',
                    textAlign: 'center',
                    padding: '4rem 2rem',
                    animation: 'fadeIn 0.6s ease',
                    background: 'linear-gradient(135deg, rgba(124,58,237,0.04), rgba(219,39,119,0.02))',
                }}>
                    <div style={{
                        fontSize: '3.5rem',
                        marginBottom: '1rem',
                        filter: 'drop-shadow(0 0 20px rgba(124,58,237,0.3))',
                    }}>
                        📊
                    </div>
                    <h3 style={{
                        color: '#E4E1E9',
                        marginBottom: '0.75rem',
                        fontWeight: 700,
                        fontSize: '1.1rem',
                    }}>
                        No charts pinned yet
                    </h3>
                    <p style={{
                        color: '#958DA1',
                        maxWidth: '400px',
                        margin: '0 auto',
                        lineHeight: 1.6,
                    }}>
                        Go to the{' '}
                        <Link to="/query" style={{ color: '#D2BBFF', fontWeight: 600 }}>
                            Query page
                        </Link>,
                        run an analysis, and click "Add to Dashboard" to pin results here.
                    </p>
                </div>
            ) : (
                <div className="card" style={{
                    marginTop: 'var(--space-lg)',
                    textAlign: 'center',
                    padding: '2.5rem',
                }}>
                    <p style={{ color: '#958DA1' }}>
                        No "{filterType}" charts found. Try a different filter.
                    </p>
                </div>
            )}

            {/* Confirmation dialog for Clear All */}
            <ConfirmModal
                open={showClearConfirm}
                title="Clear All Charts?"
                message="This will remove all pinned charts from your dashboard. This action cannot be undone."
                confirmLabel="🗑 Clear All"
                onConfirm={() => { clearPanels(); setShowClearConfirm(false) }}
                onCancel={() => setShowClearConfirm(false)}
            />
        </div>
    )
}

export default Dashboard
