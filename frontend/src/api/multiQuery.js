/**
 * Multi-Query API — JOIN queries across two datasets
 */

import axiosClient from './axiosClient'

/** Get columns that exist in BOTH datasets (valid join keys) */
export async function getCommonColumns(datasetId1, datasetId2) {
    const res = await axiosClient.get('/multi-query/common-columns', {
        params: { dataset_id_1: datasetId1, dataset_id_2: datasetId2 },
    })
    return res.data
}

/** Preview the merged DataFrame (first 10 rows) before running a query */
export async function previewJoin(datasetId1, datasetId2, joinOn, joinHow = 'inner') {
    const res = await axiosClient.post('/multi-query/preview-join', {
        dataset_id_1: datasetId1,
        dataset_id_2: datasetId2,
        join_on:      joinOn,
        join_how:     joinHow,
    })
    return res.data
}

/** Run a natural-language query on the merged result of two datasets */
export async function askMultiQuery(datasetId1, datasetId2, joinOn, joinHow, query, graphType = 'auto', sessionId = null) {
    const payload = {
        dataset_id_1: datasetId1,
        dataset_id_2: datasetId2,
        join_on:      joinOn,
        join_how:     joinHow,
        query,
        graph_type:   graphType,
    }
    if (sessionId) payload.session_id = sessionId
    const res = await axiosClient.post('/multi-query/ask', payload)
    return res.data
}
