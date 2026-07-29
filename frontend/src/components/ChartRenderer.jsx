/**
 * ============================================================
 * ChartRenderer — Renders charts based on backend recommendation
 * ============================================================
 * Supports: Bar, Line, Pie, and Table visualizations.
 * Uses Recharts library for chart rendering.
 *
 * IMPORTANT: Parent should pass a unique `key` prop to force
 * remount when data changes (prevents stale chart rendering).
 * ============================================================
 */

import React, { useMemo } from 'react'
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

// Color palette for charts
const COLORS = ['#6c63ff', '#a855f7', '#3498db', '#2ecc71', '#f1c40f', '#e74c3c', '#1abc9c', '#e67e22']

const tooltipStyle = { background: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: 8, color: '#e0e0e0' }

function ChartRenderer({ data, visualization }) {
    // Memoize data to avoid unnecessary re-renders from parent
    const chartData = useMemo(() => data, [data])

    if (!chartData || chartData.length === 0) {
        return <p style={{ color: 'var(--color-text-muted)' }}>No data to visualize.</p>
    }

    const { chart_type, x_axis, y_axis, reason } = visualization

    // ── Data Table ─────────────────────────────────────────
    if (chart_type === 'table' || !x_axis) {
        const columns = Object.keys(chartData[0] || {})
        return (
            <div className="chart-container">
                <h4 style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>📊 Data Table</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>{reason}</p>
                <div className="data-table-container">
                    <table className="data-table">
                        <thead>
                            <tr>{columns.map((col) => <th key={col}>{col}</th>)}</tr>
                        </thead>
                        <tbody>
                            {chartData.slice(0, 100).map((row, i) => (
                                <tr key={i}>
                                    {columns.map((col) => <td key={col}>{String(row[col] ?? '—')}</td>)}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        )
    }

    // ── Bar Chart ──────────────────────────────────────────
    if (chart_type === 'bar') {
        return (
            <div className="chart-container">
                <h4 style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>📊 Bar Chart</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>{reason}</p>
                <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                        <XAxis dataKey={x_axis} tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                        <YAxis tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                        <Tooltip contentStyle={tooltipStyle} />
                        <Legend />
                        <Bar dataKey={y_axis} fill="#6c63ff" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        )
    }

    // ── Line Chart ─────────────────────────────────────────
    if (chart_type === 'line') {
        return (
            <div className="chart-container">
                <h4 style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>📈 Line Chart</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>{reason}</p>
                <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                        <XAxis dataKey={x_axis} tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                        <YAxis tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                        <Tooltip contentStyle={tooltipStyle} />
                        <Legend />
                        <Line type="monotone" dataKey={y_axis} stroke="#6c63ff" strokeWidth={2} dot={{ fill: '#6c63ff' }} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        )
    }

    // ── Pie Chart ──────────────────────────────────────────
    if (chart_type === 'pie') {
        const pieData = chartData.map((item) => ({
            name: String(item[x_axis]),
            value: Number(item[y_axis]) || 0,
        }))
        return (
            <div className="chart-container">
                <h4 style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>🥧 Pie Chart</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>{reason}</p>
                <ResponsiveContainer width="100%" height={400}>
                    <PieChart>
                        <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={150} label>
                            {pieData.map((_, i) => (
                                <Cell key={i} fill={COLORS[i % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip contentStyle={tooltipStyle} />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        )
    }

    return <p>Unsupported chart type: {chart_type}</p>
}

export default ChartRenderer
