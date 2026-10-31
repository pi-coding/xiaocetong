import request from './request'

export const chatWithAi = (data) => request.post('/ai/chat', data)

export const describeProblem = (text) => request.post('/ai/describe-problem', { text })

export const fetchInsight = () => request.get('/ai/insight')