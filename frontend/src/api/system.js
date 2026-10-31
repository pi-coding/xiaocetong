import request from './request'

export const fetchHealth = () => request.get('/health')