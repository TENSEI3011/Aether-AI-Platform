/**
 * Compare API — Compare two datasets
 */

import axiosClient from './axiosClient'

export async function compareDatasets(datasetId1, datasetId2) {
    const res = await axiosClient.post('/compare', {
        dataset_id_1: datasetId1,
        dataset_id_2: datasetId2,
    })
    return res.data
}
