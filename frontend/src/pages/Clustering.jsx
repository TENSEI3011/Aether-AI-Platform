/**
 * ============================================================
 * Clustering Page — K-Means with automatic Elbow Method
 * ============================================================
 * Calls POST /api/queries/cluster with dataset_id.
 * Shows cluster sizes as visual bars, cluster centers table,
 * and the elbow inertia curve data.
 * ============================================================
 */

import React, { useState, useCallback } from 'react'
import axiosClient from '../api/axiosClient'

// Simple bar-chart bar component for cluster sizes
function ClusterBar({ label, count, max, color }) {
    const pct = max > 0 ? (count / max) * 100 : 0
    return (
        <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                    Cluster {label}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{count} rows</span>
            </div>
            <div style={{ height: 8, background: 'rgba(255,255,255,0.06)', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{
                    height: '100%', width: `${pct}%`,
                    background: color,
                    borderRadius: 4,
                    transition: 'width 0.8s ease',
                }} />
            </div>
        </div>
    )
}

const CLUSTER_COLORS = [
    'linear-gradient(90deg, #6c63ff, #a855f7)',
    'linear-gradient(90deg, #00d1ff, #0078ff)',
    'linear-gradient(90deg, #2ecc71, #1abc9c)',
    'linear-gradient(90deg, #f1c40f, #e67e22)',
    'linear-gradient(90deg, #e74c3c, #c0392b)',
    'linear-gradient(90deg, #e91e8c, #9c27b0)',
    'linear-gradient(90deg, #00bcd4, #009688)',
    'linear-gradient(90deg, #ff9800, #ff5722)',
]

function Clustering() {
    const [datasetId, setDatasetId] = useState('')
    const [maxK, setMaxK]           = useState(8)
    const [loading, setLoading]     = useState(false)
    const [result, setResult]       = useState(null)
    const [error, setError]         = useState('')

    const handleRun = useCallback(async (e) => {
        e?.preventDefault()
        if (!datasetId.trim()) return
        setLoading(true); setError(''); setResult(null)
        try {
            const res = await axiosClient.post('/queries/cluster', {
                dataset_id: datasetId.trim(),
                max_k: parseInt(maxK),
            })
            setResult(res.data)
        } catch (err) {
            setError(err.response?.data?.detail || 'Clustering failed. Please check the dataset ID.')
        } finally {
            setLoading(false)
        }
    }, [datasetId, maxK])

    const clusterData = result?.cluster_result
    const maxCount = clusterData ? Math.max(...Object.values(clusterData.cluster_sizes || {})) : 1

    return (
        <div style={{ position: 'relative' }}>
            <div className="bg-orb bg-orb-1" />

            <h1 className="page-title">K-Means Clustering</h1>
            <p className="page-subtitle">
                Automatically group your data into meaningful segments using unsupervised machine learning
            </p>

            {/* ── Config Card ── */}
            <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c4c0ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                    ⚙️ Configure Clustering
                </div>
                <form onSubmit={handleRun} style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-lg)', alignItems: 'flex-end' }}>
                    <div className="input-group" style={{ flex: '1 1 220px', marginBottom: 0 }}>
                        <label>Dataset ID</label>
                        <input
                            className="input-field"
                            type="text"
                            value={datasetId}
                            onChange={(e) => setDatasetId(e.target.value)}
                            placeholder="e.g. 1 (from Upload page)"
                            required
                        />
                    </div>
                    <div className="input-group" style={{ flex: '1 1 180px', marginBottom: 0 }}>
                        <label>Max Clusters to Test (K)</label>
                        <input
                            className="input-field"
                            type="number"
                            min={2} max={15}
                            value={maxK}
                            onChange={(e) => setMaxK(e.target.value)}
                        />
                    </div>
                    <button
                        className="btn btn-primary"
                        type="submit"
                        disabled={loading || !datasetId.trim()}
                        style={{ flexShrink: 0, padding: '0.8rem 2rem' }}
                    >
                        {loading ? (
                            <><div className="spinner" style={{ width: 16, height: 16 }} /> Clustering...</>
                        ) : (
                            '🎯 Run Clustering'
                        )}
                    </button>
                </form>
            </div>

            {/* ── Algorithm info ── */}
            <div style={{
                background: 'rgba(108,99,255,0.05)',
                border: '1px solid rgba(108,99,255,0.2)',
                borderRadius: 'var(--border-radius-lg)',
                padding: 'var(--space-md) var(--space-lg)',
                marginBottom: 'var(--space-xl)',
                display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
            }}>
                <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>🧠</span>
                <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#c4c0ff', marginBottom: '0.3rem' }}>
                        ML Concept: K-Means + Elbow Method
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
                        K-Means partitions data by minimising within-cluster variance. The Elbow Method tests
                        K=2 to K_max and picks the "elbow" point where adding more clusters stops reducing inertia significantly.
                    </div>
                </div>
            </div>

            {/* ── Error ── */}
            {error && <div className="alert alert-error">{error}</div>}

            {/* ── Results ── */}
            {clusterData && (
                <div>
                    {/* KPI row */}
                    <div className="grid-4" style={{ marginBottom: 'var(--space-xl)' }}>
                        <div className="card kpi-card">
                            <div className="kpi-icon">🎯</div>
                            <div className="kpi-value" style={{ color: '#c4c0ff' }}>{clusterData.optimal_k}</div>
                            <div className="kpi-label">Optimal K</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">📦</div>
                            <div className="kpi-value">{clusterData.rows_clustered?.toLocaleString()}</div>
                            <div className="kpi-label">Rows Clustered</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">📐</div>
                            <div className="kpi-value">{clusterData.columns_used?.length}</div>
                            <div className="kpi-label">Features Used</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">⚙️</div>
                            <div className="kpi-value" style={{ fontSize: '0.85rem' }}>{clusterData.method}</div>
                            <div className="kpi-label">Method</div>
                        </div>
                    </div>

                    {/* Columns used */}
                    {clusterData.columns_used?.length > 0 && (
                        <div style={{ marginBottom: 'var(--space-xl)', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Features:</span>
                            {clusterData.columns_used.map(col => (
                                <span key={col} style={{
                                    fontSize: '0.75rem', padding: '0.2rem 0.6rem',
                                    background: 'rgba(108,99,255,0.12)', border: '1px solid rgba(108,99,255,0.3)',
                                    borderRadius: '999px', color: '#c4c0ff', fontWeight: 600,
                                }}>
                                    {col}
                                </span>
                            ))}
                        </div>
                    )}

                    <div className="grid-2" style={{ marginBottom: 'var(--space-xl)' }}>
                        {/* Cluster Sizes */}
                        <div className="card">
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c4c0ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-lg)' }}>
                                📊 Cluster Sizes
                            </div>
                            {Object.entries(clusterData.cluster_sizes || {})
                                .sort((a, b) => a[0] - b[0])
                                .map(([cid, count]) => (
                                    <ClusterBar
                                        key={cid}
                                        label={cid}
                                        count={count}
                                        max={maxCount}
                                        color={CLUSTER_COLORS[parseInt(cid) % CLUSTER_COLORS.length]}
                                    />
                                ))}
                        </div>

                        {/* Elbow Curve */}
                        <div className="card">
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#a6e6ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-lg)' }}>
                                📈 Elbow Curve (Inertia per K)
                            </div>
                            {clusterData.inertia_values?.length > 0 ? (
                                <div>
                                    {clusterData.inertia_values.map(({ k, inertia }) => {
                                        const maxInertia = Math.max(...clusterData.inertia_values.map(v => v.inertia))
                                        const pct = maxInertia > 0 ? (inertia / maxInertia) * 100 : 0
                                        return (
                                            <div key={k} style={{ marginBottom: '0.6rem' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.78rem', color: k === clusterData.optimal_k ? '#c4c0ff' : 'var(--color-text-muted)', fontWeight: k === clusterData.optimal_k ? 700 : 400 }}>
                                                        K={k} {k === clusterData.optimal_k ? ' ← Optimal' : ''}
                                                    </span>
                                                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{inertia.toLocaleString()}</span>
                                                </div>
                                                <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3 }}>
                                                    <div style={{
                                                        height: '100%', width: `${pct}%`,
                                                        background: k === clusterData.optimal_k
                                                            ? 'linear-gradient(90deg, #6c63ff, #a855f7)'
                                                            : 'rgba(255,255,255,0.12)',
                                                        borderRadius: 3,
                                                        transition: 'width 0.6s ease',
                                                    }} />
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            ) : (
                                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>No elbow data available.</p>
                            )}
                        </div>
                    </div>

                    {/* Cluster Centers */}
                    {clusterData.cluster_centers?.length > 0 && (
                        <div className="card">
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#2ecc71', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                                📍 Cluster Centers (Original Scale)
                            </div>
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Cluster</th>
                                            {Object.keys(clusterData.cluster_centers[0] || {}).map(col => (
                                                <th key={col}>{col}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {clusterData.cluster_centers.map((center, i) => (
                                            <tr key={i}>
                                                <td>
                                                    <span style={{
                                                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                                        width: 24, height: 24, borderRadius: '50%',
                                                        background: CLUSTER_COLORS[i % CLUSTER_COLORS.length],
                                                        fontSize: '0.7rem', fontWeight: 700, color: '#fff',
                                                    }}>{i}</span>
                                                </td>
                                                {Object.values(center).map((val, j) => (
                                                    <td key={j}>{val}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default Clustering
