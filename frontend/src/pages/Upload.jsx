/**
 * ============================================================
 * Upload Page — Aether AI glowing drag-and-drop with schema cards
 * ============================================================
 * All API logic preserved: uploadDataset(), profile, schema display
 * ============================================================
 */

import React, { useState, useRef } from 'react'
import { uploadDataset } from '../api/datasets'

function Upload() {
    const [file, setFile]         = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [result, setResult]     = useState(null)
    const [error, setError]       = useState('')
    const fileInput = useRef(null)

    const handleDrop = (e) => {
        e.preventDefault()
        setDragOver(false)
        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile) setFile(droppedFile)
    }

    const handleUpload = async () => {
        if (!file) return
        setUploading(true); setError(''); setResult(null)
        try {
            const data = await uploadDataset(file)
            setResult(data)
        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed. Please try again.')
        } finally {
            setUploading(false)
        }
    }

    const getTypeClass = (type) => {
        const t = (type || '').toLowerCase()
        if (t === 'numeric')     return 'numeric'
        if (t === 'categorical') return 'categorical'
        if (t === 'datetime')    return 'datetime'
        return 'boolean'
    }

    return (
        <div style={{ position: 'relative' }}>
            <div className="bg-orb bg-orb-1" />

            <h1 className="page-title">Upload Dataset</h1>
            <p className="page-subtitle">Upload a CSV or Excel file to begin your AI-powered analysis</p>

            {/* ── Upload Zone ── */}
            <div
                className={`upload-zone ${dragOver ? 'dragover' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInput.current?.click()}
            >
                <div className="upload-zone-icon">
                    {file ? '✅' : '☁️'}
                </div>
                <div className="upload-zone-title">
                    {file ? file.name : 'Drag & Drop your file here'}
                </div>
                <div className="upload-zone-sub">
                    {file
                        ? `${(file.size / 1024 / 1024).toFixed(2)} MB — click to change`
                        : 'or click to browse files'
                    }
                </div>
                <div className="upload-format-badge">
                    ✓ .csv &nbsp;·&nbsp; .xlsx &nbsp;·&nbsp; .xls
                </div>
                <input
                    ref={fileInput}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    style={{ display: 'none' }}
                    onChange={(e) => setFile(e.target.files[0])}
                />
            </div>

            {/* ── Upload Button ── */}
            {file && (
                <div style={{ marginTop: 'var(--space-lg)', display: 'flex', justifyContent: 'center' }}>
                    <button
                        className="btn btn-primary"
                        onClick={handleUpload}
                        disabled={uploading}
                        style={{ padding: '0.8rem 2.5rem', fontSize: '1rem' }}
                    >
                        {uploading ? (
                            <><div className="spinner" style={{ width: 18, height: 18 }} /> Uploading & Validating...</>
                        ) : (
                            '🚀 Upload & Validate'
                        )}
                    </button>
                </div>
            )}

            {/* ── Error ── */}
            {error && (
                <div className="alert alert-error" style={{ marginTop: 'var(--space-lg)' }}>
                    ⚠ {error}
                </div>
            )}

            {/* ── Results ── */}
            {result && (
                <div style={{ marginTop: 'var(--space-xl)' }}>
                    {/* Success banner */}
                    <div className="alert alert-success" style={{ marginBottom: 'var(--space-lg)', padding: '1rem 1.5rem' }}>
                        ✅ {result.message} — Dataset ID:{' '}
                        <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1em', marginLeft: 4 }}>
                            {result.dataset_id}
                        </strong>
                        <span style={{ color: 'var(--color-text-muted)', marginLeft: 12, fontSize: '0.85rem' }}>
                            (copy this ID for queries)
                        </span>
                    </div>

                    {/* Data Profile + Schema side by side */}
                    <div className="grid-2">
                        {/* Data Profile Card */}
                        <div className="card">
                            <h3 style={{
                                color: '#c4c0ff',
                                marginBottom: 'var(--space-lg)',
                                fontSize: '0.9rem',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                letterSpacing: '0.08em',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}>
                                📊 Data Profile
                            </h3>
                            <div className="profile-grid" style={{ marginBottom: 'var(--space-lg)' }}>
                                <span className="profile-key">Rows</span>
                                <span className="profile-value">{result.profile.rows?.toLocaleString()}</span>
                                <span className="profile-key">Columns</span>
                                <span className="profile-value">{result.profile.columns}</span>
                                <span className="profile-key">Duplicate Rows</span>
                                <span className="profile-value" style={{ color: result.profile.duplicate_rows > 0 ? 'var(--color-warning)' : 'var(--color-success)' }}>
                                    {result.profile.duplicate_rows}
                                </span>
                            </div>

                            <div style={{
                                fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-text-muted)',
                                textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem'
                            }}>
                                Missing Values per Column
                            </div>
                            <div className="profile-grid">
                                {Object.entries(result.profile.missing_values || {}).map(([col, count]) => (
                                    <React.Fragment key={col}>
                                        <span className="profile-key">{col}</span>
                                        <span className="profile-value" style={{
                                            color: count > 0 ? 'var(--color-warning)' : 'var(--color-success)'
                                        }}>
                                            {count}
                                        </span>
                                    </React.Fragment>
                                ))}
                            </div>
                        </div>

                        {/* Schema Card */}
                        <div className="card">
                            <h3 style={{
                                color: '#a6e6ff',
                                marginBottom: 'var(--space-lg)',
                                fontSize: '0.9rem',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                letterSpacing: '0.08em',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}>
                                🔍 Schema
                            </h3>
                            {result.schema.columns.map((col) => (
                                <div key={col.name} className="schema-row">
                                    <span className="schema-name">{col.name}</span>
                                    <span className={`type-badge ${getTypeClass(col.semantic_type)}`}>
                                        {col.semantic_type}
                                    </span>
                                    <span className="schema-unique">{col.unique_count} unique</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Upload
