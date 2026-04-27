/**
 * Queries API — Submit natural language queries and cleaning
 */

import axiosClient from './axiosClient'

/**
 * Send a natural language query to the backend pipeline.
 */
export async function askQuery(datasetId, query, graphType = 'auto', sessionId = null, thresholds = {}) {
    const payload = {
        dataset_id:      datasetId,
        query,
        graph_type:      graphType,
        z_threshold:     thresholds.z_threshold     ?? 3.0,
        iqr_multiplier:  thresholds.iqr_multiplier  ?? 1.5,
    }
    if (sessionId) payload.session_id = sessionId

    const res = await axiosClient.post('/queries/ask', payload)
    return res.data
}

export async function getQueryHistory() {
    const res = await axiosClient.get('/queries/history')
    return res.data
}

/**
 * Send a natural language cleaning instruction to the backend.
 * e.g. "remove duplicates", "fill missing values with 0"
 */
export async function cleanDataset(datasetId, instruction) {
    const res = await axiosClient.post('/queries/clean', {
        dataset_id: datasetId,
        instruction,
    })
    return res.data
}

/**
 * Run a forecasting model on a dataset column.
 * method: "linear" | "moving_average"
 */
export async function forecastQuery(datasetId, xColumn, yColumn, periods = 5, method = 'linear') {
    const res = await axiosClient.post('/queries/forecast', {
        dataset_id: datasetId,
        x_column:   xColumn,
        y_column:   yColumn,
        periods,
        method,
    })
    return res.data
}
