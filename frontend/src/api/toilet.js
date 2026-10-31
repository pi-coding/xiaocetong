import request from './request'

export const fetchToilets = (params) => request.get('/toilets', { params })

export const fetchNearbyToilets = (limit = 5) => request.get('/toilets/nearby', { params: { limit } })

export const fetchToiletDetail = (id) => request.get(`/toilets/${id}`)

export const fetchToiletQr = (id) => request.get(`/toilets/${id}/qr`)

export const createToilet = (data) => request.post('/toilets', data)

export const updateToilet = (id, data) => request.put(`/toilets/${id}`, data)

export const deleteToilet = (id) => request.delete(`/toilets/${id}`)