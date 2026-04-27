/**
 * Scenario API — What-If analysis
 */

import axiosClient from './axiosClient'

export async function runWhatIf(datasetId, mutations, forecastX = null, forecastY = null, forecastPeriods = 5) {
    const res = await axiosClient.post('/scenario/what-if', {
        dataset_id: datasetId,
        mutations,
        forecast_x: forecastX,
        forecast_y: forecastY,
        forecast_periods: forecastPeriods,
    })
    return res.data
}
