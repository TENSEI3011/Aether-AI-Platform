/**
 * ============================================================
 * Forecast Page — Predictive Analytics UI
 * ============================================================
 * Connects to the existing /api/queries/forecast backend endpoint
 * (forecaster.py — linear regression + moving average).
 *
 * Features:
 *   - Dataset selector (from DB — same as Query page)
 *   - Schema-aware column pickers (auto-fills X/Y from dataset schema)
 *   - Method toggle: Linear Regression / Moving Average
 *   - Period slider: 1–20 steps ahead
 *   - Recharts ComposedChart: historical series + forecast series
 *   - Trend badge, confidence score, textual summary
 * ============================================================
 */

import React, { useState, useEffect, useCallback } from 'react'
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { getMyDatasets, getSchema } from '../api/datasets'
import { forecastQuery } from '../api/queries'

const TREND_META = {
    rising:  { icon: '📈', color: '#4ade80', label: 'Rising Trend' },
    falling: { icon: '📉', color: '#f87171', label: 'Falling Trend' },
    stable:  { icon: '➡️', color: '#facc15', label: 'Stable Trend' },
}

function Forecast() {
    // ── Dataset / schema state ────────────────────────────
    const [myDatasets,   setMyDatasets]   = useState([])
    const [datasetId,    setDatasetId]    = useState('')
    const [columns,      setColumns]      = useState({ numeric: [], categorical: [], datetime: [] })
    const [schemaLoading, setSchemaLoading] = useState(false)

    // ── Config ────────────────────────────────────────────
    const [xColumn,  setXColumn]  = useState('')
    const [yColumn,  setYColumn]  = useState('')
    const [periods,  setPeriods]  = useState(5)
    const [method,   setMethod]   = useState('linear')

    // ── Result ─────────────────────────────────────────────
    const [loading,  setLoading]  = useState(false)
    const [result,   setResult]   = useState(null)
    const [error,    setError]    = useState('')

    // ── Load dataset list ─────────────────────────────────
    useEffect(() => {
        getMyDatasets().then(setMyDatasets).catch(() => {})
    }, [])

    // ── Load schema when dataset changes ─────────────────
    useEffect(() => {
        if (!datasetId) { setColumns({ numeric: [], categorical: [], datetime: [] }); return }
        setSchemaLoading(true)
        setXColumn('')
        setYColumn('')
        setResult(null)
        setError('')
        import('../api/datasets').then(({ getSchema }) => {
            getSchema(datasetId)
                .then((schema) => {
                    const numeric     = (schema.columns || []).filter(c => c.semantic_type === 'numeric').map(c => c.name)
                    const categorical = (schema.columns || []).filter(c => c.semantic_type === 'categorical').map(c => c.name)
                    const datetime    = (schema.columns || []).filter(c => c.semantic_type === 'datetime').map(c => c.name)
                    setColumns({ numeric, categorical, datetime })
                    // Auto-select sensible defaults
                    const allX = [...datetime, ...categorical, ...numeric]
                    if (allX.length > 0)   setXColumn(allX[0])
                    if (numeric.length > 0) setYColumn(numeric[0])
                })
                .catch(() => setError('Failed to load dataset schema'))
                .finally(() => setSchemaLoading(false))
        })
    }, [datasetId])

    // ── Run forecast ──────────────────────────────────────
    const handleForecast = useCallback(async () => {
        if (!datasetId || !xColumn || !yColumn) return
        setLoading(true)
        setResult(null)
        setError('')
        try {
            const data = await forecastQuery(datasetId, xColumn, yColumn, periods, method)
            if (data.success === false) {
                setError(data.error || 'Forecast failed')
            } else {
                setResult(data)
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Forecast request failed')
        } finally {
            setLoading(false)
        }
    }, [datasetId, xColumn, yColumn, periods, method])

    // ── Build unified chart data ──────────────────────────
    const chartData = (() => {
        if (!result) return []
        const hist = (result.historical || []).map(p => ({ x: p.x, historical: p.y, forecast: null }))
        const fcst = (result.forecast   || []).map(p => ({ x: p.x, historical: null, forecast: p.y }))
        // Connect the last historical point to the first forecast point
        if (hist.length > 0 && fcst.length > 0) {
            fcst[0] = { ...fcst[0], historical: hist[hist.length - 1].historical }
        }
        return [...hist, ...fcst]
    })()

    const trendMeta = result ? (TREND_META[result.trend] || TREND_META.stable) : null
    const xAllCols = [...columns.datetime, ...columns.categorical, ...columns.numeric]

    return (
        <div>
            <h1 className="page-title">📈 Predictive Forecast</h1>
            <p className="page-subtitle">
                Project future values using Linear Regression or Moving Average
            </p>

            {/* ── Config Panel ─────────────────────────────── */}
            <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                    ⚙️ Forecast Configuration
                </h3>

                <div className="grid-2" style={{ gap: 'var(--space-md)' }}>
                    {/* Dataset */}
                    <div className="input-group">
                        <label>Dataset</label>
                        {myDatasets.length > 0 ? (
                            <select
                                id="forecast-dataset"
                                className="input-field"
                                value={datasetId}
                                onChange={e => setDatasetId(e.target.value)}
                            >
                                <option value="">— Select a dataset —</option>
                                {myDatasets.map(d => (
                                    <option key={d.dataset_id} value={d.dataset_id} disabled={!d.in_memory}>
                                        #{d.dataset_id} · {d.filename}
                                        {d.row_count ? ` (${d.row_count.toLocaleString()} rows)` : ''}
                                        {!d.in_memory ? ' [re-upload needed]' : ''}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <input
                                id="forecast-dataset-manual"
                                className="input-field"
                                placeholder="Enter dataset ID (e.g. 1)"
                                value={datasetId}
                                onChange={e => setDatasetId(e.target.value)}
                            />
                        )}
                        {schemaLoading && <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>Loading schema…</span>}
                    </div>

                    {/* Method */}
                    <div className="input-group">
                        <label>Forecast Method</label>
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: 4 }}>
                            {[
                                { value: 'linear',         label: '📐 Linear Regression' },
                                { value: 'moving_average', label: '🌊 Moving Average' },
                            ].map(opt => (
                                <button
                                    key={opt.value}
                                    onClick={() => setMethod(opt.value)}
                                    style={{
                                        flex: 1,
                                        padding: '0.55rem 0.5rem',
                                        borderRadius: 8,
                                        border: `2px solid ${method === opt.value ? 'var(--color-accent)' : 'var(--color-border)'}`,
                                        background: method === opt.value ? 'rgba(99,102,241,0.15)' : 'var(--color-bg-secondary)',
                                        color: method === opt.value ? 'var(--color-accent)' : 'var(--color-text-muted)',
                                        cursor: 'pointer',
                                        fontSize: '0.82rem',
                                        fontWeight: method === opt.value ? 700 : 400,
                                        transition: 'all 0.2s',
                                    }}
                                >
                                    {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* X Column */}
                    <div className="input-group">
                        <label>X-Axis Column (Time / Category)</label>
                        {xAllCols.length > 0 ? (
                            <select
                                id="forecast-x-col"
                                className="input-field"
                                value={xColumn}
                                onChange={e => setXColumn(e.target.value)}
                            >
                                <option value="">— Select column —</option>
                                {columns.datetime.map(c     => <option key={c} value={c}>📅 {c} (date)</option>)}
                                {columns.categorical.map(c  => <option key={c} value={c}>🏷️ {c} (text)</option>)}
                                {columns.numeric.map(c      => <option key={c} value={c}>🔢 {c} (numeric)</option>)}
                            </select>
                        ) : (
                            <input
                                id="forecast-x-manual"
                                className="input-field"
                                placeholder="e.g. year, month, date"
                                value={xColumn}
                                onChange={e => setXColumn(e.target.value)}
                            />
                        )}
                    </div>

                    {/* Y Column */}
                    <div className="input-group">
                        <label>Y-Axis Column (Value to Forecast)</label>
                        {columns.numeric.length > 0 ? (
                            <select
                                id="forecast-y-col"
                                className="input-field"
                                value={yColumn}
                                onChange={e => setYColumn(e.target.value)}
                            >
                                <option value="">— Select numeric column —</option>
                                {columns.numeric.map(c => <option key={c} value={c}>{c}</option>)}
                            </select>
                        ) : (
                            <input
                                id="forecast-y-manual"
                                className="input-field"
                                placeholder="e.g. sales, temperature, revenue"
                                value={yColumn}
                                onChange={e => setYColumn(e.target.value)}
                            />
                        )}
                    </div>
                </div>

                {/* Periods slider */}
                <div style={{ marginTop: 'var(--space-md)' }}>
                    <label style={{
                        fontSize: '0.85rem',
                        color: 'var(--color-text-secondary)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginBottom: 6,
                    }}>
                        <span>Forecast Periods Ahead</span>
                        <strong style={{ color: 'var(--color-accent)', fontSize: '1.1rem' }}>{periods}</strong>
                    </label>
                    <input
                        id="forecast-periods"
                        type="range"
                        min="1"
                        max="20"
                        step="1"
                        value={periods}
                        onChange={e => setPeriods(Number(e.target.value))}
                        style={{ width: '100%', accentColor: 'var(--color-accent)' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
                        <span>1 step</span><span>20 steps</span>
                    </div>
                </div>

                {/* Run button */}
                <div style={{ marginTop: 'var(--space-lg)', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <button
                        id="run-forecast"
                        className="btn btn-primary"
                        onClick={handleForecast}
                        disabled={loading || !datasetId || !xColumn || !yColumn}
                        style={{ padding: '0.6rem 2rem', fontSize: '1rem' }}
                    >
                        {loading ? '⏳ Forecasting…' : '🔮 Run Forecast'}
                    </button>
                    {loading && <span style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
                        Running {method === 'linear' ? 'linear regression' : 'moving average'}…
                    </span>}
                </div>
            </div>

            {/* Error */}
            {error && <div className="alert alert-error" style={{ marginBottom: 'var(--space-lg)' }}>{error}</div>}

            {/* ── Results ──────────────────────────────────── */}
            {result && (
                <>
                    {/* KPI strip */}
                    <div className="grid-4" style={{ marginBottom: 'var(--space-lg)' }}>
                        {/* Trend */}
                        <div className="card kpi-card" style={{ borderTop: `3px solid ${trendMeta.color}` }}>
                            <div className="kpi-value" style={{ color: trendMeta.color, fontSize: '2rem' }}>
                                {trendMeta.icon}
                            </div>
                            <div className="kpi-label">{trendMeta.label}</div>
                        </div>

                        {/* Confidence */}
                        <div className="card kpi-card">
                            <div className="kpi-value" style={{ color: 'var(--color-accent)' }}>
                                {Math.round((result.confidence || 0) * 100)}%
                            </div>
                            <div className="kpi-label">
                                {method === 'linear' ? 'R² Confidence' : 'Smoothness Score'}
                            </div>
                        </div>

                        {/* Next predicted */}
                        <div className="card kpi-card">
                            <div className="kpi-value" style={{ fontSize: '1.4rem' }}>
                                {result.forecast?.[0]?.y?.toLocaleString() ?? '—'}
                            </div>
                            <div className="kpi-label">Next Predicted ({yColumn})</div>
                        </div>

                        {/* Final forecast */}
                        <div className="card kpi-card">
                            <div className="kpi-value" style={{ fontSize: '1.4rem' }}>
                                {result.forecast?.[result.forecast.length - 1]?.y?.toLocaleString() ?? '—'}
                            </div>
                            <div className="kpi-label">Value at +{periods} Periods</div>
                        </div>
                    </div>

                    {/* Summary text */}
                    {result.summary && (
                        <div className="card" style={{
                            marginBottom: 'var(--space-lg)',
                            borderLeft: `3px solid ${trendMeta.color}`,
                            padding: '1rem 1.25rem',
                        }}>
                            <p style={{ margin: 0, color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
                                {result.summary}
                            </p>
                        </div>
                    )}

                    {/* Chart */}
                    <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                        <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                            📊 Historical + Forecast Chart
                        </h3>
                        <div style={{ marginBottom: 8, display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.8rem', color: '#60a5fa' }}>
                                ─── Historical ({result.historical?.length || 0} points)
                            </span>
                            <span style={{ fontSize: '0.8rem', color: '#f472b6' }}>
                                ─ ─ Forecast ({result.forecast?.length || 0} points)
                            </span>
                            {method === 'linear' && result.slope !== undefined && (
                                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                    slope: {result.slope > 0 ? '+' : ''}{result.slope}  intercept: {result.intercept}
                                </span>
                            )}
                            {method === 'moving_average' && result.window !== undefined && (
                                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                    window size: {result.window}
                                </span>
                            )}
                        </div>
                        <ResponsiveContainer width="100%" height={360}>
                            <ComposedChart data={chartData} margin={{ top: 8, right: 20, bottom: 20, left: 10 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.07)" />
                                <XAxis
                                    dataKey="x"
                                    tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }}
                                    interval="preserveStartEnd"
                                    angle={-30}
                                    textAnchor="end"
                                    height={50}
                                />
                                <YAxis tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'var(--color-bg-card)',
                                        border: '1px solid var(--color-border)',
                                        borderRadius: 8,
                                        fontSize: '0.82rem',
                                    }}
                                    formatter={(val, name) => [
                                        val !== null ? val?.toLocaleString() : '—',
                                        name === 'historical' ? `Historical (${yColumn})` : `Forecast (${yColumn})`,
                                    ]}
                                />
                                <Legend
                                    formatter={(name) => name === 'historical' ? 'Historical' : 'Forecast'}
                                    wrapperStyle={{ fontSize: '0.82rem', paddingTop: 8 }}
                                />
                                {/* Boundary line between history and forecast */}
                                {result.historical?.length > 0 && (
                                    <ReferenceLine
                                        x={result.historical[result.historical.length - 1]?.x}
                                        stroke="rgba(255,255,255,0.25)"
                                        strokeDasharray="4 4"
                                        label={{ value: 'Forecast starts', fill: 'var(--color-text-muted)', fontSize: 10 }}
                                    />
                                )}
                                <Line
                                    type="monotone"
                                    dataKey="historical"
                                    stroke="#60a5fa"
                                    strokeWidth={2.5}
                                    dot={{ r: 3, fill: '#60a5fa' }}
                                    connectNulls={false}
                                    name="historical"
                                    animationDuration={800}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="forecast"
                                    stroke="#f472b6"
                                    strokeWidth={2.5}
                                    strokeDasharray="6 3"
                                    dot={{ r: 4, fill: '#f472b6', strokeWidth: 2, stroke: '#fff' }}
                                    connectNulls={false}
                                    name="forecast"
                                    animationDuration={800}
                                    animationBegin={400}
                                />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Forecast table */}
                    <div className="card">
                        <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                            🔮 Forecast Values
                        </h3>
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                                        <th style={{ padding: '0.5rem 1rem', textAlign: 'left', color: 'var(--color-text-muted)', fontWeight: 600 }}>Step</th>
                                        <th style={{ padding: '0.5rem 1rem', textAlign: 'left', color: 'var(--color-text-muted)', fontWeight: 600 }}>Period</th>
                                        <th style={{ padding: '0.5rem 1rem', textAlign: 'right', color: 'var(--color-accent)', fontWeight: 700 }}>
                                            Predicted {yColumn}
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(result.forecast || []).map((pt, i) => (
                                        <tr key={i} style={{
                                            borderBottom: '1px solid var(--color-border)',
                                            background: i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
                                        }}>
                                            <td style={{ padding: '0.45rem 1rem', color: 'var(--color-text-muted)' }}>+{i + 1}</td>
                                            <td style={{ padding: '0.45rem 1rem', color: 'var(--color-text-secondary)' }}>{pt.x}</td>
                                            <td style={{
                                                padding: '0.45rem 1rem',
                                                textAlign: 'right',
                                                color: trendMeta.color,
                                                fontWeight: 600,
                                            }}>
                                                {pt.y?.toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default Forecast
