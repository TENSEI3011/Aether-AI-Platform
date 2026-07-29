/**
 * Datasets API — Upload and inspect datasets
 */

import axiosClient from './axiosClient'

export async function uploadDataset(file) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await axiosClient.post('/datasets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
}

export async function getSchema(datasetId) {
    const res = await axiosClient.get(`/datasets/${datasetId}/schema`)
    return res.data
}

export async function getProfile(datasetId) {
    const res = await axiosClient.get(`/datasets/${datasetId}/profile`)
    return res.data
}
