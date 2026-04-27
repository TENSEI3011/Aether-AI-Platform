/**
 * Alerts API — Smart alerts CRUD and notifications
 */

import axiosClient from './axiosClient'

export async function createAlert(datasetId, columnName, condition, threshold, label = '') {
    const res = await axiosClient.post('/alerts', {
        dataset_id: datasetId,
        column_name: columnName,
        condition,
        threshold,
        label,
    })
    return res.data
}

export async function getAlerts() {
    const res = await axiosClient.get('/alerts')
    return res.data
}

export async function deleteAlert(id) {
    const res = await axiosClient.delete(`/alerts/${id}`)
    return res.data
}

export async function checkAlerts(datasetId) {
    const res = await axiosClient.post(`/alerts/check/${datasetId}`)
    return res.data
}

export async function getNotifications() {
    const res = await axiosClient.get('/alerts/notifications')
    return res.data
}

export async function markNotificationRead(id) {
    const res = await axiosClient.post(`/alerts/notifications/${id}/read`)
    return res.data
}

export async function markAllNotificationsRead() {
    const res = await axiosClient.post('/alerts/notifications/read-all')
    return res.data
}
