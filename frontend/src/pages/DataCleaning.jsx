/**
 * DataCleaning — Power BI Power Query–Style Data Cleaning Page
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { cleanDataset } from '../api/queries'
import { getMyDatasets, getFullProfile, getSchema } from '../api/datasets'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts'

const COLORS = ['#7C3AED','#A855F7','#3498db','#2ecc71','#f1c40f','#e74c3c','#1abc9c','#e67e22']
const tipStyle = { background: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: 8, color: '#e0e0e0' }

const QUICK_ACTIONS = [
    { label: 'Remove Duplicates',       icon: '🔁', instruction: 'remove duplicate rows' },
    { label: 'Drop Null Rows',          icon: '🚫', instruction: 'drop rows with any null values' },
    { label: 'Fill Nulls → 0',          icon: '0️⃣',  instruction: 'fill all missing values with 0' },
    { label: 'Fill Nulls → Mean',       icon: '📊', instruction: 'fill missing numeric values with column mean' },
    { label: 'Fill Nulls → Median',     icon: '📈', instruction: 'fill missing numeric values with column median' },
    { label: 'Forward Fill',            icon: '⏩', instruction: 'forward fill missing values' },
    { label: 'Trim Whitespace',         icon: '✂️',  instruction: 'strip leading and trailing whitespace from all string columns' },
    { label: 'Lowercase Strings',       icon: '🔡', instruction: 'convert all string columns to lowercase' },
    { label: 'Drop Constant Columns',   icon: '🗑️',  instruction: 'drop columns where all values are the same' },
    { label: 'Auto-Convert Types',      icon: '🔄', instruction: 'convert columns to their best inferred types' },
]

function DataCleaning() {
    const [searchParams] = useSearchParams()
    const [datasetId, setDatasetId] = useState(searchParams.get('dataset') || '')
    const [myDatasets, setMyDatasets] = useState([])

    // Profile / quality
    const [profile, setProfile] = useState(null)
    const [profileLoading, setProfileLoading] = useState(false)

    // Preview
    const [preview, setPreview] = useState(null)
    const [previewLoading, setPreviewLoading] = useState(false)

    // Cleaning
    const [instruction, setInstruction] = useState('')
    const [cleaning, setCleaning] = useState(false)
    const [cleanResult, setCleanResult] = useState(null)
    const [cleanError, setCleanError] = useState('')

    // History log
    const [history, setHistory] = useState([])

    // Active tab
    const [activeTab, setActiveTab] = useState('quality')

    useEffect(() => { getMyDatasets().then(setMyDatasets).catch(() => {}) }, [])

    // Load profile + preview when dataset changes
    const loadDataset = useCallback(async (id) => {
        if (!id) { setProfile(null); setPreview(null); return }
        setProfileLoading(true)
        setPreviewLoading(true)
        setCleanResult(null)
        setCleanError('')
        setHistory([])
        try { setProfile(await getFullProfile(id)) } catch { setProfile(null) }
        try { setPreview(await getSchema(id)) } catch { setPreview(null) }
        setProfileLoading(false)
        setPreviewLoading(false)
    }, [])

    useEffect(() => { loadDataset(datasetId) }, [datasetId, loadDataset])

    // Quality KPIs
    const kpis = useMemo(() => {
        if (!profile) return null
        const totalMissing = profile.missing_values?.reduce((s, m) => s + m.missing_count, 0) || 0
        return {
            rows: profile.overview?.rows || 0,
            cols: profile.overview?.columns || 0,
            missing: totalMissing,
            dupes: profile.overview?.duplicate_rows || 0,
        }
    }, [profile])

    // Run a cleaning operation
    const runClean = useCallback(async (instr) => {
        if (!datasetId.trim() || !instr.trim()) return
        setCleaning(true)
        setCleanResult(null)
        setCleanError('')
        try {
            const data = await cleanDataset(datasetId, instr)
            if (data.success) {
                setCleanResult(data)
                setHistory(prev => [...prev, {
                    step: prev.length + 1,
                    instruction: instr,
                    before: data.before_rows,
                    after: data.after_rows,
                    code: data.generated_code,
                    time: new Date().toLocaleTimeString(),
                }])
                // Refresh profile after cleaning
                try { setProfile(await getFullProfile(datasetId)) } catch {}
                try { setPreview(await getSchema(datasetId)) } catch {}
            } else {
                setCleanError(data.errors?.join(', ') || 'Cleaning failed')
            }
        } catch (err) {
            setCleanError(err.response?.data?.detail || 'Cleaning request failed')
        } finally {
            setCleaning(false)
        }
    }, [datasetId])

    const handleCleanSubmit = () => { runClean(instruction); setInstruction('') }

    return (
        <div>
            <h1 className="page-title" style={{ animation: 'fadeIn 0.4s ease' }}>Data Cleaning</h1>
            <p className="page-subtitle" style={{ animation: 'fadeIn 0.6s ease' }}>
                Clean & transform your data — Power Query–style editor
            </p>

            {/* Dataset Picker */}
            <div className="card" style={{ marginBottom: 'var(--space-lg)', padding: 'var(--space-md) var(--space-lg)', animation: 'fadeIn 0.5s ease' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <div className="input-group" style={{ flex: 1, minWidth: 200, margin: 0 }}>
                        <label style={{ fontSize: '0.8rem', marginBottom: 4 }}>Select Dataset</label>
                        {myDatasets.length > 0 ? (
                            <select className="input-field" value={datasetId} onChange={e => setDatasetId(e.target.value)}>
                                <option value="">— Choose a dataset —</option>
                                {myDatasets.map(d => (
                                    <option key={d.dataset_id} value={d.dataset_id} disabled={!d.in_memory}>
                                        #{d.dataset_id} · {d.filename}{d.row_count ? ` (${d.row_count.toLocaleString()} rows)` : ''}{!d.in_memory ? ' [re-upload]' : ''}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <input className="input-field" type="text" value={datasetId}
                                onChange={e => setDatasetId(e.target.value)} placeholder="Enter dataset ID" />
                        )}
                    </div>
                    {datasetId && (
                        <Link to={`/query?dataset=${datasetId}`} className="btn btn-secondary"
                            style={{ padding: '0.4rem 1rem', fontSize: '0.8rem', borderRadius: 8, textDecoration: 'none', alignSelf: 'flex-end' }}>
                            ✦ Query This Dataset
                        </Link>
                    )}
                </div>
            </div>

            {profileLoading && (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                    <div className="spinner" /><span style={{ marginLeft: '1rem', color: 'var(--color-text-muted)' }}>Loading data profile...</span>
                </div>
            )}

            {/* Main Content — only show when dataset selected */}
            {datasetId && profile && (
                <>
                    {/* KPI Cards */}
                    <div className="grid-4" style={{ marginBottom: 'var(--space-lg)', animation: 'fadeIn 0.5s ease' }}>
                        {[
                            { value: kpis?.rows?.toLocaleString(), label: 'Total Rows', icon: '📋', color: '#7C3AED' },
                            { value: kpis?.cols, label: 'Columns', icon: '📊', color: '#A855F7' },
                            { value: kpis?.missing?.toLocaleString(), label: 'Missing Values', icon: '⚠️', color: kpis?.missing > 0 ? '#F59E0B' : '#10B981' },
                            { value: kpis?.dupes, label: 'Duplicate Rows', icon: '🔁', color: kpis?.dupes > 0 ? '#EF4444' : '#10B981' },
                        ].map((k, i) => (
                            <div key={i} className="card kpi-card" style={{ animation: `fadeIn ${0.3 + i * 0.1}s ease` }}>
                                <div style={{ fontSize: '1.2rem', marginBottom: '0.5rem', opacity: 0.7 }}>{k.icon}</div>
                                <div className="kpi-value" style={{ background: `linear-gradient(135deg, ${k.color}, ${k.color}dd)`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>{k.value}</div>
                                <div className="kpi-label">{k.label}</div>
                            </div>
                        ))}
                    </div>

                    {/* Tab Bar */}
                    <div style={{ display: 'flex', gap: 4, marginBottom: 'var(--space-lg)', animation: 'fadeIn 0.6s ease' }}>
                        {[
                            { id: 'quality', label: '📉 Data Quality', },
                            { id: 'clean', label: '🧹 Clean Data', },
                            { id: 'history', label: '📜 Applied Steps', badge: history.length },
                        ].map(tab => (
                            <button key={tab.id}
                                className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setActiveTab(tab.id)}
                                style={{ padding: '0.4rem 1rem', fontSize: '0.82rem', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                                {tab.label}
                                {tab.badge > 0 && (
                                    <span style={{ background: 'rgba(124,58,237,0.3)', padding: '1px 7px', borderRadius: 10, fontSize: '0.7rem' }}>{tab.badge}</span>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* ─── TAB: Data Quality ──────────────────── */}
                    {activeTab === 'quality' && (
                        <div style={{ animation: 'fadeIn 0.3s ease' }}>
                            <div className="grid-2" style={{ gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
                                {/* Missing Values Chart */}
                                <div className="card">
                                    <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                                        📉 Missing Values by Column
                                    </h3>
                                    {profile.missing_values?.some(m => m.missing_count > 0) ? (
                                        <ResponsiveContainer width="100%" height={280}>
                                            <BarChart data={profile.missing_values.filter(m => m.missing_count > 0)}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                                                <XAxis dataKey="column" tick={{ fill: '#a0a0b0', fontSize: 11 }} angle={-25} textAnchor="end" height={70} />
                                                <YAxis tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                                                <Tooltip contentStyle={tipStyle} />
                                                <Bar dataKey="missing_count" fill="#e74c3c" radius={[4,4,0,0]} name="Missing" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <p style={{ color: 'var(--color-success)', textAlign: 'center', padding: '2rem' }}>✅ No missing values!</p>
                                    )}
                                </div>
                                {/* Type Distribution */}
                                <div className="card">
                                    <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                                        🔤 Data Type Distribution
                                    </h3>
                                    <ResponsiveContainer width="100%" height={280}>
                                        <PieChart>
                                            <Pie data={Object.entries(profile.data_types?.distribution || {}).map(([name, value]) => ({ name, value }))}
                                                dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90}
                                                label={({ name, value }) => `${name}: ${value}`}>
                                                {Object.entries(profile.data_types?.distribution || {}).map((_, i) => (
                                                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip contentStyle={tipStyle} /><Legend />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Column Details Table */}
                            <div className="card">
                                <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>📋 Column Details</h3>
                                <div className="data-table-container">
                                    <table className="data-table">
                                        <thead><tr><th>Column</th><th>Data Type</th><th>Semantic</th><th>Missing</th><th>Missing %</th></tr></thead>
                                        <tbody>
                                            {profile.data_types?.columns?.map((col, i) => {
                                                const m = profile.missing_values?.find(mv => mv.column === col.column)
                                                return (
                                                    <tr key={i}>
                                                        <td><strong>{col.column}</strong></td>
                                                        <td>{col.dtype}</td>
                                                        <td>
                                                            <span style={{
                                                                padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem',
                                                                background: col.semantic_type === 'numeric' ? 'rgba(108,99,255,0.2)' : col.semantic_type === 'datetime' ? 'rgba(52,152,219,0.2)' : 'rgba(46,204,113,0.2)',
                                                                color: col.semantic_type === 'numeric' ? '#6c63ff' : col.semantic_type === 'datetime' ? '#3498db' : '#2ecc71',
                                                            }}>{col.semantic_type}</span>
                                                        </td>
                                                        <td>{m?.missing_count || 0}</td>
                                                        <td style={{ color: (m?.missing_percent || 0) > 0 ? '#F59E0B' : 'var(--color-success)' }}>{m?.missing_percent || 0}%</td>
                                                    </tr>
                                                )
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ─── TAB: Clean Data ────────────────────── */}
                    {activeTab === 'clean' && (
                        <div style={{ animation: 'fadeIn 0.3s ease' }}>
                            {/* Quick Actions Grid */}
                            <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                                <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-sm)', fontSize: '0.95rem' }}>⚡ Quick Actions</h3>
                                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }}>
                                    One-click cleaning operations — applied immediately to your dataset
                                </p>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.5rem' }}>
                                    {QUICK_ACTIONS.map(action => (
                                        <button key={action.label}
                                            className="btn btn-secondary clean-action-btn"
                                            onClick={() => runClean(action.instruction)}
                                            disabled={cleaning}
                                            style={{
                                                padding: '0.6rem 0.8rem', fontSize: '0.8rem', borderRadius: 10,
                                                display: 'flex', alignItems: 'center', gap: 8, textAlign: 'left',
                                                justifyContent: 'flex-start', transition: 'all 0.2s ease',
                                            }}>
                                            <span style={{ fontSize: '1.1rem' }}>{action.icon}</span>
                                            {action.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* NL Cleaning Input */}
                            <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                                <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-sm)', fontSize: '0.95rem' }}>🧹 Natural Language Cleaning</h3>
                                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }}>
                                    Describe any cleaning operation in plain English
                                </p>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <input className="input-field" style={{ flex: 1 }}
                                        placeholder='e.g. "rename column age to user_age", "drop rows where salary < 0"'
                                        value={instruction} onChange={e => setInstruction(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && handleCleanSubmit()}
                                        disabled={cleaning} />
                                    <button className="btn btn-primary" onClick={handleCleanSubmit}
                                        disabled={cleaning || !instruction.trim()} style={{ padding: '0.5rem 1.5rem' }}>
                                        {cleaning ? '⏳ Cleaning...' : '🧹 Clean'}
                                    </button>
                                </div>
                                {/* Suggestion chips */}
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: '0.75rem' }}>
                                    {['Drop rows where any column is empty', 'Replace negative values with 0', 'Remove outliers using IQR method', 'Normalize numeric columns to 0-1 range'].map(s => (
                                        <button key={s} onClick={() => setInstruction(s)} style={{
                                            padding: '0.25rem 0.7rem', fontSize: '0.75rem', borderRadius: 20,
                                            border: '1px solid var(--color-border)', background: 'var(--color-bg-secondary)',
                                            color: 'var(--color-text-muted)', cursor: 'pointer', transition: 'all 0.15s',
                                        }}>{s}</button>
                                    ))}
                                </div>
                            </div>

                            {/* Loading */}
                            {cleaning && (
                                <div style={{ display: 'flex', justifyContent: 'center', padding: '1.5rem' }}>
                                    <div className="spinner" /><span style={{ marginLeft: '1rem', color: 'var(--color-text-muted)' }}>Applying cleaning operation...</span>
                                </div>
                            )}

                            {/* Error */}
                            {cleanError && <div className="alert alert-error" style={{ marginBottom: 'var(--space-md)' }}>{cleanError}</div>}

                            {/* Clean Result */}
                            {cleanResult && (
                                <div className="card" style={{ borderLeft: '3px solid var(--color-success)', animation: 'fadeIn 0.3s ease' }}>
                                    <h4 style={{ color: 'var(--color-success)', marginBottom: 'var(--space-sm)', fontSize: '0.9rem' }}>✅ Cleaning Applied Successfully</h4>
                                    <div className="grid-3" style={{ gap: 'var(--space-md)', marginBottom: 'var(--space-md)' }}>
                                        <div style={{ textAlign: 'center' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>{cleanResult.before_rows}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Rows Before</div>
                                        </div>
                                        <div style={{ textAlign: 'center' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: cleanResult.rows_removed > 0 ? '#F59E0B' : 'var(--color-success)' }}>{cleanResult.rows_removed}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Rows Removed</div>
                                        </div>
                                        <div style={{ textAlign: 'center' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-success)' }}>{cleanResult.after_rows}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Rows After</div>
                                        </div>
                                    </div>
                                    <code className="history-code" style={{ display: 'block', fontSize: '0.78rem' }}>{cleanResult.generated_code}</code>

                                    {/* Preview of cleaned data */}
                                    {cleanResult.preview?.length > 0 && (
                                        <div style={{ marginTop: 'var(--space-md)' }}>
                                            <h5 style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-sm)', fontSize: '0.82rem' }}>Preview (first {cleanResult.preview.length} rows)</h5>
                                            <div className="data-table-container" style={{ maxHeight: 250, overflowY: 'auto' }}>
                                                <table className="data-table">
                                                    <thead><tr>{cleanResult.columns?.map(c => <th key={c}>{c}</th>)}</tr></thead>
                                                    <tbody>
                                                        {cleanResult.preview.map((row, ri) => (
                                                            <tr key={ri}>{cleanResult.columns?.map(c => (
                                                                <td key={c} style={{ color: row[c] === null || row[c] === undefined || row[c] === '' ? '#F59E0B' : undefined }}>
                                                                    {row[c] === null || row[c] === undefined ? '—' : String(row[c])}
                                                                </td>
                                                            ))}</tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ─── TAB: Applied Steps ────────────────── */}
                    {activeTab === 'history' && (
                        <div style={{ animation: 'fadeIn 0.3s ease' }}>
                            {history.length === 0 ? (
                                <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
                                    <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>📜</div>
                                    <h3 style={{ color: 'var(--color-text-secondary)', marginBottom: '0.5rem', fontSize: '1rem' }}>No Steps Applied Yet</h3>
                                    <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
                                        Go to the <button onClick={() => setActiveTab('clean')} style={{ color: '#D2BBFF', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600, textDecoration: 'underline' }}>Clean Data</button> tab and apply some operations.
                                    </p>
                                </div>
                            ) : (
                                <div className="card">
                                    <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                                        📜 Applied Steps ({history.length})
                                    </h3>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {history.map((step, i) => (
                                            <div key={i} style={{
                                                display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                                                padding: 'var(--space-md)', background: 'var(--color-bg-secondary)',
                                                borderRadius: 'var(--border-radius-sm)', borderLeft: '3px solid var(--color-accent)',
                                            }}>
                                                <div style={{
                                                    width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                                                    background: 'linear-gradient(135deg, #7C3AED, #A855F7)',
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    fontSize: '0.75rem', fontWeight: 700, color: '#fff',
                                                }}>{step.step}</div>
                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                    <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--color-text-primary)', marginBottom: 4 }}>
                                                        {step.instruction}
                                                    </div>
                                                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: 'var(--color-text-muted)', flexWrap: 'wrap' }}>
                                                        <span>{step.before} → {step.after} rows</span>
                                                        <span style={{ color: step.before - step.after > 0 ? '#F59E0B' : 'var(--color-success)' }}>
                                                            {step.before - step.after > 0 ? `−${step.before - step.after} removed` : 'No rows removed'}
                                                        </span>
                                                        <span>{step.time}</span>
                                                    </div>
                                                    <code className="history-code" style={{ marginTop: 6, fontSize: '0.72rem' }}>{step.code}</code>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* Empty state when no dataset selected */}
            {!datasetId && !profileLoading && (
                <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem', animation: 'fadeIn 0.5s ease',
                    background: 'linear-gradient(135deg, rgba(124,58,237,0.04), rgba(219,39,119,0.02))' }}>
                    <div style={{ fontSize: '3.5rem', marginBottom: '1rem', filter: 'drop-shadow(0 0 20px rgba(124,58,237,0.3))' }}>🧹</div>
                    <h3 style={{ color: '#E4E1E9', marginBottom: '0.75rem', fontWeight: 700, fontSize: '1.1rem' }}>Select a Dataset to Start Cleaning</h3>
                    <p style={{ color: '#958DA1', maxWidth: 400, margin: '0 auto', lineHeight: 1.6 }}>
                        Choose a dataset from the dropdown above, or <Link to="/upload" style={{ color: '#D2BBFF', fontWeight: 600 }}>upload a new one</Link> first.
                    </p>
                </div>
            )}
        </div>
    )
}

export default DataCleaning
