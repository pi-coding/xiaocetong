import request from './request'

export const createOrder = (data) => request.post('/orders', data)

export const fetchMyOrders = (params) => request.get('/orders/my', { params })

export const fetchOrderDetail = (id) => request.get(`/orders/${id}`)

export const fetchOrderTimeline = (id) => request.get(`/orders/${id}/timeline`)

export const cancelOrder = (id) => request.put(`/orders/${id}/cancel`)

export const urgeOrder = (id) => request.put(`/orders/${id}/urge`)

export const fetchAdminOrders = (params) => request.get('/orders', { params })

export const assignOrder = (id, staffId, extra = {}) =>
  request.post(`/orders/${id}/assign`, { staff_id: staffId, ...extra })

export const fetchDispatchSuggestions = (params) =>
  request.get('/orders/ai-dispatch/suggest', { params })

export const runAiDispatch = (orderIds = []) =>
  request.post('/orders/ai-dispatch', { order_ids: orderIds })

export const closeOrder = (id, reason) => request.post(`/orders/${id}/close`, { reason })

export const fetchStaffTasks = (params) => request.get('/orders/staff/my', { params })

export const acceptOrder = (id) => request.post(`/orders/${id}/accept`)

export const finishOrder = (id, data) => request.post(`/orders/${id}/finish`, data)