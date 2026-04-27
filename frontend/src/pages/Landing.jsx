/**
 * ============================================================
 * Landing Page — Aether Intelligence
 * ============================================================
 * Premium public-facing hero page with glassmorphic feature
 * cards, gradient accents, ambient orbs, and clear CTAs.
 * Redesigned using Stitch MCP "Aether Flow" design system.
 * ============================================================
 */

import React from 'react'
import { Link } from 'react-router-dom'

const FEATURES = [
    {
        icon: '🧠',
        title: 'Natural Language Queries',
        desc: 'Ask anything about your data and get answers in seconds — no SQL or code needed.',
        gradient: 'linear-gradient(135deg, rgba(124,58,237,0.15), rgba(168,85,247,0.08))',
    },
    {
        icon: '📊',
        title: 'Auto-Visualization',
        desc: 'AI automatically selects the best chart type and generates beautiful, interactive visualizations.',
        gradient: 'linear-gradient(135deg, rgba(59,130,246,0.12), rgba(124,58,237,0.08))',
    },
    {
        icon: '🎙️',
        title: 'Voice Input & Output',
        desc: 'Talk to your data naturally with advanced voice recognition and AI-narrated insights.',
        gradient: 'linear-gradient(135deg, rgba(219,39,119,0.12), rgba(124,58,237,0.08))',
    },
    {
        icon: '📈',
        title: 'Predictive Forecasting',
        desc: 'Predict future trends using built-in ML models — linear regression and moving averages.',
        gradient: 'linear-gradient(135deg, rgba(16,185,129,0.12), rgba(124,58,237,0.08))',
    },
    {
        icon: '🔗',
        title: 'Multi-Dataset Joins',
        desc: 'Seamlessly combine data from multiple sources with natural language JOIN operations.',
        gradient: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(124,58,237,0.08))',
    },
    {
        icon: '🛡️',
        title: 'Secure & Sandboxed',
        desc: 'All AI-generated code passes AST-level validation. Your data is encrypted and private.',
        gradient: 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(124,58,237,0.08))',
    },
]

const STATS = [
    { value: '10K+', label: 'Queries Processed' },
    { value: '99.9%', label: 'Uptime' },
    { value: '< 2s', label: 'Response Time' },
]

function Landing() {
    return (
        <div style={{ minHeight: '85vh', position: 'relative' }}>
            {/* ── Ambient Background Orbs ─────────────────── */}
            <div style={{
                position: 'absolute',
                top: '-150px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '800px',
                height: '600px',
                background: 'radial-gradient(ellipse, rgba(124,58,237,0.10) 0%, transparent 70%)',
                filter: 'blur(80px)',
                pointerEvents: 'none',
                zIndex: 0,
            }} />

            {/* ── Hero Section ─────────────────────────────── */}
            <div style={{
                textAlign: 'center',
                padding: '5rem 1.5rem 3rem',
                maxWidth: '780px',
                margin: '0 auto',
                position: 'relative',
                zIndex: 1,
            }}>
                {/* Glowing chip */}
                <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 1rem',
                    borderRadius: '9999px',
                    background: 'rgba(124,58,237,0.10)',
                    border: '1px solid rgba(124,58,237,0.20)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: '#D2BBFF',
                    marginBottom: '1.5rem',
                    animation: 'fadeIn 0.6s ease',
                    backdropFilter: 'blur(10px)',
                }}>
                    <span style={{ fontSize: '1rem' }}>✨</span>
                    Powered by Generative AI
                </div>

                <h1 style={{
                    fontSize: 'clamp(2.2rem, 5vw, 3.5rem)',
                    fontWeight: 900,
                    lineHeight: 1.08,
                    letterSpacing: '-0.03em',
                    marginBottom: '1.25rem',
                    background: 'linear-gradient(135deg, #D2BBFF, #A855F7, #DB2777)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    animation: 'fadeIn 0.8s ease',
                }}>
                    AI-Powered Data Analysis
                    <br />
                    for Everyone
                </h1>

                <p style={{
                    fontSize: '1.1rem',
                    color: '#958DA1',
                    lineHeight: 1.7,
                    marginBottom: '2.5rem',
                    animation: 'fadeIn 1s ease',
                    maxWidth: '600px',
                    margin: '0 auto 2.5rem',
                }}>
                    Upload your datasets and ask questions in plain English.
                    Get instant charts, insights, forecasts, and AI narration —
                    no technical skills required.
                </p>

                <div style={{
                    display: 'flex',
                    gap: '0.75rem',
                    justifyContent: 'center',
                    flexWrap: 'wrap',
                    animation: 'fadeIn 1.2s ease',
                }}>
                    <Link to="/register" className="btn btn-primary" style={{
                        padding: '0.9rem 2.25rem',
                        fontSize: '1rem',
                        borderRadius: '12px',
                        fontWeight: 700,
                    }}>
                        🚀 Get Started Free
                    </Link>
                    <Link to="/login" className="btn btn-secondary" style={{
                        padding: '0.9rem 2.25rem',
                        fontSize: '1rem',
                        borderRadius: '12px',
                    }}>
                        Sign In
                    </Link>
                </div>
            </div>

            {/* ── Stats Row ──────────────────────────────── */}
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '3rem',
                padding: '2rem 1.5rem 3rem',
                animation: 'fadeIn 1.4s ease',
            }}>
                {STATS.map((s, i) => (
                    <div key={i} style={{ textAlign: 'center' }}>
                        <div style={{
                            fontSize: '1.75rem',
                            fontWeight: 800,
                            letterSpacing: '-0.02em',
                            background: 'linear-gradient(135deg, #7C3AED, #FFB1C7)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text',
                        }}>
                            {s.value}
                        </div>
                        <div style={{
                            fontSize: '0.8rem',
                            color: '#958DA1',
                            fontWeight: 500,
                            marginTop: '4px',
                        }}>
                            {s.label}
                        </div>
                    </div>
                ))}
            </div>

            {/* ── Feature Grid ────────────────────────────── */}
            <div style={{
                maxWidth: '960px',
                margin: '0 auto',
                padding: '0 1.5rem 3rem',
            }}>
                <h2 style={{
                    textAlign: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 800,
                    letterSpacing: '-0.02em',
                    marginBottom: '0.5rem',
                    color: '#E4E1E9',
                }}>
                    Everything you need to analyse data
                </h2>
                <p style={{
                    textAlign: 'center',
                    color: '#958DA1',
                    fontSize: '0.95rem',
                    marginBottom: '2rem',
                }}>
                    A complete AI-powered analytics toolkit at your fingertips
                </p>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                    gap: '1rem',
                }}>
                    {FEATURES.map((f, i) => (
                        <div
                            key={i}
                            className="card"
                            style={{
                                padding: '1.75rem',
                                animation: `fadeIn ${0.4 + i * 0.12}s ease`,
                                background: f.gradient,
                                borderColor: 'rgba(74,68,85,0.15)',
                            }}
                        >
                            <div style={{
                                width: '44px',
                                height: '44px',
                                borderRadius: '10px',
                                background: 'rgba(124,58,237,0.12)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '1.4rem',
                                marginBottom: '1rem',
                            }}>
                                {f.icon}
                            </div>
                            <h3 style={{
                                fontSize: '0.95rem',
                                fontWeight: 700,
                                marginBottom: '0.5rem',
                                color: '#E4E1E9',
                            }}>
                                {f.title}
                            </h3>
                            <p style={{
                                fontSize: '0.85rem',
                                color: '#958DA1',
                                lineHeight: 1.6,
                            }}>
                                {f.desc}
                            </p>
                        </div>
                    ))}
                </div>
            </div>

            {/* ── Bottom CTA ──────────────────────────────── */}
            <div style={{
                textAlign: 'center',
                padding: '2.5rem 1.5rem',
                background: 'linear-gradient(135deg, rgba(124,58,237,0.06), rgba(219,39,119,0.04))',
                border: '1px solid rgba(124,58,237,0.10)',
                borderRadius: '16px',
                maxWidth: '720px',
                margin: '1rem auto 3rem',
                backdropFilter: 'blur(10px)',
                position: 'relative',
                overflow: 'hidden',
            }}>
                {/* Glow line */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: '10%',
                    right: '10%',
                    height: '1px',
                    background: 'linear-gradient(90deg, transparent, rgba(124,58,237,0.5), transparent)',
                }} />

                <h3 style={{
                    fontSize: '1.4rem',
                    fontWeight: 800,
                    letterSpacing: '-0.02em',
                    marginBottom: '0.5rem',
                    color: '#E4E1E9',
                }}>
                    Ready to transform your data?
                </h3>
                <p style={{
                    color: '#958DA1',
                    marginBottom: '1.5rem',
                    fontSize: '0.95rem',
                }}>
                    Upload a CSV, ask a question, and get insights in seconds.
                </p>
                <Link to="/register" className="btn btn-primary" style={{
                    padding: '0.85rem 2.5rem',
                    fontSize: '1rem',
                    borderRadius: '12px',
                    fontWeight: 700,
                }}>
                    Create Free Account
                </Link>
            </div>
        </div>
    )
}

export default Landing
