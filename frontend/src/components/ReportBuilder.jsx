/**
 * ============================================================
 * ReportBuilder — Rich branded PDF report generation
 * ============================================================
 * Uses jsPDF (already in deps) to generate multi-section PDFs
 * with branded cover page, insights, and data tables.
 * ============================================================
 */

import React, { useState, useCallback } from 'react'

function ReportBuilder({ open, onClose, query, result, insights, narration }) {
    const [generating, setGenerating] = useState(false)
    const [reportType, setReportType] = useState('detailed')

    const generatePDF = useCallback(async () => {
        if (!result) return
        setGenerating(true)

        try {
            const { jsPDF } = await import('jspdf')
            const pdf = new jsPDF('p', 'mm', 'a4')
            const pageW = pdf.internal.pageSize.getWidth()
            const pageH = pdf.internal.pageSize.getHeight()
            let y = 0

            // ── Cover Page ─────────────────────────────────────
            // Background
            pdf.setFillColor(14, 14, 19)
            pdf.rect(0, 0, pageW, pageH, 'F')

            // Purple accent strip
            pdf.setFillColor(124, 58, 237)
            pdf.rect(0, 0, pageW, 4, 'F')

            // Brand
            pdf.setFont('helvetica', 'bold')
            pdf.setFontSize(28)
            pdf.setTextColor(210, 187, 255)
            pdf.text('AI Analysis Platform', pageW / 2, 60, { align: 'center' })

            pdf.setFontSize(14)
            pdf.setTextColor(149, 141, 161)
            pdf.text('Generative AI Data Analysis Report', pageW / 2, 72, { align: 'center' })

            // Divider line
            pdf.setDrawColor(124, 58, 237)
            pdf.setLineWidth(0.5)
            pdf.line(40, 85, pageW - 40, 85)

            // Query title
            pdf.setFontSize(11)
            pdf.setTextColor(228, 225, 233)
            const queryLines = pdf.splitTextToSize(`Query: "${query}"`, pageW - 60)
            pdf.text(queryLines, 30, 100)

            // Meta info
            pdf.setFontSize(9)
            pdf.setTextColor(149, 141, 161)
            pdf.text(`Generated: ${new Date().toLocaleString()}`, 30, 120)
            pdf.text(`Data Rows: ${result.data?.length || 0}`, 30, 127)
            pdf.text(`Report Type: ${reportType === 'summary' ? 'Executive Summary' : 'Detailed Analysis'}`, 30, 134)

            // Footer
            pdf.setFontSize(8)
            pdf.text('Powered by Generative AI Analysis Platform', pageW / 2, pageH - 15, { align: 'center' })

            // ── Page 2: Insights ────────────────────────────────
            pdf.addPage()
            pdf.setFillColor(14, 14, 19)
            pdf.rect(0, 0, pageW, pageH, 'F')
            pdf.setFillColor(124, 58, 237)
            pdf.rect(0, 0, pageW, 4, 'F')

            y = 20
            pdf.setFont('helvetica', 'bold')
            pdf.setFontSize(16)
            pdf.setTextColor(210, 187, 255)
            pdf.text('Key Insights', 20, y)
            y += 12

            // Narration
            if (narration) {
                pdf.setFont('helvetica', 'normal')
                pdf.setFontSize(10)
                pdf.setTextColor(228, 225, 233)
                const narLines = pdf.splitTextToSize(narration, pageW - 40)
                pdf.text(narLines, 20, y)
                y += narLines.length * 5 + 8
            }

            // Highlights
            if (insights?.highlights?.length > 0) {
                pdf.setFont('helvetica', 'bold')
                pdf.setFontSize(11)
                pdf.setTextColor(210, 187, 255)
                pdf.text('Highlights', 20, y)
                y += 8

                pdf.setFont('helvetica', 'normal')
                pdf.setFontSize(9)
                pdf.setTextColor(204, 195, 216)

                for (const h of insights.highlights) {
                    const clean = h.replace(/[📈📉📊⬆️⬇️➡️🏆🔗📌⚡\*]/g, '').trim()
                    const lines = pdf.splitTextToSize(`• ${clean}`, pageW - 45)
                    if (y + lines.length * 4 > pageH - 20) {
                        pdf.addPage()
                        pdf.setFillColor(14, 14, 19)
                        pdf.rect(0, 0, pageW, pageH, 'F')
                        y = 20
                    }
                    pdf.text(lines, 25, y)
                    y += lines.length * 4 + 4
                }
            }

            // ── Page 3: Data Table (if detailed) ────────────────
            if (reportType === 'detailed' && result.data?.length > 0) {
                pdf.addPage()
                pdf.setFillColor(14, 14, 19)
                pdf.rect(0, 0, pageW, pageH, 'F')
                pdf.setFillColor(124, 58, 237)
                pdf.rect(0, 0, pageW, 4, 'F')

                y = 20
                pdf.setFont('helvetica', 'bold')
                pdf.setFontSize(16)
                pdf.setTextColor(210, 187, 255)
                pdf.text('Data Preview (Top 30 Rows)', 20, y)
                y += 12

                const columns = result.columns || Object.keys(result.data[0] || {})
                const colCount = Math.min(columns.length, 6)
                const colW = (pageW - 40) / colCount
                const rows = result.data.slice(0, 30)

                // Header
                pdf.setFillColor(42, 41, 47)
                pdf.rect(20, y - 4, pageW - 40, 8, 'F')
                pdf.setFont('helvetica', 'bold')
                pdf.setFontSize(7)
                pdf.setTextColor(210, 187, 255)
                for (let c = 0; c < colCount; c++) {
                    pdf.text(String(columns[c]).substring(0, 15), 22 + c * colW, y)
                }
                y += 8

                // Rows
                pdf.setFont('helvetica', 'normal')
                pdf.setFontSize(7)
                pdf.setTextColor(204, 195, 216)
                for (const row of rows) {
                    if (y > pageH - 15) {
                        pdf.addPage()
                        pdf.setFillColor(14, 14, 19)
                        pdf.rect(0, 0, pageW, pageH, 'F')
                        y = 20
                    }
                    for (let c = 0; c < colCount; c++) {
                        const val = String(row[columns[c]] ?? '').substring(0, 18)
                        pdf.text(val, 22 + c * colW, y)
                    }
                    y += 5
                }
            }

            // Save
            pdf.save(`report-${Date.now()}.pdf`)
        } catch (err) {
            console.error('PDF generation failed:', err)
        } finally {
            setGenerating(false)
        }
    }, [result, query, insights, narration, reportType])

    if (!open) return null

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '480px' }}>
                <h3 style={{ color: 'var(--color-accent)', marginBottom: 'var(--space-md)' }}>
                    📄 Generate PDF Report
                </h3>

                <div className="input-group" style={{ marginBottom: 'var(--space-md)' }}>
                    <label>Report Type</label>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {[
                            { value: 'summary', label: '📋 Executive Summary', desc: 'Insights & narration only' },
                            { value: 'detailed', label: '📊 Detailed Analysis', desc: 'Insights + data table' },
                        ].map(opt => (
                            <button
                                key={opt.value}
                                className={`btn ${reportType === opt.value ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setReportType(opt.value)}
                                style={{ flex: 1, flexDirection: 'column', padding: '0.75rem' }}
                            >
                                <div style={{ fontSize: '0.85rem' }}>{opt.label}</div>
                                <div style={{ fontSize: '0.7rem', opacity: 0.7, marginTop: '4px' }}>{opt.desc}</div>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="card" style={{
                    padding: 'var(--space-sm) var(--space-md)',
                    marginBottom: 'var(--space-md)',
                    background: 'var(--color-bg-secondary)',
                    fontSize: '0.82rem',
                }}>
                    <div style={{ color: 'var(--color-text-muted)' }}>Report contents:</div>
                    <ul style={{ margin: '0.5rem 0 0 1rem', color: 'var(--color-text-secondary)', fontSize: '0.8rem' }}>
                        <li>Branded cover page</li>
                        <li>AI narration & insights</li>
                        {reportType === 'detailed' && <li>Data table (top 30 rows)</li>}
                    </ul>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                    <button className="btn btn-secondary" onClick={onClose} disabled={generating}>Cancel</button>
                    <button className="btn btn-primary" onClick={generatePDF} disabled={generating}>
                        {generating ? '⏳ Generating...' : '📄 Generate PDF'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ReportBuilder
