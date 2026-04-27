/**
 * ============================================================
 * ChartRenderer — Renders charts based on backend recommendation
 * ============================================================
 * Supports: Bar, Line, Pie, Table, Scatter, Histogram, Heatmap
 * Uses Recharts library. Highlights anomalous data points.
 * Parent passes a unique `key` to force remount on new queries.
 * ============================================================
 */

import React, { useMemo } from 'react'
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    ScatterChart, Scatter, ZAxis,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    ReferenceDot,
} from 'recharts'

const COLORS = ['#6c63ff', '#a855f7', '#3498db', '#2ecc71', '#f1c40f', '#e74c3c', '#1abc9c', '#e67e22']
const tooltipStyle = { background: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: 8, color: '#e0e0e0' }

// ── Histogram: bucket values into bins ─────────────────────
function buildHistogramBins(data, column, binCount = 15) {
    const values = data.map((d) => Number(d[column])).filter((v) => !isNaN(v))
    if (values.length === 0) return []
    const min = Math.min(...values)
    const max = Math.max(...values)
    const binWidth = (max - min) / binCount || 1
    const bins = Array.from({ length: binCount }, (_, i) => ({
        range: `${(min + i * binWidth).toFixed(1)}–${(min + (i + 1) * binWidth).toFixed(1)}`,
        count: 0,
    }))
    values.forEach((v) => {
        const idx = Math.min(Math.floor((v - min) / binWidth), binCount - 1)
        bins[idx].count++
    })
    return bins
}

// ── Heatmap: map a value to a blue→purple→red gradient ─────
function heatColor(value, min, max) {
    const ratio = max === min ? 0.5 : (value - min) / (max - min)
    if (ratio >= 0.5) {
        const t = (ratio - 0.5) * 2
        return `rgb(${Math.round(108 + 123 * t)},${Math.round(99 - 99 * t)},${Math.round(255 - 213 * t)})`
    }
    const t = ratio * 2
    return `rgb(${Math.round(52 + 56 * t)},${Math.round(152 - 53 * t)},${Math.round(219 + 36 * t)})`
}

// ── Shared chart title helper ───────────────────────────────
function ChartTitle({ icon, label, reason }) {
    return (
        <div style={{ marginBottom: '1rem' }}>
            <h4 style={{ color: 'var(--color-text-secondary)', margin: 0 }}>{icon} {label}</h4>
            {reason && <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', margin: '4px 0 0' }}>{reason}</p>}
        </div>
    )
}

function ChartRenderer({ data, visualization, anomalies }) {
    const chartData = useMemo(() => data, [data])

    const anomalyIndices = useMemo(() => {
        if (!anomalies?.anomaly_indices || !visualization?.y_axis) return new Set()
        return new Set(anomalies.anomaly_indices[visualization.y_axis] || [])
    }, [anomalies, visualization])

    const anomalyDots = useMemo(() => {
        if (!visualization?.x_axis || !visualization?.y_axis || anomalyIndices.size === 0) return []
        return chartData
            .filter((_, i) => anomalyIndices.has(i))
            .map((item, i) => ({
                key: `a-${i}`,
                x: item[visualization.x_axis],
                y: Number(item[visualization.y_axis]) || 0,
            }))
    }, [chartData, anomalyIndices, visualization])

    if (!chartData || chartData.length === 0) {
        return <p style={{ color: 'var(--color-text-muted)' }}>No data to visualize.</p>
    }

    const { chart_type, x_axis, y_axis, reason } = visualization

    // ── Data Table ─────────────────────────────────────────
    if (chart_type === 'table' || !x_axis) {
        const cols = Object.keys(chartData[0] || {})
        return (
            <div className="chart-container">
                <ChartTitle icon="📋" label="Data Table" reason={reason} />
                <div className="data-table-container">
                    <table className="data-table">
                        <thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                        <tbody>
                            {chartData.slice(0, 100).map((row, i) => (
                                <tr key={i} style={anomalyIndices.has(i) ? { background: 'rgba(231,76,60,0.15)' } : {}}>
                                    {cols.map((c) => <td key={c}>{String(row[c] ?? '—')}</td>)}
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
                <ChartTitle icon="📊" label="Bar Chart" reason={reason} />
                <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                        <XAxis dataKey={x_axis} tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                        <YAxis tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                        <Tooltip contentStyle={tooltipStyle} />
                        <Legend />
                        <Bar dataKey={y_axis} fill="#6c63ff" radius={[4, 4, 0, 0]} />
                        {anomalyDots.map((d) => <ReferenceDot key={d.key} x={d.x} y={d.y} r={8} fill="#e74c3c" stroke="#fff" strokeWidth={2} />)}
                    </BarChart>
                </ResponsiveContainer>
            </div>
        )
    }

    // ── Line Chart ─────────────────────────────────────────
    if (chart_type === 'line') {
        return (
            <div className="chart-container">
                <ChartTitle icon="📈" label="Line Chart" reason={reason} />
                <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                        <XAxis dataKey={x_axis} tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                        <YAxis tick={{ fill: '#a0a0b0', fontSize: 12 }} />
                        <Tooltip contentStyle={tooltipStyle} />
                        <Legend />
                        <Line type="monotone" dataKey={y_axis} stroke="#6c63ff" strokeWidth={2} dot={{ fill: '#6c63ff' }} />
                        {anomalyDots.map((d) => <ReferenceDot key={d.key} x={d.x} y={d.y} r={8} fill="#e74c3c" stroke="#fff" strokeWidth={2} />)}
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
                <ChartTitle icon="🥧" label="Pie Chart" reason={reason} />
                <ResponsiveContainer width="100%" height={400}>
                    <PieChart>
                        <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={150} label>
                            {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip contentStyle={tooltipStyle} />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        )
    }

    // ── Scatter Chart ──────────────────────────────────────
    if (chart_type === 'scatter') {
        const scatterData = chartData.map((item) => ({
            x: Number(item[x_axis]) || 0,
            y: Number(item[y_axis]) || 0,
        }))
        return (
            <div className="chart-container">
                <ChartTitle icon="🔵" label="Scatter Plot" reason={reason} />
                <ResponsiveContainer width="100%" height={400}>
                    <ScatterChart margin={{ bottom: 20, left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                        <XAxis dataKey="x" name={x_axis} tick={{ fill: '#a0a0b0', fontSize: 12 }}
                            label={{ value: x_axis, position: 'insideBottom', offset: -10, fill: '#a0a0b0', fontSize: 12 }} />
                        <YAxis dataKey="y" name={y_axis} tick={{ fill: '#a0a0b0', fontSize: 12 }}
                            label={{ value: y_axis, angle: -90, position: 'insideLeft', fill: '#a0a0b0', fontSize: 12 }} />
                        <ZAxis range={[40, 40]} />
                        <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: '3 3' }} />
                        <Scatter data={scatterData} fill="#6c63ff" fillOpacity={0.75} />
                    </ScatterChart>
                </ResponsiveContainer>
            </div>
        )
    }

    // ── Histogram ──────────────────────────────────────────
    if (chart_type === 'histogram') {
        const bins = buildHistogramBins(chartData, x_axis, 15)
        return (
            <div className="chart-container">
                <ChartTitle icon="📉" label={`Histogram — ${x_axis}`} reason={reason} />
                <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={bins} barCategoryGap="2%">
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
                        <XAxis dataKey="range" tick={{ fill: '#a0a0b0', fontSize: 10 }} interval={2} />
                        <YAxis tick={{ fill: '#a0a0b0', fontSize: 12 }}
                            label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: '#a0a0b0' }} />
                        <Tooltip contentStyle={tooltipStyle} formatter={(v) => [v, 'Count']} />
                        <Bar dataKey="count" fill="#a855f7" radius={[2, 2, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        )
    }

    // ── Heatmap ────────────────────────────────────────────
    if (chart_type === 'heatmap') {
        const colNames = Object.keys(chartData[0] || {}).filter((k) => k !== x_axis)
        const rowLabels = chartData.map((row) => String(row[x_axis] ?? ''))
        const allVals = chartData.flatMap((row) =>
            colNames.map((c) => Number(row[c])).filter((v) => !isNaN(v))
        )
        const minVal = Math.min(...allVals)
        const maxVal = Math.max(...allVals)

        return (
            <div className="chart-container">
                <ChartTitle icon="🌡️" label="Heatmap" reason={reason} />
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ borderCollapse: 'separate', borderSpacing: 3, fontSize: '0.78rem', margin: '0 auto' }}>
                        <thead>
                            <tr>
                                <th style={{ padding: '4px 8px' }}></th>
                                {colNames.map((c) => (
                                    <th key={c} style={{ padding: '4px 8px', color: 'var(--color-text-secondary)', textAlign: 'center', whiteSpace: 'nowrap', fontSize: '0.75rem' }}>{c}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {chartData.map((row, ri) => (
                                <tr key={ri}>
                                    <td style={{ padding: '4px 8px', color: 'var(--color-text-secondary)', fontWeight: 600, whiteSpace: 'nowrap' }}>{rowLabels[ri]}</td>
                                    {colNames.map((c) => {
                                        const val = Number(row[c])
                                        return (
                                            <td key={c}
                                                title={`${rowLabels[ri]} × ${c} = ${isNaN(val) ? '—' : val.toFixed(4)}`}
                                                style={{
                                                    padding: '8px 14px', borderRadius: 6, textAlign: 'center',
                                                    background: isNaN(val) ? '#1a1a2e' : heatColor(val, minVal, maxVal),
                                                    color: '#fff', fontWeight: 600, minWidth: 55,
                                                    transition: 'transform 0.15s',
                                                    cursor: 'default',
                                                }}>
                                                {isNaN(val) ? '—' : val.toFixed(2)}
                                            </td>
                                        )
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14, justifyContent: 'center', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        <span>Low ({minVal.toFixed(2)})</span>
                        <div style={{ width: 140, height: 12, borderRadius: 6, background: 'linear-gradient(to right, rgb(52,152,219), rgb(108,99,255), rgb(231,76,60))' }} />
                        <span>High ({maxVal.toFixed(2)})</span>
                    </div>
                </div>
            </div>
        )
    }

    return <p style={{ color: 'var(--color-text-muted)' }}>Unsupported chart type: {chart_type}</p>
}

export default ChartRenderer
