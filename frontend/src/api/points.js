import request from './request'

export const fetchMyPoints = (params) => request.get('/points/my', { params })

export const fetchPointsRanking = (limit = 10) => request.get('/points/ranking', { params: { limit } })

export const fetchPointsRules = () => request.get('/points/rules')

export const adjustPoints = (data) => request.post('/points/adjust', data)