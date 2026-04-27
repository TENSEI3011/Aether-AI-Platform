/**
 * ============================================================
 * pdfReport.js — Structured per-query PDF report generator
 * ============================================================
 * Generates a proper multi-section PDF using jsPDF (already
 * installed). Unlike the html2canvas dashboard export, this
 * produces a text-rich document with:
 *   - Query title
 *   - AI explanation
 *   - Generated Pandas code
 *   - Key insights (bulleted)
 *   - Anomaly summary
 *   - Data table (first 20 rows)
 *   - Footer with timestamp
 * ============================================================
 */

/**
 * Generate and download a structured PDF report for a query result.
 * @param {object} result  — The full API response from /queries/ask
 */
export async function generateQueryPDF(result) {
    const { jsPDF } = await import('jspdf')

    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const pageW  = doc.internal.pageSize.getWidth()
    const pageH  = doc.internal.pageSize.getHeight()
    const margin = 16
    const contentW = pageW - margin * 2
    let y = margin

    // ── Helper: safe text wrap ────────────────────────────
    const addText = (text, fontSize = 10, color = [220, 220, 230], bold = false, maxWidth = contentW) => {
        doc.setFontSize(fontSize)
        doc.setTextColor(...color)
        doc.setFont('helvetica', bold ? 'bold' : 'normal')
        const lines = doc.splitTextToSize(String(text || ''), maxWidth)
        lines.forEach((line) => {
            if (y + 6 > pageH - margin) { doc.addPage(); y = margin }
            doc.text(line, margin, y)
            y += fontSize * 0.45
        })
        y += 2
    }

    const addSection = (title) => {
        y += 4
        if (y + 10 > pageH - margin) { doc.addPage(); y = margin }
        // Section title bar
        doc.setFillColor(30, 30, 60)
        doc.roundedRect(margin, y - 4, contentW, 9, 2, 2, 'F')
        doc.setFontSize(11)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(120, 160, 255)
        doc.text(title, margin + 3, y + 2)
        y += 9
    }

    const addHRule = () => {
        doc.setDrawColor(45, 45, 80)
        doc.setLineWidth(0.3)
        doc.line(margin, y, pageW - margin, y)
        y += 4
    }

    // ── Cover: gradient-style header ──────────────────────
    doc.setFillColor(15, 15, 35)
    doc.rect(0, 0, pageW, 38, 'F')
    doc.setFillColor(20, 20, 60)
    doc.rect(0, 30, pageW, 6, 'F')

    doc.setFontSize(18)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(120, 160, 255)
    doc.text('AI Analysis Report', margin, 16)

    doc.setFontSize(9)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(140, 140, 180)
    doc.text('Generative AI Data Analysis Platform', margin, 23)

    const ts = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })
    doc.text(`Generated: ${ts}`, pageW - margin - 1, 23, { align: 'right' })

    y = 46

    // ── Section 1: Query ──────────────────────────────────
    addSection('📋 Query')
    addText(result.query || '—', 12, [255, 255, 255], true)

    // ── Section 2: AI Explanation ─────────────────────────
    addSection('🤖 AI Explanation')
    addText(result.explanation || 'No explanation available.', 10, [200, 200, 220])

    // ── Section 3: Narration ──────────────────────────────
    if (result.narration) {
        addSection('📢 AI Narration')
        addText(result.narration, 10, [200, 220, 200])
    }

    // ── Section 4: Generated Code ─────────────────────────
    addSection('💻 Generated Pandas Code')
    if (result.generated_code) {
        doc.setFillColor(20, 22, 40)
        const codeLines = doc.splitTextToSize(result.generated_code, contentW - 6)
        const codeH = codeLines.length * 5 + 6
        if (y + codeH > pageH - margin) { doc.addPage(); y = margin }
        doc.roundedRect(margin, y, contentW, codeH, 2, 2, 'F')
        doc.setFontSize(8.5)
        doc.setFont('courier', 'normal')
        doc.setTextColor(80, 220, 150)
        codeLines.forEach((line, i) => {
            doc.text(line, margin + 3, y + 5 + i * 5)
        })
        y += codeH + 4
    }

    // ── Section 5: Key Insights ───────────────────────────
    const highlights = result.insights?.highlights || []
    if (highlights.length > 0) {
        addSection('📊 Key Insights')
        // Remove emoji chars that jsPDF can't render
        const cleanH = (s) => s.replace(/[\u{1F300}-\u{1FFFF}]/gu, '').replace(/[📈📉📊⬆️⬇️➡️🏆🔗📌⚡]/g, '').trim()
        highlights.forEach((h) => {
            addText(`• ${cleanH(h)}`, 9.5, [190, 220, 255])
        })
        if (result.insights?.summary) {
            y += 2
            addText(result.insights.summary, 9, [160, 160, 200])
        }
    }

    // ── Section 6: Anomalies ──────────────────────────────
    const anomalyCount = result.anomalies?.anomaly_count || 0
    if (anomalyCount > 0) {
        addSection(`⚠️ Anomalies Detected (${anomalyCount})`)
        ;(result.anomalies?.insights || []).slice(0, 6).forEach((msg) => {
            addText(`• ${msg}`, 9.5, [255, 180, 100])
        })
    }

    // ── Section 7: Data Table ─────────────────────────────
    const data    = result.result?.data || []
    const columns = result.result?.columns || []
    if (data.length > 0 && columns.length > 0) {
        addSection(`📋 Data Table (first ${Math.min(data.length, 20)} of ${result.result?.row_count || data.length} rows)`)

        const rows       = data.slice(0, 20)
        const maxCols    = Math.min(columns.length, 6)
        const colW       = contentW / maxCols
        const cellH      = 6
        const headerY    = y

        // Header row
        doc.setFillColor(30, 30, 70)
        doc.rect(margin, headerY, contentW, cellH, 'F')
        doc.setFontSize(8)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(130, 170, 255)
        columns.slice(0, maxCols).forEach((col, ci) => {
            const cx = margin + ci * colW
            doc.text(String(col).slice(0, 14), cx + 2, headerY + 4)
        })
        y += cellH

        // Data rows
        rows.forEach((row, ri) => {
            if (y + cellH > pageH - margin) { doc.addPage(); y = margin }
            if (ri % 2 === 0) {
                doc.setFillColor(20, 20, 45)
                doc.rect(margin, y, contentW, cellH, 'F')
            }
            doc.setFontSize(7.5)
            doc.setFont('helvetica', 'normal')
            doc.setTextColor(200, 200, 220)
            columns.slice(0, maxCols).forEach((col, ci) => {
                const val = String(row[col] ?? '').slice(0, 14)
                doc.text(val, margin + ci * colW + 2, y + 4)
            })
            y += cellH
        })
        y += 4
    }

    // ── Suggestions ───────────────────────────────────────
    const suggestions = result.suggestions || []
    if (suggestions.length > 0) {
        addSection('💡 Suggested Follow-up Questions')
        suggestions.forEach((s, i) => {
            addText(`${i + 1}. ${s}`, 9.5, [180, 255, 180])
        })
    }

    // ── Footer on every page ──────────────────────────────
    const totalPages = doc.getNumberOfPages()
    for (let p = 1; p <= totalPages; p++) {
        doc.setPage(p)
        doc.setFillColor(15, 15, 30)
        doc.rect(0, pageH - 10, pageW, 10, 'F')
        doc.setFontSize(7.5)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(100, 100, 140)
        doc.text('Generative AI Analysis Platform — Academic Project', margin, pageH - 3)
        doc.text(`Page ${p} of ${totalPages}`, pageW - margin, pageH - 3, { align: 'right' })
    }

    // ── Save ──────────────────────────────────────────────
    const safeName = (result.query || 'report').slice(0, 40).replace(/[^a-z0-9 ]/gi, '_')
    doc.save(`analysis-${safeName}.pdf`)
}
