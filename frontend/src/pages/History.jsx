/**
 * ============================================================
 * History Page — Past query log
 * ============================================================
 * Features:
 *  - Live search filter (searches natural_query text)
 *  - Status filter (All / Valid / Invalid)
 *  - Pagination (10 items per page)
 *  - Clear all filters button
 * ============================================================
 */

import React, { useEffect, useState, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getQueryHistory } from '../api/queries'
import { formatDate } from '../utils/helpers'

const PAGE_SIZE = 10

function History() {
    const [history, setHistory]   = useState([])
    const [loading, setLoading]   = useState(true)
    const [error, setError]       = useState('')
    const [search, setSearch]     = useState('')
    const [statusFilter, setStatusFilter] = useState('all')   // 'all' | 'valid' | 'invalid'
    const [page, setPage]         = useState(1)
    const [copyToast, setCopyToast] = useState('')
    const navigate = useNavigate()

    useEffect(() => { loadHistory() }, [])

    const loadHistory = async () => {
        try {
            const data = await getQueryHistory()
            setHistory(data)
        } catch {
            setError('Failed to load query history')
        } finally {
            setLoading(false)
        }
    }

    // ── Filtered + paginated data ─────────────────────────
    const filtered = useMemo(() => {
        return history.filter((item) => {
            const matchesSearch = item.natural_query
                ?.toLowerCase()
                .includes(search.toLowerCase())
            const matchesStatus =
                statusFilter === 'all' ||
                (statusFilter === 'valid' && item.is_valid) ||
                (statusFilter === 'invalid' && !item.is_valid)
            return matchesSearch && matchesStatus
        })
    }, [history, search, statusFilter])

    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
    const paginated  = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

    const handleSearch = (e) => { setSearch(e.target.value); setPage(1) }
    const handleStatus = (s) => { setStatusFilter(s); setPage(1) }
    const clearFilters = () => { setSearch(''); setStatusFilter('all'); setPage(1) }

    const handleRerun = useCallback((query) => {
        navigate(`/query?rerun=${encodeURIComponent(query)}`)
    }, [navigate])

    const handleCopy = useCallback((text) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopyToast('Copied!')
            setTimeout(() => setCopyToast(''), 1500)
        })
    }, [])

    const hasActiveFilters = search || statusFilter !== 'all'

    return (
        <div>
            <h1 className="page-title">Query History</h1>
            <p className="page-subtitle">Your past data analysis queries</p>

            {/* ── Filter Bar ──────────────────────────────────── */}
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1.5rem', alignItems: 'center' }}>
                {/* Search */}
                <div style={{ flex: 1, minWidth: 220, position: 'relative' }}>
                    <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', fontSize: '1rem', pointerEvents: 'none' }}>🔍</span>
                    <input
                        id="history-search"
                        type="text"
                        className="form-input"
                        placeholder="Search queries..."
                        value={search}
                        onChange={handleSearch}
                        style={{ paddingLeft: '2.25rem', width: '100%' }}
                    />
                </div>

                {/* Status filter buttons */}
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {[
                        { key: 'all',     label: 'All' },
                        { key: 'valid',   label: '✓ Valid' },
                        { key: 'invalid', label: '✗ Invalid' },
                    ].map(({ key, label }) => (
                        <button
                            key={key}
                            id={`status-filter-${key}`}
                            onClick={() => handleStatus(key)}
                            style={{
                                padding: '0.4rem 1rem',
                                borderRadius: 20,
                                border: `1px solid ${statusFilter === key ? 'var(--color-accent)' : 'var(--color-border)'}`,
                                background: statusFilter === key ? 'var(--color-accent)' : 'var(--color-bg-card)',
                                color: statusFilter === key ? '#fff' : 'var(--color-text-secondary)',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                transition: 'all var(--transition-fast)',
                                fontWeight: statusFilter === key ? 600 : 400,
                            }}
                        >
                            {label}
                        </button>
                    ))}
                </div>

                {/* Clear filters */}
                {hasActiveFilters && (
                    <button
                        onClick={clearFilters}
                        style={{
                            padding: '0.4rem 0.8rem',
                            borderRadius: 20,
                            border: '1px solid var(--color-danger)',
                            background: 'transparent',
                            color: 'var(--color-danger)',
                            cursor: 'pointer',
                            fontSize: '0.82rem',
                            transition: 'all var(--transition-fast)',
                        }}
                    >
                        ✕ Clear
                    </button>
                )}

                {/* Results count */}
                <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginLeft: 'auto' }}>
                    {filtered.length} result{filtered.length !== 1 ? 's' : ''}
                </span>
            </div>

            {/* ── Loading / Error ──────────────────────────────── */}
            {loading && (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                    <div className="spinner" />
                </div>
            )}
            {error && <div className="alert alert-error">{error}</div>}

            {/* ── Empty state ──────────────────────────────────── */}
            {!loading && history.length === 0 && (
                <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                    <p style={{ color: 'var(--color-text-muted)', fontSize: '1.1rem' }}>
                        No queries yet. Go to the <a href="/query">Query page</a> to start analysing your data!
                    </p>
                </div>
            )}

            {/* ── No search results ────────────────────────────── */}
            {!loading && history.length > 0 && filtered.length === 0 && (
                <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
                    <p style={{ color: 'var(--color-text-muted)' }}>
                        No results match your filters. <button onClick={clearFilters} style={{ background: 'none', border: 'none', color: 'var(--color-accent)', cursor: 'pointer', textDecoration: 'underline' }}>Clear filters</button>
                    </p>
                </div>
            )}

            {/* ── History List ─────────────────────────────────── */}
            {paginated.length > 0 && (
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    {paginated.map((item, idx) => (
                        <div
                            key={item.id}
                            className="history-item"
                            style={{
                                borderBottom: idx < paginated.length - 1 ? '1px solid var(--color-border)' : 'none',
                                transition: 'background var(--transition-fast)',
                            }}
                        >
                            <div style={{ flex: 1 }}>
                                <div className="history-query">{item.natural_query}</div>
                                {item.generated_code && (
                                    <code className="history-code">{item.generated_code}</code>
                                )}
                                <div style={{ marginTop: '0.35rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                    <span className={`badge ${item.is_valid ? 'badge-success' : 'badge-error'}`}>
                                        {item.is_valid ? '✓ Valid' : '✗ Invalid'}
                                    </span>
                                    {item.chart_type && (
                                        <span className="badge" style={{ background: 'var(--color-bg-hover)', color: 'var(--color-text-muted)', fontSize: '0.72rem' }}>
                                            {item.chart_type}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="history-date">{formatDate(item.created_at)}</div>
                            <div style={{ display: 'flex', gap: '4px', marginTop: '6px', flexShrink: 0 }}>
                                <button
                                    className="btn btn-primary"
                                    onClick={() => handleRerun(item.natural_query)}
                                    style={{ padding: '3px 10px', fontSize: '0.72rem' }}
                                    title="Re-run this query"
                                >
                                    🔄 Re-run
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => handleCopy(item.natural_query)}
                                    style={{ padding: '3px 10px', fontSize: '0.72rem' }}
                                    title="Copy query text"
                                >
                                    📋 Copy
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* ── Pagination ───────────────────────────────────── */}
            {totalPages > 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
                    <button
                        id="page-prev"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        style={{
                            padding: '0.4rem 0.9rem',
                            borderRadius: 8,
                            border: '1px solid var(--color-border)',
                            background: 'var(--color-bg-card)',
                            color: page === 1 ? 'var(--color-text-muted)' : 'var(--color-text-primary)',
                            cursor: page === 1 ? 'not-allowed' : 'pointer',
                        }}
                    >
                        ← Prev
                    </button>

                    {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
                        .reduce((acc, p, idx, arr) => {
                            if (idx > 0 && arr[idx - 1] !== p - 1) acc.push('…')
                            acc.push(p)
                            return acc
                        }, [])
                        .map((p, i) =>
                            p === '…' ? (
                                <span key={`ellipsis-${i}`} style={{ color: 'var(--color-text-muted)', padding: '0 4px' }}>…</span>
                            ) : (
                                <button
                                    key={p}
                                    id={`page-btn-${p}`}
                                    onClick={() => setPage(p)}
                                    style={{
                                        padding: '0.4rem 0.7rem',
                                        minWidth: 36,
                                        borderRadius: 8,
                                        border: `1px solid ${page === p ? 'var(--color-accent)' : 'var(--color-border)'}`,
                                        background: page === p ? 'var(--color-accent)' : 'var(--color-bg-card)',
                                        color: page === p ? '#fff' : 'var(--color-text-secondary)',
                                        cursor: 'pointer',
                                        fontWeight: page === p ? 600 : 400,
                                    }}
                                >
                                    {p}
                                </button>
                            )
                        )
                    }

                    <button
                        id="page-next"
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        style={{
                            padding: '0.4rem 0.9rem',
                            borderRadius: 8,
                            border: '1px solid var(--color-border)',
                            background: 'var(--color-bg-card)',
                            color: page === totalPages ? 'var(--color-text-muted)' : 'var(--color-text-primary)',
                            cursor: page === totalPages ? 'not-allowed' : 'pointer',
                        }}
                    >
                        Next →
                    </button>

                    <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginLeft: 8 }}>
                        Page {page} of {totalPages}
                    </span>
                </div>
            )}


            {/* Copy toast notification */}
            {copyToast && (
                <div style={{
                    position: 'fixed', bottom: 24, right: 24,
                    background: 'var(--color-accent)', color: '#fff',
                    padding: '0.6rem 1.25rem', borderRadius: 8,
                    fontSize: '0.85rem', fontWeight: 600,
                    boxShadow: 'var(--shadow-md)',
                    zIndex: 9999,
                    animation: 'fadeIn 0.2s ease',
                }}>
                    ✓ {copyToast}
                </div>
            )}
        </div>
    )
}

export default History
