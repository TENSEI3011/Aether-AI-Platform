/**
 * ============================================================
 * Query Page — Natural language data analysis
 * ============================================================
 * Features:
 *   1. queryKey counter forces ChartRenderer full remount
 *   2. All state cleared before each new query
 *   3. Voice input via Web Speech API
 *   4. Graph type selector dropdown
 *   5. "Add to Dashboard" with navigation link
 *   6. Loading spinner during processing
 * ============================================================
 */

import React, { useState, useCallback, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { askQuery } from '../api/queries'
import { exportExcel, getMyDatasets, getSchema } from '../api/datasets'
import { synthesizeSpeech } from '../api/voice'
import ChartRenderer from '../components/ChartRenderer'
import InsightDisplay from '../components/InsightDisplay'
import VoiceRecorder from '../components/VoiceRecorder'
import SaveQueryModal from '../components/SaveQueryModal'
import ReportBuilder from '../components/ReportBuilder'
import { useDashboard } from '../hooks/useDashboard'
import { getSavedQueries, deleteSavedQuery } from '../api/savedQueries'

// Available chart type options for the dropdown
const CHART_OPTIONS = [
    { value: 'auto',      label: '🔄 Auto (AI selects)' },
    { value: 'bar',       label: '📊 Bar Chart' },
    { value: 'line',      label: '📈 Line Chart' },
    { value: 'pie',       label: '🥧 Pie Chart' },
    { value: 'scatter',   label: '🔵 Scatter Plot' },
    { value: 'histogram', label: '📉 Histogram' },
    { value: 'heatmap',   label: '🌡️ Heatmap' },
    { value: 'table',     label: '📋 Data Table' },
]

function Query() {
    // ── State ────────────────────────────────────────────
    const [datasetId, setDatasetId]   = useState('')
    const [query, setQuery]           = useState('')
    const [graphType, setGraphType]   = useState('auto')
    const [loading, setLoading]       = useState(false)
    const [result, setResult]         = useState(null)
    const [error, setError]           = useState('')
    const [addedToDashboard, setAddedToDashboard] = useState(false)
    const [queryKey, setQueryKey]     = useState(0)

    // Conversational memory
    const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`)
    const [conversationHistory, setConversationHistory] = useState([])

    // Anomaly detection thresholds
    const [zThreshold, setZThreshold]       = useState(3.0)
    const [iqrMultiplier, setIqrMultiplier] = useState(1.5)
    const [showThresholds, setShowThresholds] = useState(false)

    // Dataset list from DB
    const [myDatasets, setMyDatasets] = useState([])
    const [searchParams] = useSearchParams()
    useEffect(() => {
        getMyDatasets().then(setMyDatasets).catch(() => {})
        // Gap 10: Pre-select dataset from URL params (e.g. /query?dataset=3)
        const urlDataset = searchParams.get('dataset')
        if (urlDataset) setDatasetId(urlDataset)
        // Support re-run from History page
        const rerunQuery = searchParams.get('rerun')
        if (rerunQuery) setQuery(decodeURIComponent(rerunQuery))
    }, [])

    // Data preview state
    const [previewData, setPreviewData] = useState(null)
    const [previewLoading, setPreviewLoading] = useState(false)

    // Load schema preview when dataset changes
    useEffect(() => {
        if (!datasetId.trim()) { setPreviewData(null); return }
        setPreviewLoading(true)
        getSchema(datasetId)
            .then((schema) => setPreviewData(schema))
            .catch(() => setPreviewData(null))
            .finally(() => setPreviewLoading(false))
    }, [datasetId])



    // TTS state
    const [ttsLoading, setTtsLoading] = useState(false)
    const [ttsAudio,   setTtsAudio]   = useState(null)   // HTMLAudioElement

    const { addPanel } = useDashboard()

    // Saved queries
    const [savedQueries, setSavedQueries] = useState([])
    const [showSaveModal, setShowSaveModal] = useState(false)
    const [showReportModal, setShowReportModal] = useState(false)

    useEffect(() => {
        getSavedQueries().then(setSavedQueries).catch(() => {})
    }, [])

    // ── Submit handler ───────────────────────────────────
    const handleSubmit = useCallback(async (e) => {
        e?.preventDefault()
        if (!datasetId.trim() || !query.trim()) return

        setResult(null)
        setError('')
        setAddedToDashboard(false)
        setLoading(true)

        try {
            const data = await askQuery(datasetId, query, graphType, sessionId, {
                z_threshold:    zThreshold,
                iqr_multiplier: iqrMultiplier,
            })

            if (data.success) {
                setResult(data)
                setQueryKey((prev) => prev + 1)
                setConversationHistory((prev) => [...prev, {
                    query:       query,
                    code:        data.generated_code,
                    explanation: data.explanation,
                    timestamp:   new Date().toLocaleTimeString(),
                }])
            } else {
                setError(data.errors?.join(', ') || 'Query failed validation')
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to process query')
        } finally {
            setLoading(false)
        }
    }, [datasetId, query, graphType, sessionId, zThreshold, iqrMultiplier])

    // ── Voice transcript callback ────────────────────────
    const handleTranscript = useCallback((transcript) => {
        setQuery(transcript)
    }, [])

    // ── Suggestion click — auto-fill & run ───────────────
    const handleSuggestionClick = useCallback((suggestion) => {
        setQuery(suggestion)
        setResult(null)
        setError('')
        setAddedToDashboard(false)
        setLoading(true)
        askQuery(datasetId, suggestion, graphType, sessionId, {
            z_threshold:    zThreshold,
            iqr_multiplier: iqrMultiplier,
        })
            .then((data) => {
                if (data.success) {
                    setResult(data)
                    setQueryKey((prev) => prev + 1)
                    setConversationHistory((prev) => [...prev, {
                        query: suggestion,
                        code: data.generated_code,
                        explanation: data.explanation,
                        timestamp: new Date().toLocaleTimeString(),
                    }])
                } else {
                    setError(data.errors?.join(', ') || 'Query failed')
                }
            })
            .catch((err) => setError(err.response?.data?.detail || 'Failed'))
            .finally(() => setLoading(false))
    }, [datasetId, graphType, sessionId, zThreshold, iqrMultiplier])



    // ── Add to Dashboard ─────────────────────────────────
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

    // ── Export handlers for query results ────────────────
    const handleExportExcel = useCallback(async () => {
        if (!result?.result?.data) return
        const columns = result.result.columns || Object.keys(result.result.data[0] || {})
        await exportExcel(result.result.data, columns, 'query-result.xlsx')
    }, [result])

    const handleExportImage = useCallback(async () => {
        const html2canvas = (await import('html2canvas')).default
        const el = document.getElementById('query-result-section')
        if (!el) return
        const canvas = await html2canvas(el, { backgroundColor: '#0f0f1a', scale: 2 })
        const link = document.createElement('a')
        link.download = 'query-result.png'
        link.href = canvas.toDataURL('image/png')
        link.click()
    }, [])

    // ── Read Aloud (TTS) ─────────────────────────────────
    const handleReadAloud = useCallback(async () => {
        if (!result) return

        // If already playing, stop and return early
        if (ttsAudio) {
            ttsAudio.pause()
            ttsAudio.currentTime = 0
            ttsAudio.onended = null
            setTtsAudio(null)
            return
        }

        // Build text from narration + top insight
        const text = [
            result.narration,
            ...(result.insights?.highlights?.slice(0, 2) || []),
        ].filter(Boolean).join('. ')
        if (!text) return

        setTtsLoading(true)
        try {
            const data = await synthesizeSpeech(text)
            if (data.audio_b64) {
                const audio = new Audio(`data:audio/mp3;base64,${data.audio_b64}`)
                audio.onended = () => setTtsAudio(null)
                setTtsAudio(audio)
                audio.play()
            }
        } catch (e) {
            console.error('TTS failed:', e)
        } finally {
            setTtsLoading(false)
        }
    }, [result, ttsAudio])

    // ── Render ───────────────────────────────────────────
    return (
        <>
        <div>
            <h1 className="page-title">Query Your Data</h1>
            <p className="page-subtitle">Ask questions about your dataset in plain English</p>

            {/* Conversation History Thread */}
            {conversationHistory.length > 0 && (
                <div className="card" style={{ marginBottom: 'var(--space-lg)', maxHeight: '200px', overflowY: 'auto' }}>
                    <h4 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-sm)', fontSize: '0.85rem' }}>
                        💬 Conversation ({conversationHistory.length} queries)
                    </h4>
                    {conversationHistory.map((item, i) => (
                        <div key={i} style={{
                            padding: '6px 10px', marginBottom: '4px',
                            background: 'var(--color-bg-secondary)', borderRadius: 'var(--border-radius-sm)',
                            fontSize: '0.8rem',
                        }}>
                            <span style={{ color: 'var(--color-accent)' }}>▶</span>
                            <span style={{ marginLeft: '6px' }}>{item.query}</span>
                            <span style={{ color: 'var(--color-text-muted)', marginLeft: '8px', fontSize: '0.7rem' }}>
                                {item.timestamp}
                            </span>
                        </div>
                    ))}
                </div>
            )}

            {/* Dataset Picker + Chart Type */}
            <div className="grid-2" style={{ marginBottom: 'var(--space-md)' }}>
                <div className="input-group">
                    <label>Dataset</label>
                    {myDatasets.length > 0 ? (
                        <>
                            <select
                                id="dataset-picker"
                                className="input-field"
                                value={datasetId}
                                onChange={(e) => setDatasetId(e.target.value)}
                            >
                                <option value="">— Select a dataset —</option>
                                {myDatasets.map((d) => (
                                    <option key={d.dataset_id} value={d.dataset_id}
                                        disabled={!d.in_memory}
                                    >
                                        #{d.dataset_id} · {d.filename}
                                        {d.row_count ? ` (${d.row_count.toLocaleString()} rows)` : ''}
                                        {!d.in_memory ? ' [re-upload needed]' : ''}
                                    </option>
                                ))}
                            </select>
                            <input
                                className="input-field"
                                type="text"
                                value={datasetId}
                                onChange={(e) => setDatasetId(e.target.value)}
                                placeholder="Or type dataset ID manually"
                                style={{ marginTop: 4, fontSize: '0.8rem' }}
                            />
                        </>
                    ) : (
                        <input
                            id="dataset-id-input"
                            className="input-field"
                            type="text"
                            value={datasetId}
                            onChange={(e) => setDatasetId(e.target.value)}
                            placeholder="Enter dataset ID (e.g. 1)"
                        />
                    )}
                </div>
                <div className="input-group">
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

            {/* Anomaly Threshold Controls */}
            <div style={{ marginBottom: 'var(--space-md)' }}>
                <button
                    onClick={() => setShowThresholds((v) => !v)}
                    style={{
                        background: 'none', border: '1px solid var(--color-border)',
                        borderRadius: 20, padding: '0.3rem 0.9rem',
                        color: 'var(--color-text-muted)', cursor: 'pointer',
                        fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 6,
                    }}
                >
                    ⚙️ Anomaly Thresholds {showThresholds ? '▲' : '▼'}
                </button>
                {showThresholds && (
                    <div className="card" style={{ marginTop: '0.6rem', padding: '1rem 1.25rem', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                        <div style={{ flex: 1, minWidth: 200 }}>
                            <label style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                                <span>Z-Score Threshold</span>
                                <strong style={{ color: 'var(--color-accent)' }}>{zThreshold.toFixed(1)}</strong>
                            </label>
                            <input
                                id="z-threshold-slider"
                                type="range" min="1" max="5" step="0.1"
                                value={zThreshold}
                                onChange={(e) => setZThreshold(parseFloat(e.target.value))}
                                style={{ width: '100%', marginTop: 6, accentColor: 'var(--color-accent)' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                                <span>Sensitive (1)</span><span>Strict (5)</span>
                            </div>
                        </div>
                        <div style={{ flex: 1, minWidth: 200 }}>
                            <label style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                                <span>IQR Multiplier</span>
                                <strong style={{ color: 'var(--color-accent)' }}>{iqrMultiplier.toFixed(1)}</strong>
                            </label>
                            <input
                                id="iqr-multiplier-slider"
                                type="range" min="0.5" max="3" step="0.1"
                                value={iqrMultiplier}
                                onChange={(e) => setIqrMultiplier(parseFloat(e.target.value))}
                                style={{ width: '100%', marginTop: 6, accentColor: 'var(--color-accent)' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                                <span>Tight (0.5)</span><span>Loose (3.0)</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* ── Data Preview (shows columns when dataset is selected) ── */}
            {datasetId && previewData && previewData.columns && (
                <div className="card" style={{ marginBottom: 'var(--space-md)', padding: 'var(--space-md) var(--space-lg)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <h4 style={{ color: 'var(--color-accent)', fontSize: '0.85rem', margin: 0 }}>
                            📋 Dataset Columns ({previewData.columns.length})
                        </h4>
                        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                            Click a column name to add it to your query
                        </span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                        {previewData.columns.map((col) => (
                            <button
                                key={col.name}
                                onClick={() => setQuery((prev) => prev ? `${prev} ${col.name}` : col.name)}
                                style={{
                                    padding: '3px 10px',
                                    fontSize: '0.75rem',
                                    borderRadius: 16,
                                    border: '1px solid var(--color-border)',
                                    background: col.semantic_type === 'numeric'
                                        ? 'rgba(108,99,255,0.12)'
                                        : col.semantic_type === 'datetime'
                                            ? 'rgba(52,152,219,0.12)'
                                            : 'rgba(46,204,113,0.12)',
                                    color: col.semantic_type === 'numeric'
                                        ? '#6c63ff'
                                        : col.semantic_type === 'datetime'
                                            ? '#3498db'
                                            : '#2ecc71',
                                    cursor: 'pointer',
                                    transition: 'all 0.15s',
                                }}
                                title={`${col.semantic_type} — ${col.unique_count} unique values`}
                            >
                                {col.semantic_type === 'numeric' ? '🔢' : col.semantic_type === 'datetime' ? '📅' : '🏷️'}
                                {' '}{col.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}
            {previewLoading && datasetId && (
                <div style={{ marginBottom: 'var(--space-md)', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                    Loading dataset schema...
                </div>
            )}

            {/* Query Input + Voice + Submit */}
            <form onSubmit={handleSubmit}>
                <div className="query-input-container">
                    <input
                        className="input-field"
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g., Show average sales by region"
                        disabled={loading}
                    />
                    <VoiceRecorder onTranscript={handleTranscript} />
                    <button className="btn btn-primary" type="submit" disabled={loading || !query.trim()}>
                        {loading ? '⏳ Analysing...' : '🔍 Analyse'}
                    </button>
                </div>
            </form>

            {/* Loading Spinner */}
            {loading && (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                    <div className="spinner" />
                    <span style={{ marginLeft: '1rem', color: 'var(--color-text-muted)' }}>
                        Processing your query...
                    </span>
                </div>
            )}

            {/* Error */}
            {error && <div className="alert alert-error" style={{ marginTop: 'var(--space-md)' }}>{error}</div>}

            {/* Results */}
            {result && (
                <div id="query-result-section" className="result-section" style={{ marginTop: 'var(--space-lg)' }}>
                    {/* Generated Code Card */}
                    <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-sm)' }}>
                                🤖 Generated Analysis
                            </h3>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <button
                                    className={`btn ${addedToDashboard ? 'btn-secondary' : 'btn-primary'}`}
                                    onClick={handleAddToDashboard}
                                    disabled={addedToDashboard}
                                    style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
                                >
                                    {addedToDashboard ? '✓ Pinned' : '📌 Add to Dashboard'}
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={handleExportExcel}
                                    style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
                                >
                                    📊 Excel
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={handleExportImage}
                                    style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
                                >
                                    🖼️ Image
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={handleReadAloud}
                                    disabled={ttsLoading}
                                    title="Read the AI narration aloud"
                                    style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
                                >
                                    {ttsLoading ? '⏳...' : ttsAudio ? '⏹️ Stop' : '🔊 Read Aloud'}
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => setShowSaveModal(true)}
                                    style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
                                >
                                    💾 Save Query
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => setShowReportModal(true)}
                                    style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
                                >
                                    📄 PDF Report
                                </button>
                                {addedToDashboard && (
                                    <Link to="/dashboard" className="btn btn-primary" style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}>
                                        📊 View Dashboard
                                    </Link>
                                )}
                            </div>
                        </div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                            {result.explanation}
                        </p>
                        <code className="history-code">{result.generated_code}</code>
                        {result.validation_warnings?.length > 0 && (
                            <div className="alert alert-info" style={{ marginTop: 'var(--space-sm)' }}>
                                ⚠️ Warnings: {result.validation_warnings.join(', ')}
                            </div>
                        )}
                    </div>

                    {/* Chart — key forces full remount on each new query */}
                    {result.result?.data && result.visualization && (
                        <ChartRenderer
                            key={`chart-${queryKey}`}
                            data={result.result.data}
                            visualization={result.visualization}
                            anomalies={result.anomalies}
                        />
                    )}

                    {/* Anomaly Alerts */}
                    {result.anomalies?.anomaly_count > 0 && (
                        <div className="card" style={{ marginTop: 'var(--space-md)', borderLeft: '3px solid var(--color-danger)' }}>
                            <h4 style={{ color: 'var(--color-danger)', marginBottom: 'var(--space-sm)' }}>
                                ⚠️ {result.anomalies.anomaly_count} Anomal{result.anomalies.anomaly_count === 1 ? 'y' : 'ies'} Detected
                            </h4>
                            <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                                {result.anomalies.insights.map((msg, i) => (
                                    <li key={i} style={{ marginBottom: '4px' }}>{msg}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Insights */}
                    {(result.insights || result.narration || result.suggestions?.length > 0) && (
                        <div style={{ marginTop: 'var(--space-lg)' }}>
                            <InsightDisplay
                                insights={result.insights}
                                narration={result.narration}
                                suggestions={result.suggestions}
                                onSuggestionClick={handleSuggestionClick}
                            />
                        </div>
                    )}

                    {/* Link to dedicated Data Cleaning page */}
                    <div className="card" style={{ marginTop: 'var(--space-lg)', display: 'flex', alignItems: 'center', gap: '0.75rem', padding: 'var(--space-md) var(--space-lg)' }}>
                        <span style={{ fontSize: '1.2rem' }}>🧹</span>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-text-primary)' }}>Need to clean your data?</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Remove duplicates, fill missing values, and more</div>
                        </div>
                        <Link to={`/cleaning?dataset=${datasetId}`} className="btn btn-secondary" style={{ padding: '0.4rem 1rem', fontSize: '0.82rem', borderRadius: 8, textDecoration: 'none' }}>
                            Open Data Cleaning →
                        </Link>
                    </div>
                </div>
            )}
        </div>

        {/* Save Query Modal */}
        <SaveQueryModal
            open={showSaveModal}
            onClose={() => {
                setShowSaveModal(false)
                getSavedQueries().then(setSavedQueries).catch(() => {})
            }}
            datasetId={datasetId}
            query={query}
            graphType={graphType}
        />

        {/* Report Builder Modal */}
        <ReportBuilder
            open={showReportModal}
            onClose={() => setShowReportModal(false)}
            query={query}
            result={result?.result ? { data: result.result.data, columns: result.result.columns } : null}
            insights={result?.insights}
            narration={result?.narration}
        />
    </>
    )
}

export default Query
