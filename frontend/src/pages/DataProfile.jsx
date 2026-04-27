/**
 * ============================================================
 * DataProfile Page — Rich dataset profiling & visualization
 * ============================================================
 * Shows KPI cards, missing value chart, data type distribution,
 * top categorical values, numeric stats, and correlation matrix.
 * ============================================================
 */

import React, { useState, useCallback } from 'react'
import { getFullProfile } from '../api/datasets'
import {
    BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

const COLORS = ['#6c63ff', '#a855f7', '#3498db', '#2ecc71', '#f1c40f', '#e74c3c', '#1abc9c', '#e67e22']
const tooltipStyle = { background: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: 8, color: '#e0e0e0' }

function DataProfile() {
    const [datasetId, setDatasetId] = useState('')
    const [loading, setLoading] = useState(false)
    const [profile, setProfile] = useState(null)
    const [error, setError] = useState('')

    const handleFetch = useCallback(async () => {
        if (!datasetId.trim()) return
        setLoading(true)
        setError('')
        setProfile(null)
        try {
            const data = await getFullProfile(datasetId)
            setProfile(data)
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load profile')
        } finally {
            setLoading(false)
        }
    }, [datasetId])

    return (
        <div>
            <h1 className="page-title">Data Profile</h1>
            <p className="page-subtitle">Explore your dataset's structure, quality, and statistics</p>

            {/* Dataset ID Input */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: 'var(--space-lg)' }}>
                <input
                    className="input-field"
                    type="text"
                    value={datasetId}
                    onChange={(e) => setDatasetId(e.target.value)}
                    placeholder="Enter dataset ID (e.g., 1)"
                    style={{ flex: 1, maxWidth: '300px' }}
                />
                <button className="btn btn-primary" onClick={handleFetch} disabled={loading || !datasetId.trim()}>
                    {loading ? '⏳ Loading...' : '📊 Load Profile'}
                </button>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            {profile && (
                <div style={{ marginTop: 'var(--space-lg)' }}>
                    {/* ── KPI Cards ──────────────────────────── */}
                    <div className="grid-4">
                        <div className="card kpi-card">
                            <div className="kpi-value">{profile.overview.rows.toLocaleString()}</div>
                            <div className="kpi-label">Total Rows</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-value">{profile.overview.columns}</div>
                            <div className="kpi-label">Total Columns</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-value">
                                {profile.missing_values.reduce((s, m) => s + m.missing_count, 0).toLocaleString()}
                            </div>
                            <div className="kpi-label">Missing Values</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-value">{profile.overview.duplicate_rows}</div>
                            <div className="kpi-label">Duplicate Rows</div>
                        </div>
                    </div>

                    <div className="grid-2" style={{ marginTop: 'var(--space-xl)', gap: 'var(--space-lg)' }}>
                        {/* ── Missing Values Bar Chart ────────── */}
                        <div className="card">
                            <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                                📉 Missing Values by Column
                            </h3>
                            {profile.missing_values.some(m => m.missing_count > 0) ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={profile.missing_values.filter(m => m.missing_count > 0)}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                                        <XAxis dataKey="column" tick={{ fill: '#a0a0b0', fontSize: 11 }} angle={-30} textAnchor="end" height={80} />
                                        <YAxis tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                                        <Tooltip contentStyle={tooltipStyle} />
                                        <Bar dataKey="missing_count" fill="#e74c3c" radius={[4, 4, 0, 0]} name="Missing Count" />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <p style={{ color: 'var(--color-success)', textAlign: 'center', padding: '2rem' }}>
                                    ✅ No missing values detected!
                                </p>
                            )}
                        </div>

                        {/* ── Data Type Distribution Pie ──────── */}
                        <div className="card">
                            <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                                🔤 Data Type Distribution
                            </h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={Object.entries(profile.data_types.distribution).map(([name, value]) => ({ name, value }))}
                                        dataKey="value"
                                        nameKey="name"
                                        cx="50%"
                                        cy="50%"
                                        outerRadius={100}
                                        label={({ name, value }) => `${name}: ${value}`}
                                    >
                                        {Object.entries(profile.data_types.distribution).map((_, i) => (
                                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={tooltipStyle} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* ── Column Types Table ──────────────────── */}
                    <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
                        <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                            📋 Column Details
                        </h3>
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Column</th>
                                        <th>Data Type</th>
                                        <th>Semantic Type</th>
                                        <th>Missing</th>
                                        <th>Missing %</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {profile.data_types.columns.map((col, i) => {
                                        const missing = profile.missing_values.find(m => m.column === col.column)
                                        return (
                                            <tr key={i}>
                                                <td><strong>{col.column}</strong></td>
                                                <td>{col.dtype}</td>
                                                <td>
                                                    <span style={{
                                                        padding: '2px 8px',
                                                        borderRadius: '12px',
                                                        fontSize: '0.75rem',
                                                        background: col.semantic_type === 'numeric' ? 'rgba(108,99,255,0.2)' :
                                                            col.semantic_type === 'categorical' ? 'rgba(46,204,113,0.2)' :
                                                            col.semantic_type === 'datetime' ? 'rgba(52,152,219,0.2)' : 'rgba(241,196,15,0.2)',
                                                        color: col.semantic_type === 'numeric' ? '#6c63ff' :
                                                            col.semantic_type === 'categorical' ? '#2ecc71' :
                                                            col.semantic_type === 'datetime' ? '#3498db' : '#f1c40f',
                                                    }}>
                                                        {col.semantic_type}
                                                    </span>
                                                </td>
                                                <td>{missing?.missing_count || 0}</td>
                                                <td style={{ color: (missing?.missing_percent || 0) > 0 ? 'var(--color-warning)' : 'var(--color-success)' }}>
                                                    {missing?.missing_percent || 0}%
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* ── Top Categorical Values ──────────────── */}
                    {profile.categorical_summary.length > 0 && (
                        <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
                            <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                                🏷️ Top Values — Categorical Columns
                            </h3>
                            <div className="grid-2" style={{ gap: 'var(--space-md)' }}>
                                {profile.categorical_summary.map((cat) => (
                                    <div key={cat.column} style={{
                                        background: 'var(--color-bg-secondary)',
                                        borderRadius: 'var(--border-radius-md)',
                                        padding: 'var(--space-md)',
                                    }}>
                                        <h4 style={{ marginBottom: 'var(--space-sm)', fontSize: '0.9rem' }}>
                                            {cat.column} <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                                                ({cat.unique_count} unique)
                                            </span>
                                        </h4>
                                        {cat.top_values.map((tv, i) => (
                                            <div key={i} style={{
                                                display: 'flex', justifyContent: 'space-between',
                                                padding: '4px 0', borderBottom: '1px solid var(--color-border)',
                                                fontSize: '0.85rem',
                                            }}>
                                                <span>{tv.value}</span>
                                                <span style={{ color: 'var(--color-accent)' }}>{tv.count}</span>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ── Numeric Stats Table ────────────────── */}
                    {profile.numeric_summary.length > 0 && (
                        <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
                            <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                                📊 Numeric Column Statistics
                            </h3>
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Column</th>
                                            <th>Mean</th>
                                            <th>Std</th>
                                            <th>Min</th>
                                            <th>Q25</th>
                                            <th>Median</th>
                                            <th>Q75</th>
                                            <th>Max</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {profile.numeric_summary.map((ns) => (
                                            <tr key={ns.column}>
                                                <td><strong>{ns.column}</strong></td>
                                                <td>{ns.mean}</td>
                                                <td>{ns.std}</td>
                                                <td>{ns.min}</td>
                                                <td>{ns.q25}</td>
                                                <td>{ns.median}</td>
                                                <td>{ns.q75}</td>
                                                <td>{ns.max}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* ── Correlation Matrix ──────────────────── */}
                    {profile.correlation_matrix.length > 0 && (
                        <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
                            <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                                🔗 Correlation Matrix
                            </h3>
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Column 1</th>
                                            <th>Column 2</th>
                                            <th>Correlation</th>
                                            <th>Strength</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {profile.correlation_matrix
                                            .filter(c => c.col1 !== c.col2)
                                            .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
                                            .map((c, i) => {
                                                const abs = Math.abs(c.value)
                                                const strength = abs >= 0.7 ? 'Strong' : abs >= 0.4 ? 'Moderate' : 'Weak'
                                                const color = abs >= 0.7 ? '#e74c3c' : abs >= 0.4 ? '#f1c40f' : '#2ecc71'
                                                return (
                                                    <tr key={i}>
                                                        <td>{c.col1}</td>
                                                        <td>{c.col2}</td>
                                                        <td style={{ color }}>{c.value}</td>
                                                        <td>
                                                            <span style={{
                                                                padding: '2px 8px', borderRadius: '12px',
                                                                fontSize: '0.75rem', background: `${color}22`, color,
                                                            }}>
                                                                {strength}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                )
                                            })
                                        }
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

export default DataProfile
