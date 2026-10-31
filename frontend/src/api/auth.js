import request from './request'

export const loginApi = (data) => request.post('/auth/login', data)

export const registerApi = (data) => request.post('/auth/register', data)

export const fetchMe = () => request.get('/auth/me')

export const updateMe = (data) => request.put('/auth/me', data)

export const changePassword = (data) => request.put('/auth/password', data)