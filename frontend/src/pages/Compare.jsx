/**
 * ============================================================
 * Compare — Side-by-side dataset comparison page
 * ============================================================
 * Features:
 *   - Two dataset pickers
 *   - Summary stat cards (rows added/removed)
 *   - Color-coded diff table
 *   - Statistical delta cards
 * ============================================================
 */

import React, { useState, useCallback, useEffect } from 'react'
import { getMyDatasets } from '../api/datasets'
import { compareDatasets } from '../api/compare'

function Compare() {
    const [datasets, setDatasets] = useState([])
    const [dsId1, setDsId1] = useState('')
    const [dsId2, setDsId2] = useState('')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')

    useEffect(() => {
        getMyDatasets().then(setDatasets).catch(() => {})
    }, [])

    const handleCompare = useCallback(async () => {
        if (!dsId1 || !dsId2) return
        if (dsId1 === dsId2) { setError('Please select two different datasets.'); return }
        setLoading(true)
        setError('')
        setResult(null)
        try {
            const data = await compareDatasets(dsId1, dsId2)
            if (data.success) setResult(data)
            else setError('Comparison failed')
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to compare datasets')
        } finally {
            setLoading(false)
        }
    }, [dsId1, dsId2])

    return (
        <div>
            <h1 className="page-title">Compare Datasets</h1>
            <p className="page-subtitle">Upload two versions of a dataset and see what changed</p>

            {/* Dataset Pickers */}
            <div className="grid-2" style={{ marginBottom: 'var(--space-lg)' }}>
                <div className="input-group">
                    <label>📁 Dataset A (Before)</label>
                    <select className="input-field" value={dsId1} onChange={e => setDsId1(e.target.value)}>
                        <option value="">— Select baseline dataset —</option>
                        {datasets.filter(d => d.in_memory).map(d => (
                            <option key={d.dataset_id} value={d.dataset_id}>
                                #{d.dataset_id} · {d.filename} ({d.row_count?.toLocaleString()} rows)
                            </option>
                        ))}
                    </select>
                </div>
                <div className="input-group">
                    <label>📁 Dataset B (After)</label>
                    <select className="input-field" value={dsId2} onChange={e => setDsId2(e.target.value)}>
                        <option value="">— Select comparison dataset —</option>
                        {datasets.filter(d => d.in_memory).map(d => (
                            <option key={d.dataset_id} value={d.dataset_id}>
                                #{d.dataset_id} · {d.filename} ({d.row_count?.toLocaleString()} rows)
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <button
                className="btn btn-primary"
                onClick={handleCompare}
                disabled={loading || !dsId1 || !dsId2}
                style={{ marginBottom: 'var(--space-lg)' }}
            >
                {loading ? '⏳ Comparing...' : '🔍 Compare Datasets'}
            </button>

            {error && <div className="alert alert-error">{error}</div>}

            {/* Results */}
            {result && (
                <div style={{ animation: 'fadeIn 0.4s ease' }}>
                    {/* Summary KPIs */}
                    <div className="grid-4" style={{ marginBottom: 'var(--space-lg)' }}>
                        {[
                            { value: result.summary.rows_added, label: 'Rows Added', color: '#10B981', icon: '➕' },
                            { value: result.summary.rows_removed, label: 'Rows Removed', color: '#EF4444', icon: '➖' },
                            { value: result.summary.columns_added, label: 'Cols Added', color: '#3B82F6', icon: '📊' },
                            { value: result.summary.stat_changes, label: 'Stat Changes', color: '#F59E0B', icon: '📈' },
                        ].map((kpi, i) => (
                            <div key={i} className="card kpi-card">
                                <div style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>{kpi.icon}</div>
                                <div className="kpi-value" style={{ color: kpi.color }}>{kpi.value}</div>
                                <div className="kpi-label">{kpi.label}</div>
                            </div>
                        ))}
                    </div>

                    {/* Dataset Info */}
                    <div className="grid-2" style={{ marginBottom: 'var(--space-lg)' }}>
                        <div className="card" style={{ borderLeft: '3px solid var(--color-accent)' }}>
                            <h4 style={{ color: 'var(--color-accent)', fontSize: '0.85rem' }}>Dataset A: {result.dataset_1.filename}</h4>
                            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.82rem' }}>{result.dataset_1.rows.toLocaleString()} rows</p>
                        </div>
                        <div className="card" style={{ borderLeft: '3px solid var(--color-tertiary)' }}>
                            <h4 style={{ color: 'var(--color-tertiary)', fontSize: '0.85rem' }}>Dataset B: {result.dataset_2.filename}</h4>
                            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.82rem' }}>{result.dataset_2.rows.toLocaleString()} rows</p>
                        </div>
                    </div>

                    {/* Statistical Deltas */}
                    {result.stat_deltas?.length > 0 && (
                        <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                            <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                                📊 Statistical Changes
                            </h3>
                            <div style={{ overflowX: 'auto' }}>
                                <table className="diff-table">
                                    <thead>
                                        <tr>
                                            <th>Column</th>
                                            <th>Before (Mean)</th>
                                            <th>After (Mean)</th>
                                            <th>Change</th>
                                            <th>% Change</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.stat_deltas.map((d, i) => (
                                            <tr key={i}>
                                                <td style={{ fontWeight: 600 }}>{d.column}</td>
                                                <td>{d.before_mean.toLocaleString()}</td>
                                                <td>{d.after_mean.toLocaleString()}</td>
                                                <td style={{ color: d.delta > 0 ? '#10B981' : d.delta < 0 ? '#EF4444' : 'var(--color-text-muted)' }}>
                                                    {d.delta > 0 ? '▲' : d.delta < 0 ? '▼' : '—'} {Math.abs(d.delta).toLocaleString()}
                                                </td>
                                                <td>
                                                    <span className={`badge ${d.delta_pct > 0 ? 'badge-success' : d.delta_pct < 0 ? 'badge-danger' : ''}`}
                                                        style={{
                                                            background: d.delta_pct > 0 ? 'rgba(16,185,129,0.15)' : d.delta_pct < 0 ? 'rgba(239,68,68,0.15)' : 'var(--color-bg-secondary)',
                                                            color: d.delta_pct > 0 ? '#10B981' : d.delta_pct < 0 ? '#EF4444' : 'var(--color-text-muted)',
                                                            padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem',
                                                        }}>
                                                        {d.delta_pct > 0 ? '+' : ''}{d.delta_pct}%
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Added Rows Sample */}
                    {result.sample_added?.length > 0 && (
                        <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                            <h3 style={{ color: '#10B981', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                                ➕ Sample Added Rows ({result.summary.rows_added} total)
                            </h3>
                            <div style={{ overflowX: 'auto', maxHeight: '300px' }}>
                                <table className="diff-table">
                                    <thead>
                                        <tr>{Object.keys(result.sample_added[0]).map(k => <th key={k}>{k}</th>)}</tr>
                                    </thead>
                                    <tbody>
                                        {result.sample_added.slice(0, 10).map((row, i) => (
                                            <tr key={i} style={{ background: 'rgba(16,185,129,0.05)' }}>
                                                {Object.values(row).map((v, j) => <td key={j}>{String(v)}</td>)}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Removed Rows Sample */}
                    {result.sample_removed?.length > 0 && (
                        <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                            <h3 style={{ color: '#EF4444', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                                ➖ Sample Removed Rows ({result.summary.rows_removed} total)
                            </h3>
                            <div style={{ overflowX: 'auto', maxHeight: '300px' }}>
                                <table className="diff-table">
                                    <thead>
                                        <tr>{Object.keys(result.sample_removed[0]).map(k => <th key={k}>{k}</th>)}</tr>
                                    </thead>
                                    <tbody>
                                        {result.sample_removed.slice(0, 10).map((row, i) => (
                                            <tr key={i} style={{ background: 'rgba(239,68,68,0.05)' }}>
                                                {Object.values(row).map((v, j) => <td key={j}>{String(v)}</td>)}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Column Changes */}
                    {(result.columns_added?.length > 0 || result.columns_removed?.length > 0) && (
                        <div className="card">
                            <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                                🔄 Column Changes
                            </h3>
                            {result.columns_added.length > 0 && (
                                <div style={{ marginBottom: '0.5rem' }}>
                                    <span style={{ color: '#10B981', fontSize: '0.85rem' }}>Added: </span>
                                    {result.columns_added.map(c => (
                                        <span key={c} className="badge" style={{ background: 'rgba(16,185,129,0.15)', color: '#10B981', margin: '0 4px', padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem' }}>{c}</span>
                                    ))}
                                </div>
                            )}
                            {result.columns_removed.length > 0 && (
                                <div>
                                    <span style={{ color: '#EF4444', fontSize: '0.85rem' }}>Removed: </span>
                                    {result.columns_removed.map(c => (
                                        <span key={c} className="badge" style={{ background: 'rgba(239,68,68,0.15)', color: '#EF4444', margin: '0 4px', padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem' }}>{c}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default Compare
