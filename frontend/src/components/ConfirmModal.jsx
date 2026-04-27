/**
 * ============================================================
 * ConfirmModal — Reusable confirmation dialog
 * ============================================================
 * Prevents accidental destructive actions (clear all, delete).
 * Usage:
 *   <ConfirmModal
 *     open={showConfirm}
 *     title="Clear Dashboard?"
 *     message="All pinned charts will be removed."
 *     confirmLabel="Clear All"
 *     onConfirm={() => { clearPanels(); setShowConfirm(false) }}
 *     onCancel={() => setShowConfirm(false)}
 *   />
 * ============================================================
 */

import React, { useEffect } from 'react'

function ConfirmModal({ open, title, message, confirmLabel = 'Confirm', onConfirm, onCancel, danger = true }) {
    // Close on Escape key
    useEffect(() => {
        if (!open) return
        const handler = (e) => { if (e.key === 'Escape') onCancel() }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [open, onCancel])

    if (!open) return null

    return (
        <div
            style={{
                position: 'fixed',
                inset: 0,
                zIndex: 9999,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(0,0,0,0.70)',
                backdropFilter: 'blur(8px)',
                animation: 'fadeIn 0.15s ease',
            }}
            onClick={onCancel}
        >
            <div
                style={{
                    background: 'rgba(31,31,37,0.90)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(74,68,85,0.25)',
                    borderRadius: '16px',
                    padding: '2rem',
                    maxWidth: '420px',
                    width: '90%',
                    boxShadow: '0 25px 50px rgba(0,0,0,0.3), 0 0 30px rgba(124,58,237,0.08)',
                    animation: 'slideUp 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <h3 style={{
                    fontSize: '1.15rem',
                    fontWeight: 700,
                    marginBottom: '0.5rem',
                    color: '#E4E1E9',
                }}>
                    {title}
                </h3>
                <p style={{
                    fontSize: '0.9rem',
                    color: '#958DA1',
                    lineHeight: 1.6,
                    marginBottom: '1.5rem',
                }}>
                    {message}
                </p>
                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={onCancel}
                        style={{ padding: '0.55rem 1.25rem', borderRadius: '8px' }}
                    >
                        Cancel
                    </button>
                    <button
                        className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`}
                        onClick={onConfirm}
                        style={{ padding: '0.55rem 1.25rem', borderRadius: '8px' }}
                    >
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ConfirmModal
