/**
 * ============================================================
 * Forecast Page — Time-Series Forecasting with Prophet
 * ============================================================
 * Calls POST /api/queries/forecast with dataset_id.
 * Renders a combined historical + forecast line chart,
 * trend badge, and confidence interval info.
 * ============================================================
 */

import React, { useState, useCallback, useMemo } from 'react'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import axiosClient from '../api/axiosClient'

const tooltipStyle = {
    background: '#1a1a2e',
    border: '1px solid #2a2a40',
    borderRadius: 8,
    color: '#e0e0e0',
    fontSize: '0.8rem',
}

const TREND_BADGE = {
    up:   { label: '↑ Upward Trend',   bg: 'rgba(46,204,113,0.12)',  border: 'rgba(46,204,113,0.35)',  color: '#2ecc71' },
    down: { label: '↓ Downward Trend', bg: 'rgba(231,76,60,0.12)',   border: 'rgba(231,76,60,0.35)',   color: '#e74c3c' },
    flat: { label: '→ Flat Trend',     bg: 'rgba(241,196,15,0.12)',  border: 'rgba(241,196,15,0.35)',  color: '#f1c40f' },
}

const FREQ_OPTIONS = [
    { value: 'D', label: 'Daily' },
    { value: 'W', label: 'Weekly' },
    { value: 'M', label: 'Monthly' },
]

function Forecast() {
    const [datasetId, setDatasetId] = useState('')
    const [dateCol, setDateCol]     = useState('')
    const [valueCol, setValueCol]   = useState('')
    const [periods, setPeriods]     = useState(30)
    const [freq, setFreq]           = useState('D')
    const [loading, setLoading]     = useState(false)
    const [result, setResult]       = useState(null)
    const [error, setError]         = useState('')

    const handleRun = useCallback(async (e) => {
        e?.preventDefault()
        if (!datasetId.trim()) return
        setLoading(true); setError(''); setResult(null)
        try {
            const res = await axiosClient.post('/queries/forecast', {
                dataset_id:  datasetId.trim(),
                date_col:    dateCol.trim()  || undefined,
                value_col:   valueCol.trim() || undefined,
                periods:     parseInt(periods),
                freq,
            })
            setResult(res.data)
        } catch (err) {
            setError(err.response?.data?.detail || 'Forecasting failed. Please check the dataset ID and column names.')
        } finally {
            setLoading(false)
        }
    }, [datasetId, dateCol, valueCol, periods, freq])

    // Merge historical + forecast for combined chart
    const chartData = useMemo(() => {
        const fr = result?.forecast_result
        if (!fr) return []
        const historical = (fr.historical || []).map(p => ({
            ds: p.ds,
            actual: p.y,
            forecast: null,
        }))
        const future = (fr.forecast || []).map(p => ({
            ds: p.ds,
            actual: null,
            forecast: p.yhat,
            lower: p.yhat_lower,
            upper: p.yhat_upper,
        }))
        return [...historical, ...future]
    }, [result])

    const fr = result?.forecast_result
    const trendInfo = fr ? (TREND_BADGE[fr.trend] || TREND_BADGE.flat) : null

    return (
        <div style={{ position: 'relative' }}>
            <div className="bg-orb bg-orb-1" />
            <div className="bg-orb bg-orb-2" />

            <h1 className="page-title">Time-Series Forecast</h1>
            <p className="page-subtitle">
                Predict future values using Facebook Prophet — AI-powered trend, seasonality, and holiday decomposition
            </p>

            {/* ── Config Card ── */}
            <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c4c0ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                    📅 Configure Forecast
                </div>
                <form onSubmit={handleRun}>
                    <div className="grid-2" style={{ marginBottom: 'var(--space-md)' }}>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label>Dataset ID *</label>
                            <input
                                className="input-field"
                                type="text"
                                value={datasetId}
                                onChange={(e) => setDatasetId(e.target.value)}
                                placeholder="e.g. 1 (from Upload page)"
                                required
                            />
                        </div>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label>Frequency</label>
                            <select className="input-field" value={freq} onChange={(e) => setFreq(e.target.value)}>
                                {FREQ_OPTIONS.map(f => (
                                    <option key={f.value} value={f.value}>{f.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="grid-2" style={{ marginBottom: 'var(--space-md)' }}>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label>Date Column (optional — auto-detect)</label>
                            <input
                                className="input-field"
                                type="text"
                                value={dateCol}
                                onChange={(e) => setDateCol(e.target.value)}
                                placeholder="e.g. date, order_date"
                            />
                        </div>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label>Value Column (optional — auto-detect)</label>
                            <input
                                className="input-field"
                                type="text"
                                value={valueCol}
                                onChange={(e) => setValueCol(e.target.value)}
                                placeholder="e.g. sales, revenue"
                            />
                        </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 'var(--space-lg)', flexWrap: 'wrap' }}>
                        <div className="input-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
                            <label>Forecast Periods ({periods})</label>
                            <input
                                className="input-field"
                                type="range"
                                min={7} max={365} step={1}
                                value={periods}
                                onChange={(e) => setPeriods(e.target.value)}
                                style={{ padding: '0.5rem 0' }}
                            />
                        </div>
                        <button
                            className="btn btn-primary"
                            type="submit"
                            disabled={loading || !datasetId.trim()}
                            style={{ flexShrink: 0, padding: '0.8rem 2rem', marginBottom: 0 }}
                        >
                            {loading ? (
                                <><div className="spinner" style={{ width: 16, height: 16 }} /> Forecasting...</>
                            ) : (
                                '📈 Run Forecast'
                            )}
                        </button>
                    </div>
                </form>
            </div>

            {/* ── Algorithm info ── */}
            <div style={{
                background: 'rgba(46,204,113,0.04)',
                border: '1px solid rgba(46,204,113,0.2)',
                borderRadius: 'var(--border-radius-lg)',
                padding: 'var(--space-md) var(--space-lg)',
                marginBottom: 'var(--space-xl)',
                display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
            }}>
                <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>🧠</span>
                <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#2ecc71', marginBottom: '0.3rem' }}>
                        ML Concept: Facebook Prophet (Additive Regression)
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
                        Prophet decomposes a time series into <strong>trend + seasonality + holidays + error</strong>.
                        It uses curve fitting (Stan MCMC) to model non-linear growth and handles missing data and outliers robustly.
                        Falls back to linear trend regression if Prophet is unavailable.
                    </div>
                </div>
            </div>

            {/* ── Error ── */}
            {error && <div className="alert alert-error">{error}</div>}

            {/* ── Results ── */}
            {fr && (
                <div>
                    {/* KPIs */}
                    <div className="grid-4" style={{ marginBottom: 'var(--space-xl)' }}>
                        <div className="card kpi-card">
                            <div className="kpi-icon">📊</div>
                            <div className="kpi-value">{fr.historical?.length || 0}</div>
                            <div className="kpi-label">Historical Points</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">🔮</div>
                            <div className="kpi-value">{fr.forecast?.length || 0}</div>
                            <div className="kpi-label">Forecast Points</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">📅</div>
                            <div className="kpi-value" style={{ fontSize: '0.9rem' }}>{fr.frequency}</div>
                            <div className="kpi-label">Frequency</div>
                        </div>
                        <div className="card kpi-card">
                            <div className="kpi-icon">⚙️</div>
                            <div className="kpi-value" style={{ fontSize: '0.8rem' }}>{fr.method}</div>
                            <div className="kpi-label">Method</div>
                        </div>
                    </div>

                    {/* Trend badge + date range */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: 'var(--space-lg)', flexWrap: 'wrap' }}>
                        {trendInfo && (
                            <span style={{
                                padding: '0.4rem 1rem',
                                background: trendInfo.bg, border: `1px solid ${trendInfo.border}`,
                                borderRadius: '999px', fontSize: '0.85rem', fontWeight: 700,
                                color: trendInfo.color,
                            }}>
                                {trendInfo.label}
                            </span>
                        )}
                        {result.date_col && (
                            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                Date: <strong style={{ color: 'var(--color-text-secondary)' }}>{result.date_col}</strong>
                                &nbsp;·&nbsp;Value: <strong style={{ color: 'var(--color-text-secondary)' }}>{result.value_col}</strong>
                            </span>
                        )}
                    </div>

                    {/* Chart */}
                    <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#a6e6ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                            📈 Historical + Forecast Chart
                        </div>
                        {chartData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={420}>
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                                    <XAxis
                                        dataKey="ds"
                                        tick={{ fill: '#a0a0b0', fontSize: 11 }}
                                        tickFormatter={(v) => v?.slice(0, 10)}
                                        interval="preserveStartEnd"
                                    />
                                    <YAxis tick={{ fill: '#a0a0b0', fontSize: 11 }} />
                                    <Tooltip
                                        contentStyle={tooltipStyle}
                                        formatter={(val, name) => [val?.toFixed ? val.toFixed(2) : val, name]}
                                        labelFormatter={(l) => `Date: ${l}`}
                                    />
                                    <Legend />
                                    {/* Divider at end of historical data */}
                                    {fr.historical?.length > 0 && (
                                        <ReferenceLine
                                            x={fr.historical[fr.historical.length - 1]?.ds}
                                            stroke="rgba(255,255,255,0.2)"
                                            strokeDasharray="4 4"
                                            label={{ value: 'Forecast →', fill: '#918fa1', fontSize: 11 }}
                                        />
                                    )}
                                    <Line
                                        type="monotone"
                                        dataKey="actual"
                                        name="Actual"
                                        stroke="#6c63ff"
                                        strokeWidth={2}
                                        dot={false}
                                        connectNulls={false}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="forecast"
                                        name="Forecast"
                                        stroke="#00d1ff"
                                        strokeWidth={2}
                                        strokeDasharray="5 3"
                                        dot={false}
                                        connectNulls={false}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '2rem' }}>
                                No chart data available.
                            </p>
                        )}
                    </div>

                    {/* Forecast table */}
                    {fr.forecast?.length > 0 && (
                        <div className="card">
                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#00d1ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                                🔮 Forecast Values (First 20 Periods)
                            </div>
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Forecast (yhat)</th>
                                            <th>Lower Bound</th>
                                            <th>Upper Bound</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {fr.forecast.slice(0, 20).map((row, i) => (
                                            <tr key={i}>
                                                <td>{row.ds}</td>
                                                <td style={{ color: '#00d1ff', fontWeight: 600 }}>{row.yhat}</td>
                                                <td style={{ color: 'var(--color-text-muted)' }}>{row.yhat_lower}</td>
                                                <td style={{ color: 'var(--color-text-muted)' }}>{row.yhat_upper}</td>
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

export default Forecast
