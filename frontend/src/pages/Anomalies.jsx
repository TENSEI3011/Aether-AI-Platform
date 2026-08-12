/**
 * ============================================================
 * Anomalies Page — Isolation Forest anomaly detection
 * ============================================================
 * Calls POST /api/queries/anomalies with dataset_id.
 * Displays anomaly rows, column stats, and a summary badge.
 * ============================================================
 */

import React, { useState, useCallback } from 'react'
import axiosClient from '../api/axiosClient'

function Anomalies() {
    const [datasetId, setDatasetId]         = useState('')
    const [contamination, setContamination] = useState(0.05)
    const [loading, setLoading]             = useState(false)
    const [result, setResult]               = useState(null)
    const [error, setError]                 = useState('')

    const handleRun = useCallback(async (e) => {
        e?.preventDefault()
        if (!datasetId.trim()) return
        setLoading(true); setError(''); setResult(null)
        try {
            const res = await axiosClient.post('/queries/anomalies', {
                dataset_id: datasetId.trim(),
                contamination: parseFloat(contamination),
            })
            setResult(res.data)
        } catch (err) {
            setError(err.response?.data?.detail || 'Anomaly detection failed. Please check the dataset ID.')
        } finally {
            setLoading(false)
        }
    }, [datasetId, contamination])

    const anomalyData = result?.anomaly_result

    return (
        <div style={{ position: 'relative' }}>
            <div className="bg-orb bg-orb-1" />
            <div className="bg-orb bg-orb-2" />

            <h1 className="page-title">Anomaly Detection</h1>
            <p className="page-subtitle">
                Use Isolation Forest (ML) to automatically find unusual outliers in your dataset
            </p>

            {/* ── Config Card ── */}
            <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c4c0ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                    🔬 Configure Detection
                </div>
                <form onSubmit={handleRun} style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-lg)', alignItems: 'flex-end' }}>
                    <div className="input-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
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
                    <div className="input-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
                        <label>Contamination Rate ({(contamination * 100).toFixed(0)}%)</label>
                        <input
                            className="input-field"
                            type="range"
                            min="0.01" max="0.5" step="0.01"
                            value={contamination}
                            onChange={(e) => setContamination(e.target.value)}
                            style={{ padding: '0.5rem 0' }}
                        />
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                            Expected proportion of anomalies in data (1–50%)
                        </span>
                    </div>
                    <button
                        className="btn btn-primary"
                        type="submit"
                        disabled={loading || !datasetId.trim()}
                        style={{ flexShrink: 0, padding: '0.8rem 2rem' }}
                    >
                        {loading ? (
                            <><div className="spinner" style={{ width: 16, height: 16 }} /> Detecting...</>
                        ) : (
                            '🔍 Run Detection'
                        )}
                    </button>
                </form>
            </div>

            {/* ── Algorithm info ── */}
            <div style={{
                background: 'rgba(0,209,255,0.04)',
                border: '1px solid rgba(0,209,255,0.15)',
                borderRadius: 'var(--border-radius-lg)',
                padding: 'var(--space-md) var(--space-lg)',
                marginBottom: 'var(--space-xl)',
                display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
            }}>
                <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>🧠</span>
                <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#00d1ff', marginBottom: '0.3rem' }}>
                        ML Concept: Isolation Forest
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
                        Randomly partitions data using decision trees. Anomalous points are isolated in fewer splits
                        (shorter path length) than normal points — making them easy to detect without labelled data.
                    </div>
                </div>
            </div>

            {/* ── Error ── */}
            {error && <div className="alert alert-error">{error}</div>}

            {/* ── Results ── */}
            {anomalyData && (
                <div>
                    {/* Summary row */}
                    <div className="grid-4" style={{ marginBottom: 'var(--space-xl)' }}>
                        <div className="card kpi-card">
                            <div className="kpi-icon">🚨</div>
                            <div className="kpi-value" style={{ color: anomalyData.anomaly_count > 0 ? '#e74c3c' : '#2ecc71' }}>
                                {anomalyData.anomaly_count}
                            </div>
                            <div className="kpi-label">Anomalies Found</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">📋</div>
                            <div className="kpi-value">{anomalyData.total_rows_checked}</div>
                            <div className="kpi-label">Rows Checked</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">📊</div>
                            <div className="kpi-value">{(anomalyData.contamination_rate * 100).toFixed(1)}%</div>
                            <div className="kpi-label">Anomaly Rate</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">⚙️</div>
                            <div className="kpi-value" style={{ fontSize: '0.85rem' }}>{anomalyData.method}</div>
                            <div className="kpi-label">Method Used</div>
                        </div>
                    </div>

                    <div className="grid-2">
                        {/* Column Stats */}
                        <div className="card">
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c4c0ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                                📐 Column Statistics
                            </div>
                            {Object.entries(anomalyData.column_stats || {}).map(([col, stats]) => (
                                <div key={col} style={{ marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--color-border)' }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>{col}</div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
                                        {['mean', 'std', 'min', 'max'].map(k => (
                                            <div key={k} style={{ textAlign: 'center' }}>
                                                <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k}</div>
                                                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{stats[k]}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Anomalous Rows */}
                        <div className="card">
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#ff6b6b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                                🚨 Anomalous Rows ({anomalyData.anomaly_rows?.length || 0})
                            </div>
                            {anomalyData.anomaly_rows?.length > 0 ? (
                                <div className="data-table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                {Object.keys(anomalyData.anomaly_rows[0] || {}).slice(0, 5).map(col => (
                                                    <th key={col}>{col}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {anomalyData.anomaly_rows.slice(0, 20).map((row, i) => (
                                                <tr key={i} style={{ background: 'rgba(231, 76, 60, 0.05)' }}>
                                                    {Object.values(row).slice(0, 5).map((val, j) => (
                                                        <td key={j}>{String(val ?? '—')}</td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
                                    ✅ No anomalies detected with current settings
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Anomalies
