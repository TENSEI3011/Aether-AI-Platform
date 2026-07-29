/**
 * ============================================================
 * Query Page — InsightAI 3-column results layout
 * ============================================================
 * All logic preserved:
 *   - queryKey counter for ChartRenderer remount
 *   - askQuery() API call
 *   - VoiceRecorder integration
 *   - addPanel() to Dashboard
 * ============================================================
 */

import React, { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { askQuery } from '../api/queries'
import ChartRenderer from '../components/ChartRenderer'
import InsightDisplay from '../components/InsightDisplay'
import VoiceRecorder from '../components/VoiceRecorder'
import { useDashboard } from '../hooks/useDashboard'

const CHART_OPTIONS = [
    { value: 'auto',  label: '🔄 Auto (AI selects)' },
    { value: 'bar',   label: '📊 Bar Chart' },
    { value: 'line',  label: '📈 Line Chart' },
    { value: 'pie',   label: '🥧 Pie Chart' },
    { value: 'table', label: '📋 Data Table' },
]

function Query() {
    const [datasetId, setDatasetId]           = useState('')
    const [query, setQuery]                   = useState('')
    const [graphType, setGraphType]           = useState('auto')
    const [loading, setLoading]               = useState(false)
    const [result, setResult]                 = useState(null)
    const [error, setError]                   = useState('')
    const [addedToDashboard, setAddedToDashboard] = useState(false)
    const [queryKey, setQueryKey]             = useState(0)

    const { addPanel } = useDashboard()

    const handleSubmit = useCallback(async (e) => {
        e?.preventDefault()
        if (!datasetId.trim() || !query.trim()) return

        setResult(null); setError(''); setAddedToDashboard(false); setLoading(true)
        try {
            const data = await askQuery(datasetId, query, graphType)
            if (data.success) {
                setResult(data)
                setQueryKey((prev) => prev + 1)
            } else {
                setError(data.errors?.join(', ') || 'Query failed validation')
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to process query')
        } finally {
            setLoading(false)
        }
    }, [datasetId, query, graphType])

    const handleTranscript = useCallback((transcript) => {
        setQuery(transcript)
    }, [])

    const handleAddToDashboard = useCallback(() => {
        if (!result) return
        addPanel({
            query: result.query,
            data: result.result?.data,
            visualization: result.visualization,
            insights: result.insights,
            generatedCode: result.generated_code,
        })
        setAddedToDashboard(true)
    }, [result, addPanel])

    return (
        <div style={{ position: 'relative' }}>
            <div className="bg-orb bg-orb-1" />
            <div className="bg-orb bg-orb-2" />

            <h1 className="page-title">Ask Your Data</h1>
            <p className="page-subtitle">
                Type your question in plain English and get instant AI-powered charts and insights
            </p>

            {/* ── Query Input Card ── */}
            <div className="card query-form-card">
                {/* Dataset ID + Chart Type row */}
                <div className="grid-2" style={{ marginBottom: 'var(--space-lg)' }}>
                    <div className="input-group" style={{ marginBottom: 0 }}>
                        <label>Dataset ID</label>
                        <input
                            className="input-field"
                            type="text"
                            value={datasetId}
                            onChange={(e) => setDatasetId(e.target.value)}
                            placeholder="e.g. 1 (from Upload page)"
                        />
                    </div>
                    <div className="input-group" style={{ marginBottom: 0 }}>
                        <label>Chart Type</label>
                        <select
                            className="input-field"
                            value={graphType}
                            onChange={(e) => setGraphType(e.target.value)}
                        >
                            {CHART_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Query input + voice + submit */}
                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '0.5rem', fontSize: '0.72rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        Natural Language Query
                    </div>
                    <div className="query-input-row">
                        <input
                            className="input-field"
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="e.g. Show average sales by region"
                            disabled={loading}
                        />
                        <VoiceRecorder onTranscript={handleTranscript} />
                        <button
                            className="btn btn-primary"
                            type="submit"
                            disabled={loading || !query.trim()}
                            style={{ flexShrink: 0, padding: '0 1.5rem', height: '46px' }}
                        >
                            {loading ? (
                                <><div className="spinner" style={{ width: 16, height: 16 }} /> Analysing...</>
                            ) : (
                                '✦ Analyse'
                            )}
                        </button>
                    </div>
                </form>
            </div>

            {/* ── Loading ── */}
            {loading && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', padding: '2rem' }}>
                    <div className="spinner" />
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                        AI is processing your query...
                    </span>
                </div>
            )}

            {/* ── Error ── */}
            {error && (
                <div className="alert alert-error" style={{ marginTop: 'var(--space-md)' }}>
                    ⚠ {error}
                </div>
            )}

            {/* ── Results: 3-column layout ── */}
            {result && (
                <div style={{ marginTop: 'var(--space-lg)' }}>
                    {/* Add to Dashboard bar */}
                    <div style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        marginBottom: 'var(--space-md)', flexWrap: 'wrap', gap: '0.75rem'
                    }}>
                        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-secondary)', margin: 0 }}>
                            ✦ AI Analysis Results
                        </h2>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                                className={`btn ${addedToDashboard ? 'btn-secondary' : 'btn-primary'}`}
                                onClick={handleAddToDashboard}
                                disabled={addedToDashboard}
                                style={{ padding: '0.4rem 1.1rem', fontSize: '0.85rem' }}
                            >
                                {addedToDashboard ? '✓ Pinned to Dashboard' : '📌 Add to Dashboard'}
                            </button>
                            {addedToDashboard && (
                                <Link to="/dashboard" className="btn btn-primary" style={{ padding: '0.4rem 1.1rem', fontSize: '0.85rem' }}>
                                    📊 View Dashboard
                                </Link>
                            )}
                        </div>
                    </div>

                    {/* 3-column grid */}
                    <div className="query-results-grid">
                        {/* Col 1: Code + Explanation */}
                        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                            <div>
                                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c4c0ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                                    🤖 Generated Code
                                </div>
                                <code className="code-block">{result.generated_code}</code>
                            </div>
                            {result.explanation && (
                                <div>
                                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                                        Explanation
                                    </div>
                                    <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                                        {result.explanation}
                                    </p>
                                </div>
                            )}
                            {result.validation_warnings?.length > 0 && (
                                <div className="alert alert-info" style={{ margin: 0 }}>
                                    ⚠ {result.validation_warnings.join(', ')}
                                </div>
                            )}
                        </div>

                        {/* Col 2: Chart */}
                        {result.result?.data && result.visualization ? (
                            <ChartRenderer
                                key={`chart-${queryKey}`}
                                data={result.result.data}
                                visualization={result.visualization}
                            />
                        ) : (
                            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <p style={{ color: 'var(--color-text-muted)' }}>No chart data available</p>
                            </div>
                        )}

                        {/* Col 3: Insights */}
                        {result.insights ? (
                            <div className="card">
                                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#a6e6ff', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-md)' }}>
                                    💡 AI Insights
                                </div>
                                <InsightDisplay insights={result.insights} />
                            </div>
                        ) : (
                            <div />
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

export default Query
