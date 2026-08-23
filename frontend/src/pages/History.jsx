/**
 * ============================================================
 * History Page — Aether AI scrollable query log with badges
 * ============================================================
 * All logic preserved: getQueryHistory() API, formatDate()
 * ============================================================
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getQueryHistory } from '../api/queries'
import { formatDate } from '../utils/helpers'

function History() {
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError]     = useState('')

    useEffect(() => { loadHistory() }, [])

    const loadHistory = async () => {
        try {
            const data = await getQueryHistory()
            setHistory(data)
        } catch (err) {
            setError('Failed to load query history')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ position: 'relative' }}>
            <div className="bg-orb bg-orb-1" />

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-sm)', flexWrap: 'wrap', gap: '1rem' }}>
                <h1 className="page-title" style={{ margin: 0 }}>Query History</h1>
                {history.length > 0 && (
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--color-border)', padding: '0.25rem 0.75rem', borderRadius: '999px' }}>
                        {history.length} queries
                    </span>
                )}
            </div>
            <p className="page-subtitle">Your last 50 AI analysis queries</p>

            {/* Loading */}
            {loading && (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
                    <div className="spinner" style={{ width: 32, height: 32 }} />
                </div>
            )}

            {/* Error */}
            {error && <div className="alert alert-error">{error}</div>}

            {/* Empty state */}
            {!loading && history.length === 0 && (
                <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📜</div>
                    <h3 style={{ color: 'var(--color-text-secondary)', fontWeight: 600, marginBottom: '0.5rem' }}>
                        No queries yet
                    </h3>
                    <p style={{ color: 'var(--color-text-muted)', maxWidth: 360, margin: '0 auto 1.5rem' }}>
                        Go to the <Link to="/query">Query page</Link> to start analysing your data with AI!
                    </p>
                    <Link to="/query" className="btn btn-primary" style={{ display: 'inline-flex' }}>
                        Run First Query →
                    </Link>
                </div>
            )}

            {/* History List */}
            {history.length > 0 && (
                <div className="history-list">
                    {history.map((item, index) => (
                        <div key={item.id} className="history-item">
                            {/* Left: number + content */}
                            <div style={{ display: 'flex', gap: '1rem', flex: 1, minWidth: 0 }}>
                                {/* Index badge */}
                                <div style={{
                                    flexShrink: 0,
                                    width: 32, height: 32,
                                    borderRadius: '50%',
                                    background: 'rgba(108,99,255,0.12)',
                                    border: '1px solid rgba(108,99,255,0.25)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: '0.75rem', fontWeight: 700, color: '#c4c0ff',
                                    marginTop: '2px'
                                }}>
                                    {index + 1}
                                </div>

                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <div className="history-query">{item.natural_query}</div>
                                    {item.generated_code && (
                                        <code className="history-code">{item.generated_code}</code>
                                    )}
                                    <div style={{ marginTop: '0.5rem' }}>
                                        <span className={`badge ${item.is_valid ? 'badge-success' : 'badge-error'}`}>
                                            {item.is_valid ? '✓ Valid' : '✗ Invalid'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Right: timestamp */}
                            <div className="history-date">
                                {formatDate(item.created_at)}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default History
