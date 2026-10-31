import request from './request'

export const createCleaningLog = (data) => request.post('/cleaning-logs', data)

export const fetchCleaningLogs = (params) => request.get('/cleaning-logs', { params })

export const fetchMyCleaningLogs = (params) => request.get('/cleaning-logs/my', { params })

export const fetchToiletCleaningLogs = (toiletId, params) =>
  request.get(`/toilets/${toiletId}/cleaning-logs`, { params })

export const fetchCleaningLog = (id) => request.get(`/cleaning-logs/${id}`)