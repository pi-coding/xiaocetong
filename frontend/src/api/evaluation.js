import request from './request'

export const createEvaluation = (orderId, data) => request.post(`/orders/${orderId}/evaluation`, data)

export const fetchEvaluations = (params) => request.get('/evaluations', { params })

export const fetchMyEvaluations = (params) => request.get('/evaluations/my', { params })

export const replyEvaluation = (id, reply) => request.put(`/evaluations/${id}/reply`, { reply })

export const appealEvaluation = (id) => request.put(`/evaluations/${id}/appeal`)