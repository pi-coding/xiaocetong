import { defineStore } from 'pinia'
import { fetchMe, loginApi } from '@/api/auth'

const TOKEN_KEY = 'cct_token'
const USER_KEY = 'cct_user'

const ROLE_HOME = {
  student: '/student/home',
  admin: '/admin/dashboard',
  staff: '/staff/tasks',
}

function readUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: readUser(),
  }),
  getters: {
    isLogin: (state) => Boolean(state.token && state.user),
    role: (state) => state.user?.role || '',
    roleName: (state) =>
      ({ student: '学生', admin: '管理员', staff: '后勤员工' })[state.user?.role] || '访客',
    displayName: (state) => state.user?.real_name || state.user?.username || '访客',
    homePath: (state) => ROLE_HOME[state.user?.role] || '/login',
  },
  actions: {
    persist() {
      localStorage.setItem(TOKEN_KEY, this.token)
      localStorage.setItem(USER_KEY, JSON.stringify(this.user))
    },
    async login(form) {
      const data = await loginApi(form)
      this.token = data.token
      this.user = data.user
      this.persist()
      return data
    },
    async refreshMe() {
      const data = await fetchMe()
      this.user = data
      this.persist()
      return data
    },
    updateLocal(user) {
      this.user = user
      this.persist()
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})