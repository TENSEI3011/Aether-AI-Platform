/**
 * ============================================================
 * Alerts — Smart alerts dashboard
 * ============================================================
 * Features:
 *   - Create alert rules (column > threshold)
 *   - Active alerts list
 *   - Notification history
 *   - Manual check trigger
 *   - Scheduled reports management
 * ============================================================
 */

import React, { useState, useCallback, useEffect } from 'react'
import { getMyDatasets, getSchema } from '../api/datasets'
import { createAlert, getAlerts, deleteAlert, checkAlerts, getNotifications } from '../api/alerts'
import { createSchedule, getSchedules, deleteSchedule } from '../api/reports'

function Alerts() {
    // State
    const [datasets, setDatasets] = useState([])
    const [alerts, setAlerts] = useState([])
    const [notifications, setNotifications] = useState([])
    const [schedules, setSchedules] = useState([])
    const [activeTab, setActiveTab] = useState('alerts')

    // Create alert form
    const [formDataset, setFormDataset] = useState('')
    const [formColumn, setFormColumn] = useState('')
    const [formCondition, setFormCondition] = useState('gt')
    const [formThreshold, setFormThreshold] = useState('')
    const [formLabel, setFormLabel] = useState('')
    const [columns, setColumns] = useState([])
    const [creating, setCreating] = useState(false)
    const [checking, setChecking] = useState(false)
    const [checkResult, setCheckResult] = useState(null)

    // Schedule form
    const [schedDataset, setSchedDataset] = useState('')
    const [schedQuery, setSchedQuery] = useState('')
    const [schedFreq, setSchedFreq] = useState('daily')
    const [schedEmail, setSchedEmail] = useState('')
    const [schedulingActive, setSchedulingActive] = useState(false)

    const [error, setError] = useState('')

    // Load data
    useEffect(() => {
        getMyDatasets().then(setDatasets).catch(() => {})
        getAlerts().then(setAlerts).catch(() => {})
        getNotifications().then(data => setNotifications(data.notifications || [])).catch(() => {})
        getSchedules().then(setSchedules).catch(() => {})
    }, [])

    // Load columns when dataset changes
    useEffect(() => {
        if (!formDataset) { setColumns([]); return }
        getSchema(formDataset)
            .then(schema => setColumns(schema.columns || []))
            .catch(() => setColumns([]))
    }, [formDataset])

    const handleCreateAlert = useCallback(async () => {
        if (!formDataset || !formColumn || !formThreshold) return
        setCreating(true)
        setError('')
        try {
            await createAlert(formDataset, formColumn, formCondition, parseFloat(formThreshold), formLabel)
            setFormColumn('')
            setFormThreshold('')
            setFormLabel('')
            const updated = await getAlerts()
            setAlerts(updated)
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create alert')
        } finally {
            setCreating(false)
        }
    }, [formDataset, formColumn, formCondition, formThreshold, formLabel])

    const handleDeleteAlert = useCallback(async (id) => {
        try {
            await deleteAlert(id)
            setAlerts(prev => prev.filter(a => a.id !== id))
        } catch { /* ignore */ }
    }, [])

    const handleCheckAlerts = useCallback(async (datasetId) => {
        setChecking(true)
        setCheckResult(null)
        try {
            const result = await checkAlerts(datasetId)
            setCheckResult(result)
            const notifs = await getNotifications()
            setNotifications(notifs.notifications || [])
        } catch (err) {
            setError(err.response?.data?.detail || 'Check failed')
        } finally {
            setChecking(false)
        }
    }, [])

    const handleCreateSchedule = useCallback(async () => {
        if (!schedDataset || !schedQuery) return
        setSchedulingActive(true)
        try {
            await createSchedule(schedDataset, schedQuery, schedFreq, schedEmail)
            setSchedQuery('')
            setSchedEmail('')
            const updated = await getSchedules()
            setSchedules(updated)
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create schedule')
        } finally {
            setSchedulingActive(false)
        }
    }, [schedDataset, schedQuery, schedFreq, schedEmail])

    const handleDeleteSchedule = useCallback(async (id) => {
        try {
            await deleteSchedule(id)
            setSchedules(prev => prev.filter(s => s.id !== id))
        } catch { /* ignore */ }
    }, [])

    const CONDITIONS = [
        { value: 'gt', label: '> Greater than' },
        { value: 'lt', label: '< Less than' },
        { value: 'gte', label: '≥ Greater or equal' },
        { value: 'lte', label: '≤ Less or equal' },
        { value: 'eq', label: '= Equal to' },
    ]

    return (
        <div>
            <h1 className="page-title">Smart Alerts & Schedules</h1>
            <p className="page-subtitle">Set up automatic monitoring and scheduled report delivery</p>

            {/* Tab Switcher */}
            <div style={{ display: 'flex', gap: '4px', marginBottom: 'var(--space-lg)' }}>
                {[
                    { value: 'alerts', label: '🔔 Alerts', count: alerts.length },
                    { value: 'schedules', label: '📧 Scheduled Reports', count: schedules.length },
                    { value: 'notifications', label: '📬 History', count: notifications.length },
                ].map(tab => (
                    <button
                        key={tab.value}
                        className={`btn ${activeTab === tab.value ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveTab(tab.value)}
                        style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                    >
                        {tab.label} ({tab.count})
                    </button>
                ))}
            </div>

            {error && <div className="alert alert-error" style={{ marginBottom: 'var(--space-md)' }}>{error}</div>}

            {/* ── Alerts Tab ──────────────────────────────────── */}
            {activeTab === 'alerts' && (
                <div>
                    {/* Create Alert Form */}
                    <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                        <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                            ➕ Create New Alert
                        </h3>
                        <div className="grid-2" style={{ marginBottom: 'var(--space-md)', gap: 'var(--space-sm)' }}>
                            <div className="input-group">
                                <label>Dataset</label>
                                <select className="input-field" value={formDataset} onChange={e => setFormDataset(e.target.value)}>
                                    <option value="">— Select —</option>
                                    {datasets.filter(d => d.in_memory).map(d => (
                                        <option key={d.dataset_id} value={d.dataset_id}>#{d.dataset_id} · {d.filename}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Column</label>
                                <select className="input-field" value={formColumn} onChange={e => setFormColumn(e.target.value)} disabled={!columns.length}>
                                    <option value="">— Select —</option>
                                    {columns.filter(c => c.semantic_type === 'numeric').map(c => (
                                        <option key={c.name} value={c.name}>{c.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="grid-2" style={{ marginBottom: 'var(--space-md)', gap: 'var(--space-sm)' }}>
                            <div className="input-group">
                                <label>Condition</label>
                                <select className="input-field" value={formCondition} onChange={e => setFormCondition(e.target.value)}>
                                    {CONDITIONS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Threshold Value</label>
                                <input className="input-field" type="number" value={formThreshold}
                                    onChange={e => setFormThreshold(e.target.value)} placeholder="e.g., 10000" />
                            </div>
                        </div>
                        <div className="input-group" style={{ marginBottom: 'var(--space-md)' }}>
                            <label>Label (optional)</label>
                            <input className="input-field" type="text" value={formLabel}
                                onChange={e => setFormLabel(e.target.value)} placeholder="e.g., Sales drop alert" />
                        </div>
                        <button className="btn btn-primary" onClick={handleCreateAlert}
                            disabled={creating || !formDataset || !formColumn || !formThreshold}>
                            {creating ? '⏳ Creating...' : '🔔 Create Alert'}
                        </button>
                    </div>

                    {/* Active Alerts */}
                    <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                        Active Alerts ({alerts.length})
                    </h3>
                    {alerts.length === 0 ? (
                        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                            No alerts configured yet. Create one above!
                        </div>
                    ) : (
                        <div style={{ display: 'grid', gap: 'var(--space-sm)' }}>
                            {alerts.map(a => (
                                <div key={a.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-sm) var(--space-md)' }}>
                                    <div>
                                        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-text-primary)' }}>
                                            {a.label || `${a.column_name} ${a.condition} ${a.threshold}`}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                                            Dataset #{a.dataset_id} · {a.column_name} {CONDITIONS.find(c => c.value === a.condition)?.label || a.condition} {a.threshold}
                                            {a.last_triggered && ` · Last triggered: ${new Date(a.last_triggered).toLocaleDateString()}`}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                                        <button className="btn btn-secondary" onClick={() => handleCheckAlerts(a.dataset_id)}
                                            disabled={checking} style={{ padding: '0.3rem 0.7rem', fontSize: '0.75rem' }}>
                                            {checking ? '⏳' : '🔍'} Check
                                        </button>
                                        <button className="btn btn-secondary" onClick={() => handleDeleteAlert(a.id)}
                                            style={{ padding: '0.3rem 0.7rem', fontSize: '0.75rem', color: '#EF4444' }}>
                                            🗑
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Check Result */}
                    {checkResult && (
                        <div className="card" style={{ marginTop: 'var(--space-md)', borderLeft: checkResult.triggered_count > 0 ? '3px solid #EF4444' : '3px solid #10B981' }}>
                            <h4 style={{ color: checkResult.triggered_count > 0 ? '#EF4444' : '#10B981', marginBottom: '0.5rem' }}>
                                {checkResult.triggered_count > 0 ? `⚠️ ${checkResult.triggered_count} Alert(s) Triggered!` : '✅ No alerts triggered'}
                            </h4>
                            {checkResult.triggered?.map((t, i) => (
                                <div key={i} style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                                    {t.message}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* ── Scheduled Reports Tab ───────────────────────── */}
            {activeTab === 'schedules' && (
                <div>
                    <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                        <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                            📧 Schedule a Report
                        </h3>
                        <div className="grid-2" style={{ marginBottom: 'var(--space-md)', gap: 'var(--space-sm)' }}>
                            <div className="input-group">
                                <label>Dataset</label>
                                <select className="input-field" value={schedDataset} onChange={e => setSchedDataset(e.target.value)}>
                                    <option value="">— Select —</option>
                                    {datasets.filter(d => d.in_memory).map(d => (
                                        <option key={d.dataset_id} value={d.dataset_id}>#{d.dataset_id} · {d.filename}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Frequency</label>
                                <select className="input-field" value={schedFreq} onChange={e => setSchedFreq(e.target.value)}>
                                    <option value="daily">Daily</option>
                                    <option value="weekly">Weekly</option>
                                    <option value="monthly">Monthly</option>
                                </select>
                            </div>
                        </div>
                        <div className="input-group" style={{ marginBottom: 'var(--space-md)' }}>
                            <label>Query to Run</label>
                            <input className="input-field" type="text" value={schedQuery}
                                onChange={e => setSchedQuery(e.target.value)} placeholder="e.g., Show average sales by region" />
                        </div>
                        <div className="input-group" style={{ marginBottom: 'var(--space-md)' }}>
                            <label>Email (for delivery)</label>
                            <input className="input-field" type="email" value={schedEmail}
                                onChange={e => setSchedEmail(e.target.value)} placeholder="your@email.com" />
                        </div>
                        <button className="btn btn-primary" onClick={handleCreateSchedule}
                            disabled={schedulingActive || !schedDataset || !schedQuery}>
                            {schedulingActive ? '⏳...' : '📧 Create Schedule'}
                        </button>
                    </div>

                    <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                        Active Schedules ({schedules.length})
                    </h3>
                    {schedules.length === 0 ? (
                        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                            No scheduled reports yet
                        </div>
                    ) : (
                        <div style={{ display: 'grid', gap: 'var(--space-sm)' }}>
                            {schedules.map(s => (
                                <div key={s.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-sm) var(--space-md)' }}>
                                    <div>
                                        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-text-primary)' }}>
                                            {s.query}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                                            Dataset #{s.dataset_id} · {s.frequency} · {s.email || 'No email'}
                                            {s.last_run && ` · Last run: ${new Date(s.last_run).toLocaleDateString()}`}
                                        </div>
                                    </div>
                                    <button className="btn btn-secondary" onClick={() => handleDeleteSchedule(s.id)}
                                        style={{ padding: '0.3rem 0.7rem', fontSize: '0.75rem', color: '#EF4444' }}>
                                        🗑
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* ── Notification History Tab ─────────────────────── */}
            {activeTab === 'notifications' && (
                <div>
                    <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                        📬 Alert History ({notifications.length})
                    </h3>
                    {notifications.length === 0 ? (
                        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                            No alert notifications yet. Create alerts and check them to generate notifications.
                        </div>
                    ) : (
                        <div style={{ display: 'grid', gap: 'var(--space-xs)' }}>
                            {notifications.map(n => (
                                <div key={n.id} className="card" style={{
                                    padding: 'var(--space-sm) var(--space-md)',
                                    borderLeft: n.is_read ? 'none' : '3px solid var(--color-accent)',
                                    opacity: n.is_read ? 0.7 : 1,
                                }}>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)' }}>{n.message}</div>
                                    <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                                        {n.created_at ? new Date(n.created_at).toLocaleString() : ''}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default Alerts
