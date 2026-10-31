import request from './request'

export const fetchMyBinding = () => request.get('/dorm-bindings/my')

export const matchBinding = (params) => request.get('/dorm-bindings/match', { params })

export const createBinding = (data) => request.post('/dorm-bindings', data)

export const updateBinding = (id, data) => request.put(`/dorm-bindings/${id}`, data)

export const deleteBinding = (id) => request.delete(`/dorm-bindings/${id}`)