/**
 * ============================================================
 * ChatSidebar — Floating AI Chat Assistant
 * ============================================================
 * Global floating chat panel with:
 *   - Collapsible bubble (bottom-right)
 *   - Message history with markdown-style formatting
 *   - Dataset-aware context with selector
 *   - Typing animation
 * ============================================================
 */

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { sendChatMessage } from '../api/chat'
import axiosClient from '../api/axiosClient'
import { useAuth } from '../hooks/useAuth'

function ChatSidebar() {
    const { user } = useAuth()
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! 👋 I\'m your AI data analyst assistant. Select a dataset below and I can suggest real queries, explain your data, and help you explore!' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [sessionId] = useState(() => `chat_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`)
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    // Dataset awareness
    const [datasets, setDatasets] = useState([])
    const [selectedDataset, setSelectedDataset] = useState('')

    // Fetch user datasets when chat opens
    useEffect(() => {
        if (isOpen && user) {
            axiosClient.get('/chat/datasets')
                .then(res => {
                    const ds = res.data.datasets || []
                    setDatasets(ds)
                    // Auto-select first dataset if none selected
                    if (ds.length > 0 && !selectedDataset) {
                        setSelectedDataset(ds[0].dataset_id)
                    }
                })
                .catch(() => {})
        }
    }, [isOpen, user])

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen) inputRef.current?.focus()
    }, [isOpen])

    const handleSend = useCallback(async () => {
        if (!input.trim() || loading) return

        const userMsg = input.trim()
        setInput('')
        setMessages(prev => [...prev, { role: 'user', content: userMsg }])
        setLoading(true)

        try {
            const data = await sendChatMessage(userMsg, sessionId, selectedDataset || null)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.response || 'I apologize, I could not generate a response.',
            }])
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '⚠️ Connection error. Please try again.',
            }])
        } finally {
            setLoading(false)
        }
    }, [input, loading, sessionId, selectedDataset])

    const handleKeyDown = useCallback((e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }, [handleSend])

    // Quick action buttons
    const quickActions = [
        '💡 Suggest queries',
        '📊 Show columns',
        '🔍 Find outliers',
    ]

    const handleQuickAction = (action) => {
        const actionMap = {
            '💡 Suggest queries': 'Suggest some analysis queries for my dataset',
            '📊 Show columns': 'What columns does my dataset have?',
            '🔍 Find outliers': 'How can I detect outliers in my data?',
        }
        setInput(actionMap[action] || action)
    }

    // Don't render if not logged in
    if (!user) return null

    const selectedName = datasets.find(d => d.dataset_id === selectedDataset)?.filename || ''

    return (
        <>
            {/* Floating Chat Bubble */}
            <button
                id="chat-bubble"
                className="chat-bubble"
                onClick={() => setIsOpen(v => !v)}
                title="AI Chat Assistant"
            >
                {isOpen ? '✕' : '🤖'}
            </button>

            {/* Chat Panel */}
            {isOpen && (
                <div className="chat-panel">
                    {/* Header */}
                    <div className="chat-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontSize: '1.2rem' }}>🧠</span>
                            <div>
                                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>AI Assistant</div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
                                    {loading ? '● Typing...' : '● Online'}
                                </div>
                            </div>
                        </div>
                        <button
                            className="btn-icon"
                            onClick={() => setIsOpen(false)}
                            style={{ color: 'var(--color-text-muted)' }}
                        >
                            ✕
                        </button>
                    </div>

                    {/* Dataset Selector */}
                    {datasets.length > 0 && (
                        <div style={{
                            padding: '0.4rem 0.75rem',
                            borderBottom: '1px solid var(--color-border, rgba(255,255,255,0.08))',
                            background: 'rgba(255,255,255,0.02)',
                        }}>
                            <select
                                value={selectedDataset}
                                onChange={e => setSelectedDataset(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.35rem 0.5rem',
                                    fontSize: '0.75rem',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-border, rgba(255,255,255,0.12))',
                                    background: 'var(--color-surface, #1a1a2e)',
                                    color: 'var(--color-text, #e0e0e0)',
                                    cursor: 'pointer',
                                }}
                            >
                                <option value="">— Select Dataset —</option>
                                {datasets.map(d => (
                                    <option key={d.dataset_id} value={d.dataset_id}>
                                        📄 {d.filename}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    {/* Quick Actions */}
                    {messages.length <= 2 && (
                        <div style={{
                            padding: '0.4rem 0.75rem',
                            display: 'flex',
                            gap: '0.35rem',
                            flexWrap: 'wrap',
                        }}>
                            {quickActions.map(action => (
                                <button
                                    key={action}
                                    onClick={() => handleQuickAction(action)}
                                    style={{
                                        fontSize: '0.7rem',
                                        padding: '0.25rem 0.5rem',
                                        borderRadius: '12px',
                                        border: '1px solid var(--color-border, rgba(255,255,255,0.12))',
                                        background: 'rgba(99, 102, 241, 0.1)',
                                        color: 'var(--color-primary, #818cf8)',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                    }}
                                    onMouseEnter={e => e.target.style.background = 'rgba(99, 102, 241, 0.2)'}
                                    onMouseLeave={e => e.target.style.background = 'rgba(99, 102, 241, 0.1)'}
                                >
                                    {action}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Messages */}
                    <div className="chat-messages">
                        {messages.map((msg, i) => (
                            <div key={i} className={`chat-msg ${msg.role}`}>
                                <div className="chat-msg-bubble">
                                    {msg.content.split('\n').map((line, j) => (
                                        <React.Fragment key={j}>
                                            {line.startsWith('•') || line.startsWith('-') ? (
                                                <div style={{ paddingLeft: '0.5rem', marginBottom: '2px' }}>{line}</div>
                                            ) : line.startsWith('**') ? (
                                                <strong>{line.replace(/\*\*/g, '')}</strong>
                                            ) : (
                                                <span>{line}</span>
                                            )}
                                            {j < msg.content.split('\n').length - 1 && <br />}
                                        </React.Fragment>
                                    ))}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="chat-msg assistant">
                                <div className="chat-msg-bubble chat-typing">
                                    <span className="typing-dot" />
                                    <span className="typing-dot" />
                                    <span className="typing-dot" />
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <div className="chat-input-area">
                        <input
                            ref={inputRef}
                            className="chat-input"
                            type="text"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={selectedName ? `Ask about ${selectedName}...` : 'Ask me anything...'}
                            disabled={loading}
                        />
                        <button
                            className="chat-send-btn"
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                        >
                            ➤
                        </button>
                    </div>
                </div>
            )}
        </>
    )
}

export default ChatSidebar
