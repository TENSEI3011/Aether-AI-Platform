/**
 * Saved Queries API — Save, list, delete query templates
 */

import axiosClient from './axiosClient'

export async function saveQuery(name, datasetId, naturalQuery, graphType = 'auto') {
    const res = await axiosClient.post('/saved-queries', {
        name,
        dataset_id: datasetId,
        natural_query: naturalQuery,
        graph_type: graphType,
    })
    return res.data
}

export async function getSavedQueries() {
    const res = await axiosClient.get('/saved-queries')
    return res.data
}

export async function deleteSavedQuery(id) {
    const res = await axiosClient.delete(`/saved-queries/${id}`)
    return res.data
}
