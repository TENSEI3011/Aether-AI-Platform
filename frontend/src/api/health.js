/**
 * Health API — Fetch platform status (LLM mode, DB mode)
 */

import axiosClient from './axiosClient'

/**
 * Returns { status, llm_mode, llm_model, db_mode }
 * llm_mode: "gemini" | "stub"
 * db_mode:  "postgresql" | "sqlite"
 */
export async function getHealthStatus() {
    const res = await axiosClient.get('/health')
    return res.data
}
