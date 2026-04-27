/**
 * ============================================================
 * Upload Page — Aether Flow Design
 * ============================================================
 * Premium drag-and-drop upload with glassmorphic zone,
 * animated success states, and polished results display.
 * ============================================================
 */

import React, { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { uploadDataset } from '../api/datasets'

function Upload() {
    const [file, setFile] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')
    const fileInput = useRef(null)

    const handleDrop = (e) => {
        e.preventDefault()
        setDragOver(false)
        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile) setFile(droppedFile)
    }

    const handleUpload = async () => {
        if (!file) return
        setUploading(true)
        setError('')
        setResult(null)
        try {
            const data = await uploadDataset(file)
            setResult(data)
            // Gap 18: Reset file state after successful upload
            setFile(null)
            if (fileInput.current) fileInput.current.value = ''
        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed')
        } finally {
            setUploading(false)
        }
    }

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    return (
        <div>
            <h1 className="page-title" style={{ animation: 'fadeIn 0.4s ease' }}>Upload Dataset</h1>
            <p className="page-subtitle" style={{ animation: 'fadeIn 0.6s ease' }}>
                Upload a CSV or Excel file for AI-powered analysis
            </p>

            {/* Upload Zone */}
            <div
                className={`upload-zone ${dragOver ? 'dragover' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInput.current?.click()}
                style={{ animation: 'fadeIn 0.5s ease' }}
            >
                <div className="upload-icon">
                    {file ? '📄' : '📂'}
                </div>
                <p style={{
                    fontSize: '1.1rem',
                    marginBottom: '0.5rem',
                    fontWeight: 600,
                    color: file ? '#D2BBFF' : '#E4E1E9',
                }}>
                    {file ? file.name : 'Drag & drop your file here'}
                </p>
                {file ? (
                    <p style={{ color: '#958DA1', fontSize: '0.85rem' }}>
                        {formatFileSize(file.size)} • Click to change
                    </p>
                ) : (
                    <p style={{ color: '#958DA1', fontSize: '0.85rem' }}>
                        or click to browse — supports <span style={{ color: '#D2BBFF' }}>.csv</span>, <span style={{ color: '#D2BBFF' }}>.xlsx</span>, <span style={{ color: '#D2BBFF' }}>.xls</span>
                    </p>
                )}
                <input
                    ref={fileInput}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    style={{ display: 'none' }}
                    onChange={(e) => setFile(e.target.files[0])}
                />
            </div>

            {/* Upload Button */}
            {file && (
                <div style={{
                    marginTop: 'var(--space-lg)',
                    textAlign: 'center',
                    animation: 'fadeIn 0.3s ease',
                }}>
                    <button
                        className="btn btn-primary"
                        onClick={handleUpload}
                        disabled={uploading}
                        style={{
                            padding: '0.85rem 2.5rem',
                            fontSize: '1rem',
                            borderRadius: '12px',
                        }}
                    >
                        {uploading ? (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span className="spinner" style={{ width: 18, height: 18 }} />
                                Uploading & Validating...
                            </span>
                        ) : '🚀 Upload & Validate'}
                    </button>
                </div>
            )}

            {/* Error */}
            {error && (
                <div className="alert alert-error" style={{ marginTop: 'var(--space-lg)', animation: 'fadeIn 0.3s ease' }}>
                    {error}
                </div>
            )}

            {/* Results */}
            {result && (
                <div style={{ marginTop: 'var(--space-xl)', animation: 'fadeIn 0.4s ease' }}>
                    <div className="alert alert-success">
                        ✅ {result.message} — Dataset ID: <strong style={{ color: '#10B981' }}>{result.dataset_id}</strong>
                    </div>

                    {/* Quick action buttons */}
                    <div style={{
                        display: 'flex', gap: '0.75rem', marginTop: 'var(--space-md)',
                        justifyContent: 'center', flexWrap: 'wrap',
                    }}>
                        <Link
                            to={`/query?dataset=${result.dataset_id}`}
                            className="btn btn-primary"
                            style={{
                                padding: '0.65rem 1.5rem',
                                fontSize: '0.9rem',
                                borderRadius: '10px',
                                textDecoration: 'none',
                            }}
                        >
                            🔍 Query This Dataset
                        </Link>
                        <Link
                            to="/profile"
                            className="btn btn-secondary"
                            style={{
                                padding: '0.65rem 1.5rem',
                                fontSize: '0.9rem',
                                borderRadius: '10px',
                                textDecoration: 'none',
                            }}
                        >
                            📊 View Data Profile
                        </Link>
                        <Link
                            to={`/cleaning?dataset=${result.dataset_id}`}
                            className="btn btn-secondary"
                            style={{
                                padding: '0.65rem 1.5rem',
                                fontSize: '0.9rem',
                                borderRadius: '10px',
                                textDecoration: 'none',
                            }}
                        >
                            🧹 Clean Data
                        </Link>
                        <button
                            className="btn btn-secondary"
                            onClick={() => { setResult(null); setError('') }}
                            style={{
                                padding: '0.65rem 1.5rem',
                                fontSize: '0.9rem',
                                borderRadius: '10px',
                            }}
                        >
                            📁 Upload Another
                        </button>
                    </div>

                    <div className="grid-2" style={{ marginTop: 'var(--space-xl)' }}>
                        {/* Data Profile */}
                        <div className="card">
                            <h3 style={{
                                background: 'linear-gradient(135deg, #7C3AED, #A855F7)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text',
                                fontWeight: 700,
                                marginBottom: 'var(--space-md)',
                            }}>
                                📊 Data Profile
                            </h3>
                            <div className="profile-grid">
                                <span className="profile-key">Rows</span>
                                <span className="profile-value">{result.profile.rows?.toLocaleString()}</span>
                                <span className="profile-key">Columns</span>
                                <span className="profile-value">{result.profile.columns}</span>
                                <span className="profile-key">Duplicate Rows</span>
                                <span className="profile-value">{result.profile.duplicate_rows}</span>
                            </div>

                            <h4 style={{
                                marginTop: 'var(--space-lg)',
                                marginBottom: 'var(--space-sm)',
                                fontSize: '0.8rem',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                letterSpacing: '0.06em',
                                color: '#958DA1',
                            }}>
                                Missing Values
                            </h4>
                            <div className="profile-grid">
                                {Object.entries(result.profile.missing_values || {}).map(([col, count]) => (
                                    <React.Fragment key={col}>
                                        <span className="profile-key">{col}</span>
                                        <span className="profile-value" style={{
                                            color: count > 0 ? '#F59E0B' : '#10B981',
                                        }}>
                                            {count}
                                        </span>
                                    </React.Fragment>
                                ))}
                            </div>
                        </div>

                        {/* Schema */}
                        <div className="card">
                            <h3 style={{
                                background: 'linear-gradient(135deg, #7C3AED, #A855F7)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text',
                                fontWeight: 700,
                                marginBottom: 'var(--space-md)',
                            }}>
                                🔍 Schema
                            </h3>
                            {result.schema.columns.map((col, i) => (
                                <div key={col.name} style={{
                                    padding: '0.65rem 0',
                                    borderBottom: i < result.schema.columns.length - 1
                                        ? '1px solid rgba(74,68,85,0.15)'
                                        : 'none',
                                    fontSize: '0.85rem',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                }}>
                                    <strong style={{ color: '#E4E1E9' }}>{col.name}</strong>
                                    <span className="badge" style={{
                                        background: 'rgba(124,58,237,0.12)',
                                        color: '#D2BBFF',
                                        fontSize: '0.65rem',
                                    }}>
                                        {col.semantic_type}
                                    </span>
                                    <span style={{
                                        color: '#958DA1',
                                        marginLeft: 'auto',
                                        fontSize: '0.75rem',
                                    }}>
                                        {col.unique_count} unique
                                    </span>
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
