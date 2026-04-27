/**
 * ============================================================
 * ErrorBoundary — Catches React rendering errors gracefully
 * ============================================================
 * Prevents the entire app from crashing to a white screen.
 * Shows a friendly error message with a retry button.
 * ============================================================
 */

import React from 'react'

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, errorInfo) {
        console.error('ErrorBoundary caught:', error, errorInfo)
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null })
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '60vh',
                    padding: '2rem',
                    textAlign: 'center',
                }}>
                    <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚠️</div>
                    <h2 style={{
                        fontSize: '1.5rem',
                        fontWeight: 700,
                        marginBottom: '0.75rem',
                        color: 'var(--color-text-primary)',
                    }}>
                        Something went wrong
                    </h2>
                    <p style={{
                        color: 'var(--color-text-secondary)',
                        marginBottom: '1.5rem',
                        maxWidth: '400px',
                        lineHeight: 1.6,
                    }}>
                        An unexpected error occurred. Try refreshing the page or click the button below.
                    </p>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <button
                            className="btn btn-primary"
                            onClick={this.handleRetry}
                            style={{ padding: '0.6rem 1.5rem' }}
                        >
                            🔄 Try Again
                        </button>
                        <button
                            className="btn btn-secondary"
                            onClick={() => window.location.href = '/dashboard'}
                            style={{ padding: '0.6rem 1.5rem' }}
                        >
                            🏠 Go Home
                        </button>
                    </div>
                    {this.state.error && (
                        <details style={{
                            marginTop: '2rem',
                            padding: '1rem',
                            background: 'var(--color-bg-secondary)',
                            border: '1px solid var(--color-border)',
                            borderRadius: '8px',
                            fontSize: '0.8rem',
                            color: 'var(--color-text-muted)',
                            maxWidth: '500px',
                            textAlign: 'left',
                        }}>
                            <summary style={{ cursor: 'pointer', marginBottom: '0.5rem' }}>
                                Error details
                            </summary>
                            <code style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                                {this.state.error.toString()}
                            </code>
                        </details>
                    )}
                </div>
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary
