/**
 * ============================================================
 * InsightDisplay — Shows automated textual insights
 * ============================================================
 * Renders summary text and highlighted key findings.
 * ============================================================
 */

import React from 'react'

function InsightDisplay({ insights }) {
    if (!insights) return null

    return (
        <div className="insight-panel">
            <h4>💡 Insights</h4>
            <p style={{ marginBottom: 'var(--space-md)', fontSize: 'var(--font-size-sm)' }}>
                {insights.summary}
            </p>
            {insights.highlights && insights.highlights.length > 0 && (
                <div>
                    {insights.highlights.map((highlight, index) => (
                        <div key={index} className="insight-highlight">
                            {highlight}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default InsightDisplay
