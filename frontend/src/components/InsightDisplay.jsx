/**
 * ============================================================
 * InsightDisplay — AI-powered insights, narration & suggestions
 * ============================================================
 * Renders:
 *  1. AI Narration  — Gemini-generated prose summary
 *  2. Key Highlights — Statistical bullets from insight_generator
 *  3. Suggested Queries — Clickable follow-up question chips
 * ============================================================
 */

import React, { useState } from 'react'

function InsightDisplay({ insights, narration, suggestions, onSuggestionClick }) {
    const [showAllHighlights, setShowAllHighlights] = useState(false)

    if (!insights && !narration && !suggestions?.length) return null

    const highlights = insights?.highlights || []
    const visibleHighlights = showAllHighlights ? highlights : highlights.slice(0, 3)

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

            {/* ── AI Narration ─────────────────────────────────── */}
            {narration && (
                <div className="card" style={{
                    borderLeft: '3px solid var(--color-accent)',
                    background: 'linear-gradient(135deg, var(--color-bg-card) 0%, var(--color-bg-secondary) 100%)',
                    position: 'relative',
                    overflow: 'hidden',
                }}>
                    {/* Decorative glow */}
                    <div style={{
                        position: 'absolute', top: 0, right: 0, width: 120, height: 120,
                        background: 'radial-gradient(circle, var(--color-accent-glow) 0%, transparent 70%)',
                        pointerEvents: 'none',
                    }} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
                        <span style={{ fontSize: '1.1rem' }}>🤖</span>
                        <h4 style={{ margin: 0, color: 'var(--color-accent)', fontSize: '0.95rem', fontWeight: 700 }}>
                            AI Narrative
                        </h4>
                        <span style={{
                            marginLeft: 'auto', fontSize: '0.65rem', padding: '2px 8px',
                            background: 'var(--color-accent-glow)', color: 'var(--color-accent)',
                            borderRadius: 20, fontWeight: 600, letterSpacing: '0.05em',
                        }}>GEMINI</span>
                    </div>
                    <p style={{
                        margin: 0, fontSize: '0.9rem', lineHeight: 1.65,
                        color: 'var(--color-text-primary)', fontStyle: 'italic',
                    }}>
                        "{narration}"
                    </p>
                </div>
            )}

            {/* ── Statistical Highlights ───────────────────────── */}
            {highlights.length > 0 && (
                <div className="insight-panel">
                    <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span>💡</span> Key Insights
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 400, marginLeft: 4 }}>
                            {insights?.summary}
                        </span>
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                        {visibleHighlights.map((h, i) => (
                            <div key={i} className="insight-highlight">
                                <span style={{ color: 'var(--color-accent)', marginRight: 6, fontSize: '0.8rem' }}>▸</span>
                                {h}
                            </div>
                        ))}
                    </div>
                    {highlights.length > 3 && (
                        <button
                            onClick={() => setShowAllHighlights((v) => !v)}
                            style={{
                                marginTop: '0.5rem', background: 'none', border: 'none',
                                color: 'var(--color-accent)', cursor: 'pointer',
                                fontSize: '0.8rem', padding: '2px 0',
                                textDecoration: 'underline',
                            }}
                        >
                            {showAllHighlights ? '▲ Show less' : `▼ Show ${highlights.length - 3} more`}
                        </button>
                    )}
                </div>
            )}

            {/* ── Suggested Follow-up Queries ──────────────────── */}
            {suggestions?.length > 0 && (
                <div className="card" style={{ padding: '1rem 1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '1rem' }}>💬</span>
                        <h4 style={{ margin: 0, fontSize: '0.9rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                            Suggested Follow-up Queries
                        </h4>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {suggestions.map((s, i) => (
                            <button
                                key={i}
                                id={`suggestion-${i}`}
                                onClick={() => onSuggestionClick?.(s)}
                                title="Click to run this query"
                                style={{
                                    padding: '0.45rem 0.9rem',
                                    borderRadius: 20,
                                    border: '1px solid var(--color-border)',
                                    background: 'var(--color-bg-secondary)',
                                    color: 'var(--color-text-secondary)',
                                    cursor: 'pointer',
                                    fontSize: '0.82rem',
                                    transition: 'all var(--transition-fast)',
                                    textAlign: 'left',
                                    maxWidth: 360,
                                    lineHeight: 1.4,
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.borderColor = 'var(--color-accent)'
                                    e.currentTarget.style.color = 'var(--color-accent)'
                                    e.currentTarget.style.background = 'var(--color-accent-glow)'
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.borderColor = 'var(--color-border)'
                                    e.currentTarget.style.color = 'var(--color-text-secondary)'
                                    e.currentTarget.style.background = 'var(--color-bg-secondary)'
                                }}
                            >
                                <span style={{ color: 'var(--color-accent)', marginRight: 5 }}>→</span>
                                {s}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default InsightDisplay
