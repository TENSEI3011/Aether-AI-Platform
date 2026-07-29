/**
 * ============================================================
 * DashboardContext — Manages dashboard chart panels
 * ============================================================
 * Stores pinned query results in session storage for
 * Power BI–style multi-chart dashboard view.
 *
 * Architecture:
 *   - Charts are stored in sessionStorage (per-session)
 *   - Each chart panel has: id, query, data, visualization,
 *     insights, and timestamp
 *   - Supports add, remove, and clear operations
 * ============================================================
 */

import React, { createContext, useState, useEffect } from 'react'

export const DashboardContext = createContext(null)

const STORAGE_KEY = 'dashboard_panels'

export function DashboardProvider({ children }) {
    const [panels, setPanels] = useState(() => {
        // Load from sessionStorage on mount
        try {
            const stored = sessionStorage.getItem(STORAGE_KEY)
            return stored ? JSON.parse(stored) : []
        } catch {
            return []
        }
    })

    // Persist to sessionStorage on every change
    useEffect(() => {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(panels))
    }, [panels])

    /**
     * Add a query result to the dashboard.
     * @param {object} panel - { query, data, visualization, insights, generatedCode }
     */
    const addPanel = (panel) => {
        const newPanel = {
            id: Date.now().toString(),
            ...panel,
            addedAt: new Date().toISOString(),
        }
        setPanels((prev) => [newPanel, ...prev])
    }

    /**
     * Remove a panel by ID.
     */
    const removePanel = (panelId) => {
        setPanels((prev) => prev.filter((p) => p.id !== panelId))
    }

    /**
     * Clear all panels from the dashboard.
     */
    const clearPanels = () => {
        setPanels([])
    }

    return (
        <DashboardContext.Provider value={{ panels, addPanel, removePanel, clearPanels }}>
            {children}
        </DashboardContext.Provider>
    )
}
