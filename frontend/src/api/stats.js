import axios from 'axios'
import request from './request'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export const fetchOverview = () => request.get('/stats/overview')

export const fetchOrdersTrend = (days = 7) => request.get('/stats/orders-trend', { params: { days } })

export const fetchTypeDistribution = () => request.get('/stats/type-distribution')

export const fetchToiletRanking = (limit = 5) => request.get('/stats/toilet-ranking', { params: { limit } })

export const fetchStaffRanking = (limit = 5) => request.get('/stats/staff-ranking', { params: { limit } })

export const fetchBuildingHeat = () => request.get('/stats/building-heat')

export const fetchEvaluationSummary = () => request.get('/stats/evaluation-summary')

export const downloadOrdersCsv = (params = {}) =>
  axios.get(`${API_BASE}/stats/export`, {
    params,
    responseType: 'blob',
    headers: { Authorization: `Bearer ${localStorage.getItem('cct_token') || ''}` },
  })