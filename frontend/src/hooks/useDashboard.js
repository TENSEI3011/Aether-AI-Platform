/**
 * useDashboard — Hook to access DashboardContext
 */

import { useContext } from 'react'
import { DashboardContext } from '../context/DashboardContext'

export function useDashboard() {
    const ctx = useContext(DashboardContext)
    if (!ctx) {
        throw new Error('useDashboard must be used within a DashboardProvider')
    }
    return ctx
}
