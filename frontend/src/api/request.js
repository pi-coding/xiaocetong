import axios from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'cct_token'
const USER_KEY = 'cct_user'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 20000,
})

service.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

service.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && body.code === 0) {
      return body.data
    }
    const msg = body?.msg || '请求失败'
    if (body?.code === 1001) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      if (!window.location.hash.startsWith('#/login')) {
        window.location.hash = '#/login'
      }
      ElMessage.warning('登录状态已失效，请重新登录')
      return Promise.reject(new Error(msg))
    }
    ElMessage.error(msg)
    return Promise.reject(new Error(msg))
  },
  (error) => {
    const msg = error.response?.data?.msg || error.message || '网络异常，请稍后重试'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default service