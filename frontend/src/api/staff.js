import request from './request'

export const fetchStaffOptions = () => request.get('/staffs/options')

export const fetchMyStaffProfile = () => request.get('/staffs/me')

export const fetchMyToilets = () => request.get('/staffs/my-toilets')

export const fetchStaffList = (params) => request.get('/staffs', { params })

export const createStaff = (data) => request.post('/staffs', data)

export const updateStaff = (id, data) => request.put(`/staffs/${id}`, data)

export const toggleStaffStatus = (id) => request.put(`/staffs/${id}/status`)

export const deleteStaff = (id) => request.delete(`/staffs/${id}`)