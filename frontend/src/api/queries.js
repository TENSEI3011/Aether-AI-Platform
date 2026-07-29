/**
 * Queries API — Submit natural language queries
 * Updated: supports graph_type override parameter
 */

import axiosClient from './axiosClient'

/**
 * Send a natural language query to the backend pipeline.
 * @param {string} datasetId - The uploaded dataset ID
 * @param {string} query - Natural language question
 * @param {string} graphType - Chart type override: 'auto','bar','line','pie','table'
 */
export async function askQuery(datasetId, query, graphType = 'auto') {
    const res = await axiosClient.post('/queries/ask', {
        dataset_id: datasetId,
        query,
        graph_type: graphType,
    })
    return res.data
}

export async function getQueryHistory() {
    const res = await axiosClient.get('/queries/history')
    return res.data
}
