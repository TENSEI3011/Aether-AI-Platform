/**
 * ============================================================
 * WhatIf — Scenario Analysis Page
 * ============================================================
 * Features:
 *   - Dataset + column pickers
 *   - Mutation builder (increase/decrease/set)
 *   - Side-by-side original vs mutated comparison
 *   - Forecast comparison (optional)
 * ============================================================
 */

import React, { useState, useCallback, useEffect } from 'react'
import { getMyDatasets, getSchema } from '../api/datasets'
import { runWhatIf } from '../api/scenario'
import ChartRenderer from '../components/ChartRenderer'

const OPERATIONS = [
    { value: 'increase_pct', label: '📈 Increase by %' },
    { value: 'decrease_pct', label: '📉 Decrease by %' },
    { value: 'multiply', label: '✖️ Multiply by' },
    { value: 'set_value', label: '🔢 Set to value' },
]

function WhatIf() {
    const [datasets, setDatasets] = useState([])
    const [datasetId, setDatasetId] = useState('')
    const [columns, setColumns] = useState([])
    const [mutations, setMutations] = useState([{ column: '', operation: 'increase_pct', value: '' }])
    const [forecastX, setForecastX] = useState('')
    const [forecastY, setForecastY] = useState('')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')

    useEffect(() => {
        getMyDatasets().then(setDatasets).catch(() => {})
    }, [])

    useEffect(() => {
        if (!datasetId) { setColumns([]); return }
        getSchema(datasetId)
            .then(schema => setColumns(schema.columns || []))
            .catch(() => setColumns([]))
    }, [datasetId])

    const numericCols = columns.filter(c => c.semantic_type === 'numeric')

    const addMutation = useCallback(() => {
        setMutations(prev => [...prev, { column: '', operation: 'increase_pct', value: '' }])
    }, [])

    const removeMutation = useCallback((idx) => {
        setMutations(prev => prev.filter((_, i) => i !== idx))
    }, [])

    const updateMutation = useCallback((idx, field, val) => {
        setMutations(prev => prev.map((m, i) => i === idx ? { ...m, [field]: val } : m))
    }, [])

    const handleAnalyze = useCallback(async () => {
        const validMuts = mutations.filter(m => m.column && m.value)
        if (!datasetId || validMuts.length === 0) return

        setLoading(true)
        setError('')
        setResult(null)

        try {
            const data = await runWhatIf(
                datasetId,
                validMuts.map(m => ({ column: m.column, operation: m.operation, value: parseFloat(m.value) })),
                forecastX || null,
                forecastY || null,
            )
            if (data.success) setResult(data)
            else setError('Analysis failed')
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to run scenario analysis')
        } finally {
            setLoading(false)
        }
    }, [datasetId, mutations, forecastX, forecastY])

    return (
        <div>
            <h1 className="page-title">What-If Analysis</h1>
            <p className="page-subtitle">Modify values and instantly see how insights & forecasts change</p>

            {/* Dataset Picker */}
            <div className="input-group" style={{ marginBottom: 'var(--space-md)', maxWidth: '400px' }}>
                <label>Dataset</label>
                <select className="input-field" value={datasetId} onChange={e => setDatasetId(e.target.value)}>
                    <option value="">— Select a dataset —</option>
                    {datasets.filter(d => d.in_memory).map(d => (
                        <option key={d.dataset_id} value={d.dataset_id}>
                            #{d.dataset_id} · {d.filename}
                        </option>
                    ))}
                </select>
            </div>

            {/* Mutations Builder */}
            <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                    🧪 Define Mutations
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }}>
                    Specify how you want to modify the data. Example: "What if revenue increases by 20%?"
                </p>

                {mutations.map((m, i) => (
                    <div key={i} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', alignItems: 'end', flexWrap: 'wrap' }}>
                        <div className="input-group" style={{ flex: 1, minWidth: '150px' }}>
                            {i === 0 && <label>Column</label>}
                            <select className="input-field" value={m.column}
                                onChange={e => updateMutation(i, 'column', e.target.value)}>
                                <option value="">— Column —</option>
                                {numericCols.map(c => (
                                    <option key={c.name} value={c.name}>{c.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="input-group" style={{ flex: 1, minWidth: '150px' }}>
                            {i === 0 && <label>Operation</label>}
                            <select className="input-field" value={m.operation}
                                onChange={e => updateMutation(i, 'operation', e.target.value)}>
                                {OPERATIONS.map(op => (
                                    <option key={op.value} value={op.value}>{op.label}</option>
                                ))}
                            </select>
                        </div>
                        <div className="input-group" style={{ flex: 0.7, minWidth: '100px' }}>
                            {i === 0 && <label>Value</label>}
                            <input className="input-field" type="number" value={m.value}
                                onChange={e => updateMutation(i, 'value', e.target.value)}
                                placeholder={m.operation.includes('pct') ? '20' : '1.5'} />
                        </div>
                        {mutations.length > 1 && (
                            <button className="btn btn-secondary" onClick={() => removeMutation(i)}
                                style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#EF4444' }}>✕</button>
                        )}
                    </div>
                ))}

                <button className="btn btn-secondary" onClick={addMutation}
                    style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', marginTop: '0.5rem' }}>
                    ➕ Add Another Mutation
                </button>
            </div>

            {/* Optional Forecast Comparison */}
            <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                <h4 style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-sm)', fontSize: '0.9rem' }}>
                    📈 Compare Forecasts (Optional)
                </h4>
                <div className="grid-2" style={{ gap: 'var(--space-sm)' }}>
                    <div className="input-group">
                        <label>X Column (time/category)</label>
                        <select className="input-field" value={forecastX} onChange={e => setForecastX(e.target.value)}>
                            <option value="">— None —</option>
                            {columns.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                        </select>
                    </div>
                    <div className="input-group">
                        <label>Y Column (values)</label>
                        <select className="input-field" value={forecastY} onChange={e => setForecastY(e.target.value)}>
                            <option value="">— None —</option>
                            {numericCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                        </select>
                    </div>
                </div>
            </div>

            <button className="btn btn-primary" onClick={handleAnalyze}
                disabled={loading || !datasetId || !mutations.some(m => m.column && m.value)}
                style={{ marginBottom: 'var(--space-lg)' }}>
                {loading ? '⏳ Analyzing...' : '🧪 Run What-If Analysis'}
            </button>

            {error && <div className="alert alert-error">{error}</div>}

            {/* Results */}
            {result && (
                <div style={{ animation: 'fadeIn 0.4s ease' }}>
                    {/* Mutations Applied */}
                    <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                        <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                            🧪 Mutations Applied
                        </h3>
                        <div style={{ display: 'grid', gap: 'var(--space-xs)' }}>
                            {result.mutations_applied.map((m, i) => (
                                <div key={i} style={{
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                    padding: '0.5rem 0.75rem', background: 'var(--color-bg-secondary)',
                                    borderRadius: 'var(--border-radius-sm)', fontSize: '0.85rem',
                                }}>
                                    <span style={{ color: 'var(--color-text-primary)' }}>
                                        <strong>{m.column}</strong> — {OPERATIONS.find(o => o.value === m.operation)?.label || m.operation} {m.value}
                                    </span>
                                    <span style={{ color: m.after_mean > m.before_mean ? '#10B981' : '#EF4444' }}>
                                        {m.before_mean} → {m.after_mean} ({m.after_mean > m.before_mean ? '▲' : '▼'}{Math.abs(((m.after_mean - m.before_mean) / m.before_mean) * 100).toFixed(1)}%)
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Side-by-side Insights */}
                    <div className="grid-2" style={{ marginBottom: 'var(--space-lg)' }}>
                        <div className="card" style={{ borderTop: '3px solid var(--color-accent)' }}>
                            <h4 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-sm)', fontSize: '0.9rem' }}>
                                📊 Original Insights
                            </h4>
                            <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                                {result.original.insights?.summary}
                            </p>
                            <ul style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0, paddingLeft: '1rem' }}>
                                {result.original.insights?.highlights?.slice(0, 3).map((h, i) => (
                                    <li key={i} style={{ marginBottom: '4px' }}>{h}</li>
                                ))}
                            </ul>
                        </div>
                        <div className="card" style={{ borderTop: '3px solid var(--color-tertiary)' }}>
                            <h4 style={{ color: 'var(--color-tertiary)', marginBottom: 'var(--space-sm)', fontSize: '0.9rem' }}>
                                🧪 Mutated Insights
                            </h4>
                            <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                                {result.mutated.insights?.summary}
                            </p>
                            <ul style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0, paddingLeft: '1rem' }}>
                                {result.mutated.insights?.highlights?.slice(0, 3).map((h, i) => (
                                    <li key={i} style={{ marginBottom: '4px' }}>{h}</li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    {/* Forecast Comparison */}
                    {result.original.forecast && result.mutated.forecast && (
                        <div className="grid-2" style={{ marginBottom: 'var(--space-lg)' }}>
                            <div className="card">
                                <h4 style={{ color: 'var(--color-accent)', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Original Forecast</h4>
                                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                    Trend: <strong>{result.original.forecast.trend}</strong> | Confidence: {result.original.forecast.confidence}
                                </p>
                                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{result.original.forecast.summary}</p>
                            </div>
                            <div className="card">
                                <h4 style={{ color: 'var(--color-tertiary)', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Mutated Forecast</h4>
                                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                    Trend: <strong>{result.mutated.forecast.trend}</strong> | Confidence: {result.mutated.forecast.confidence}
                                </p>
                                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{result.mutated.forecast.summary}</p>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default WhatIf
