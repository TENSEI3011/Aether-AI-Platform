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

export async function getFullProfile(datasetId) {
    const res = await axiosClient.get(`/datasets/${datasetId}/full-profile`)
    return res.data
}

/** List all datasets the current user has ever uploaded (from DB). */
export async function getMyDatasets() {
    const res = await axiosClient.get('/datasets/list')
    return res.data
}

export async function exportExcel(data, columns, filename = 'export.xlsx') {
    const res = await axiosClient.post('/datasets/export-excel', {
        data, columns, filename,
    }, { responseType: 'blob' })
    // Trigger browser download
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
}

/**
 * Soft-delete a dataset. Only the owner can delete.
 */
export async function deleteDataset(datasetId) {
    const res = await axiosClient.delete(`/datasets/${datasetId}`)
    return res.data
}
