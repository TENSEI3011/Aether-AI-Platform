/**
 * ============================================================
 * SaveQueryModal — Save a query as a reusable template
 * ============================================================
 */

import React, { useState, useCallback } from 'react'
import { saveQuery } from '../api/savedQueries'

function SaveQueryModal({ open, onClose, datasetId, query, graphType }) {
    const [name, setName] = useState('')
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState(false)

    const handleSave = useCallback(async () => {
        if (!name.trim()) {
            setError('Please enter a name for your query template.')
            return
        }
        setSaving(true)
        setError('')
        try {
            await saveQuery(name.trim(), datasetId, query, graphType)
            setSuccess(true)
            setTimeout(() => {
                setSuccess(false)
                setName('')
                onClose()
            }, 1200)
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to save query')
        } finally {
            setSaving(false)
        }
    }, [name, datasetId, query, graphType, onClose])

    if (!open) return null

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                    💾 Save Query Template
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-md)' }}>
                    Save this query for one-click re-use later.
                </p>

                <div className="input-group" style={{ marginBottom: 'var(--space-md)' }}>
                    <label>Template Name</label>
                    <input
                        className="input-field"
                        type="text"
                        value={name}
                        onChange={e => setName(e.target.value)}
                        placeholder="e.g., Monthly Sales Summary"
                        onKeyDown={e => e.key === 'Enter' && handleSave()}
                        autoFocus
                    />
                </div>

                <div className="card" style={{
                    padding: 'var(--space-sm) var(--space-md)',
                    marginBottom: 'var(--space-md)',
                    background: 'var(--color-bg-secondary)',
                    fontSize: '0.82rem',
                }}>
                    <div style={{ color: 'var(--color-text-muted)', marginBottom: '4px' }}>Query:</div>
                    <div style={{ color: 'var(--color-text-primary)' }}>{query}</div>
                </div>

                {error && <div className="alert alert-error" style={{ marginBottom: 'var(--space-sm)' }}>{error}</div>}
                {success && <div className="alert alert-info" style={{ marginBottom: 'var(--space-sm)' }}>✅ Saved successfully!</div>}

                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                    <button className="btn btn-secondary" onClick={onClose} disabled={saving}>
                        Cancel
                    </button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving || !name.trim()}>
                        {saving ? '⏳ Saving...' : '💾 Save'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default SaveQueryModal
