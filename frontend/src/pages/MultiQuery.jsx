/**
 * ============================================================
 * MultiQuery Page — JOIN queries across two datasets
 * ============================================================
 * Lets users:
 *   1. Select two datasets
 *   2. Pick a join column (auto-detected from common columns)
 *   3. Choose join type (inner / left / right / outer)
 *   4. Preview the merged table
 *   5. Ask a natural-language question on the merged result
 *   6. See the full chart + insights + narration
 * ============================================================
 */

import React, { useState, useEffect } from 'react'
import { getMyDatasets } from '../api/datasets'
import { getCommonColumns, previewJoin, askMultiQuery } from '../api/multiQuery'
import ChartRenderer from '../components/ChartRenderer'
import InsightDisplay from '../components/InsightDisplay'

const JOIN_TYPES = [
    { value: 'inner', label: 'Inner Join — only matching rows in both' },
    { value: 'left',  label: 'Left Join  — all rows from Dataset 1' },
    { value: 'right', label: 'Right Join — all rows from Dataset 2' },
    { value: 'outer', label: 'Outer Join — all rows from both' },
]

const CHART_OPTIONS = [
    { value: 'auto',      label: '🔄 Auto (AI selects)' },
    { value: 'bar',       label: '📊 Bar Chart' },
    { value: 'line',      label: '📈 Line Chart' },
    { value: 'pie',       label: '🥧 Pie Chart' },
    { value: 'table',     label: '📋 Data Table' },
]

function MultiQuery() {
    // ── State ─────────────────────────────────────────────
    const [datasets,       setDatasets]      = useState([])
    const [ds1,            setDs1]           = useState('')
    const [ds2,            setDs2]           = useState('')
    const [joinHow,        setJoinHow]       = useState('inner')
    const [commonCols,     setCommonCols]    = useState([])
    const [joinOn,         setJoinOn]        = useState('')
    const [preview,        setPreview]       = useState(null)
    const [previewLoading, setPreviewLoading]= useState(false)
    const [query,          setQuery]         = useState('')
    const [graphType,      setGraphType]     = useState('auto')
    const [loading,        setLoading]       = useState(false)
    const [result,         setResult]        = useState(null)
    const [error,          setError]         = useState('')
    const [colsError,      setColsError]     = useState('')
    const [queryKey,       setQueryKey]      = useState(0)

    // ── Load datasets on mount ────────────────────────────
    useEffect(() => {
        getMyDatasets()
            .then(setDatasets)
            .catch(() => setDatasets([]))
    }, [])

    // ── Fetch common columns when both datasets selected ──
    useEffect(() => {
        if (!ds1 || !ds2 || ds1 === ds2) {
            setCommonCols([])
            setJoinOn('')
            return
        }
        setColsError('')
        getCommonColumns(ds1, ds2)
            .then(data => {
                setCommonCols(data.common_columns || [])
                if (data.common_columns?.length > 0) {
                    setJoinOn(data.common_columns[0])
                } else {
                    setColsError('⚠️ No common columns found. These datasets may not be joinable.')
                }
            })
            .catch(() => setColsError('Failed to fetch common columns.'))
    }, [ds1, ds2])

    // ── Preview Join ──────────────────────────────────────
    const handlePreview = async () => {
        if (!ds1 || !ds2 || !joinOn) return
        setPreviewLoading(true)
        setPreview(null)
        try {
            const data = await previewJoin(ds1, ds2, joinOn, joinHow)
            setPreview(data)
        } catch (e) {
            setError(e.response?.data?.detail || 'Preview failed.')
        } finally {
            setPreviewLoading(false)
        }
    }

    // ── Submit Query ──────────────────────────────────────
    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!ds1 || !ds2 || !joinOn || !query.trim()) return
        setLoading(true)
        setResult(null)
        setError('')
        setQueryKey(k => k + 1)
        try {
            const data = await askMultiQuery(ds1, ds2, joinOn, joinHow, query, graphType)
            if (!data.success) {
                setError((data.errors || ['Query failed.']).join(' | '))
            } else {
                setResult(data)
            }
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to run query.')
        } finally {
            setLoading(false)
        }
    }

    // ── Helpers ───────────────────────────────────────────
    const dsLabel = (id) => {
        const ds = datasets.find(d => d.dataset_id == id)
        return ds ? ds.filename : id
    }

    return (
        <div className="page-container" style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' }}>

            {/* ── Header ─────────────────────────────────── */}
            <div style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.4rem' }}>
                    🔗 Join Query
                </h1>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '1rem' }}>
                    Merge two datasets and ask natural-language questions on the combined data.
                </p>
            </div>

            {/* ── Step 1: Select Datasets ─────────────────── */}
            <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>
                    Step 1 — Select Datasets
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                            Dataset 1
                        </label>
                        <select
                            value={ds1}
                            onChange={e => setDs1(e.target.value)}
                            className="query-input"
                            style={{ width: '100%' }}
                        >
                            <option value="">-- Select Dataset 1 --</option>
                            {datasets.map(d => (
                                <option key={d.dataset_id} value={d.dataset_id}>{d.filename} (ID: {d.dataset_id})</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                            Dataset 2
                        </label>
                        <select
                            value={ds2}
                            onChange={e => setDs2(e.target.value)}
                            className="query-input"
                            style={{ width: '100%' }}
                        >
                            <option value="">-- Select Dataset 2 --</option>
                            {datasets.map(d => (
                                <option key={d.dataset_id} value={d.dataset_id}>{d.filename} (ID: {d.dataset_id})</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* ── Step 2: Join Configuration ─────────────── */}
            {ds1 && ds2 && ds1 !== ds2 && (
                <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                    <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>
                        Step 2 — Configure Join
                    </h2>

                    {colsError && (
                        <div style={{ color: '#f87171', background: 'rgba(248,113,113,0.1)', padding: '0.75rem 1rem', borderRadius: 8, marginBottom: '1rem' }}>
                            {colsError}
                        </div>
                    )}

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                                Join Column <span style={{ color: 'var(--color-accent)' }}>*</span>
                            </label>
                            {commonCols.length > 0 ? (
                                <select
                                    value={joinOn}
                                    onChange={e => setJoinOn(e.target.value)}
                                    className="query-input"
                                    style={{ width: '100%' }}
                                >
                                    {commonCols.map(c => (
                                        <option key={c} value={c}>{c}</option>
                                    ))}
                                </select>
                            ) : (
                                <input
                                    type="text"
                                    value={joinOn}
                                    onChange={e => setJoinOn(e.target.value)}
                                    placeholder="Type a column name manually"
                                    className="query-input"
                                    style={{ width: '100%' }}
                                />
                            )}
                            {commonCols.length > 0 && (
                                <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '0.3rem' }}>
                                    {commonCols.length} common column{commonCols.length > 1 ? 's' : ''} detected
                                </p>
                            )}
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                                Join Type
                            </label>
                            <select
                                value={joinHow}
                                onChange={e => setJoinHow(e.target.value)}
                                className="query-input"
                                style={{ width: '100%' }}
                            >
                                {JOIN_TYPES.map(jt => (
                                    <option key={jt.value} value={jt.value}>{jt.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <button
                        onClick={handlePreview}
                        disabled={!joinOn || previewLoading}
                        className="btn btn-secondary"
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                        {previewLoading ? '⏳ Loading...' : '👁️ Preview Merged Data'}
                    </button>
                </div>
            )}

            {/* ── Preview Table ──────────────────────────── */}
            {preview && (
                <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem', overflowX: 'auto' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>📋 Merged Preview</h2>
                        <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                            {preview.merged_rows} rows × {preview.merged_cols} columns
                            &nbsp;·&nbsp;{joinHow.toUpperCase()} JOIN on <code style={{ color: 'var(--color-accent)' }}>{joinOn}</code>
                        </span>
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                        <thead>
                            <tr>
                                {preview.columns?.map(col => (
                                    <th key={col} style={{
                                        textAlign: 'left', padding: '0.5rem 0.75rem',
                                        background: 'var(--color-bg-hover)',
                                        color: 'var(--color-accent)',
                                        borderBottom: '1px solid var(--color-border)',
                                        whiteSpace: 'nowrap',
                                    }}>{col}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {preview.preview?.slice(0, 5).map((row, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                                    {preview.columns?.map(col => (
                                        <td key={col} style={{ padding: '0.4rem 0.75rem', color: 'var(--color-text-secondary)', whiteSpace: 'nowrap' }}>
                                            {String(row[col] ?? '')}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {preview.preview?.length > 5 && (
                        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
                            Showing 5 of {preview.merged_rows} merged rows
                        </p>
                    )}
                </div>
            )}

            {/* ── Step 3: Ask Query ──────────────────────── */}
            {ds1 && ds2 && joinOn && (
                <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                    <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>
                        Step 3 — Ask a Question
                    </h2>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                        Querying: <strong>{dsLabel(ds1)}</strong> + <strong>{dsLabel(ds2)}</strong>
                        &nbsp;joined on <code style={{ color: 'var(--color-accent)' }}>{joinOn}</code>
                    </div>

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        <textarea
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                            placeholder="e.g. Compare average PM10 across cities from both datasets"
                            className="query-input"
                            rows={3}
                            style={{ resize: 'vertical', fontFamily: 'inherit' }}
                        />
                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                            <select
                                value={graphType}
                                onChange={e => setGraphType(e.target.value)}
                                className="query-input"
                                style={{ width: 200 }}
                            >
                                {CHART_OPTIONS.map(o => (
                                    <option key={o.value} value={o.value}>{o.label}</option>
                                ))}
                            </select>
                            <button
                                type="submit"
                                disabled={loading || !query.trim()}
                                className="btn btn-primary"
                                style={{ flex: 1 }}
                            >
                                {loading ? '⏳ Analysing...' : '🔍 Analyse'}
                            </button>
                        </div>
                    </form>

                    {error && (
                        <div style={{ color: '#f87171', background: 'rgba(248,113,113,0.1)', padding: '0.75rem 1rem', borderRadius: 8, marginTop: '0.75rem' }}>
                            ⚠️ {error}
                        </div>
                    )}
                </div>
            )}

            {/* ── Results ────────────────────────────────── */}
            {result && (
                <>
                    {/* Join info badge */}
                    <div style={{
                        display: 'flex', gap: '0.5rem', flexWrap: 'wrap',
                        marginBottom: '1rem', alignItems: 'center',
                    }}>
                        <span style={{ fontSize: '0.78rem', background: 'rgba(139,92,246,0.15)', color: '#a78bfa', padding: '0.25rem 0.75rem', borderRadius: 20, border: '1px solid rgba(139,92,246,0.3)' }}>
                            🔗 {result.join_info?.join_how?.toUpperCase()} JOIN on {result.join_info?.join_on}
                        </span>
                        <span style={{ fontSize: '0.78rem', background: 'rgba(16,185,129,0.1)', color: '#34d399', padding: '0.25rem 0.75rem', borderRadius: 20, border: '1px solid rgba(16,185,129,0.3)' }}>
                            {result.join_info?.merged_rows} merged rows
                        </span>
                    </div>

                    {/* Explanation */}
                    <div className="card" style={{ padding: '1rem 1.5rem', marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                        <code style={{ background: 'none', fontSize: '0.82rem' }}>{result.generated_code}</code>
                    </div>

                    {/* Chart */}
                    {result.visualization && result.result && (
                        <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                            <ChartRenderer
                                key={queryKey}
                                data={result.result.data}
                                columns={result.result.columns}
                                visualization={result.visualization}
                                query={query}
                            />
                        </div>
                    )}

                    {/* Insights */}
                    {result.insights && (
                        <InsightDisplay
                            insights={result.insights}
                            narration={result.narration}
                            anomalies={result.anomalies}
                            suggestions={result.suggestions}
                            onSuggestionClick={q => setQuery(q)}
                        />
                    )}
                </>
            )}
        </div>
    )
}

export default MultiQuery
