/**
 * ============================================================
 * DashboardContext — Manages dashboard chart panels
 * ============================================================
 * Stores pinned query results in session storage for
 * Power BI–style multi-chart dashboard view.
 *
 * Architecture:
 *   - Charts are stored in localStorage (persists across sessions)
 *   - Each chart panel has: id, query, data, visualization,
 *     insights, and timestamp
 *   - Supports add, remove, and clear operations
 *   - Layout positions are stored separately for react-grid-layout
 * ============================================================
 */

import React, { createContext, useState, useEffect, useCallback } from 'react'

export const DashboardContext = createContext(null)

const STORAGE_KEY = 'dashboard_panels'
const LAYOUT_KEY = 'dashboard_layouts'

/** Default grid position for a newly added panel */
const defaultLayoutItem = (id, index) => ({
    i: id,
    x: (index % 2) * 6,   // 2 columns in a 12-col grid
    y: Math.floor(index / 2) * 4,
    w: 6,
    h: 4,
    minW: 3,
    minH: 2,
})

export function DashboardProvider({ children }) {
    const [panels, setPanels] = useState(() => {
        // Load from localStorage on mount
        try {
            const stored = localStorage.getItem(STORAGE_KEY)
            return stored ? JSON.parse(stored) : []
        } catch {
            return []
        }
    })

    const [layouts, setLayouts] = useState(() => {
        try {
            const stored = localStorage.getItem(LAYOUT_KEY)
            return stored ? JSON.parse(stored) : {}
        } catch {
            return {}
        }
    })

    // Persist panels to localStorage on every change
    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(panels))
    }, [panels])

    // Persist layouts to localStorage on every change
    useEffect(() => {
        localStorage.setItem(LAYOUT_KEY, JSON.stringify(layouts))
    }, [layouts])

    /**
     * Build the react-grid-layout array from panels + saved layouts.
     * Ensures every panel has a layout entry.
     */
    const getGridLayout = useCallback(() => {
        const savedLg = layouts.lg || []
        return panels.map((panel, index) => {
            const existing = savedLg.find((l) => l.i === panel.id)
            return existing || defaultLayoutItem(panel.id, index)
        })
    }, [panels, layouts])

    /**
     * Called by react-grid-layout whenever the user drags or resizes.
     */
    const onLayoutChange = useCallback((currentLayout, allLayouts) => {
        setLayouts(allLayouts)
    }, [])

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
        // Also remove from saved layouts
        setLayouts((prev) => {
            const cleaned = {}
            for (const [bp, items] of Object.entries(prev)) {
                cleaned[bp] = items.filter((l) => l.i !== panelId)
            }
            return cleaned
        })
    }

    /**
     * Clear all panels from the dashboard.
     */
    const clearPanels = () => {
        setPanels([])
        setLayouts({})
    }

    return (
        <DashboardContext.Provider value={{
            panels,
            addPanel,
            removePanel,
            clearPanels,
            layouts,
            getGridLayout,
            onLayoutChange,
        }}>
            {children}
        </DashboardContext.Provider>
    )
}
