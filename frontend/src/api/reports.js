/**
 * Reports API — Scheduled reports, PDF data, email delivery
 */

import axiosClient from './axiosClient'

export async function createSchedule(datasetId, query, frequency = 'daily', email = '') {
    const res = await axiosClient.post('/reports/schedule', {
        dataset_id: datasetId,
        query,
        frequency,
        email,
    })
    return res.data
}

export async function getSchedules() {
    const res = await axiosClient.get('/reports/schedules')
    return res.data
}

export async function deleteSchedule(id) {
    const res = await axiosClient.delete(`/reports/schedules/${id}`)
    return res.data
}

export async function sendReportEmail(email, subject, body) {
    const res = await axiosClient.post('/reports/send-email', {
        email, subject, body,
    })
    return res.data
}
