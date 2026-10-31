import request from './request'

export const fetchOverdueToilets = (params) => request.get('/alerts/overdue-toilets', { params })

export const fetchOverdueOrders = (params) => request.get('/alerts/overdue-orders', { params })

export const fetchAlertSummary = () => request.get('/alerts/summary')

export const createCleanOrder = (toiletId) => request.post(`/alerts/${toiletId}/create-order`)