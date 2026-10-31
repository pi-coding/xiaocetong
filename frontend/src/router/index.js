import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    redirect: () => {
      const store = useUserStore()
      return store.isLogin ? store.homePath : '/login'
    },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue'),
    meta: { public: true, title: '学生注册' },
  },
  {
    path: '/student',
    component: () => import('@/layouts/StudentLayout.vue'),
    meta: { roles: ['student'] },
    children: [
      {
        path: 'home',
        name: 'student-home',
        component: () => import('@/views/student/Home.vue'),
        meta: { title: '首页' },
      },
      {
        path: 'toilets',
        name: 'student-toilets',
        component: () => import('@/views/student/ToiletSearch.vue'),
        meta: { title: '找厕所' },
      },
      {
        path: 'toilets/:id',
        name: 'student-toilet-detail',
        component: () => import('@/views/student/ToiletDetail.vue'),
        meta: { title: '厕所详情' },
      },
      {
        path: 'orders',
        name: 'student-orders',
        component: () => import('@/views/student/OrderList.vue'),
        meta: { title: '我的工单' },
      },
      {
        path: 'orders/create',
        name: 'student-order-create',
        component: () => import('@/views/student/CreateOrder.vue'),
        meta: { title: '提交工单' },
      },
      {
        path: 'orders/:id',
        name: 'student-order-detail',
        component: () => import('@/views/student/OrderDetail.vue'),
        meta: { title: '工单详情' },
      },
      {
        path: 'bind',
        name: 'student-bind',
        component: () => import('@/views/student/BindDorm.vue'),
        meta: { title: '宿舍绑定' },
      },
      {
        path: 'points',
        name: 'student-points',
        component: () => import('@/views/student/Points.vue'),
        meta: { title: '我的积分' },
      },
      {
        path: 'ai',
        name: 'student-ai',
        component: () => import('@/views/student/AiAssistant.vue'),
        meta: { title: 'AI 助手' },
      },
      {
        path: 'profile',
        name: 'student-profile',
        component: () => import('@/views/student/Profile.vue'),
        meta: { title: '我的' },
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { roles: ['admin'] },
    children: [
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '数据驾驶舱' },
      },
      {
        path: 'toilets',
        name: 'admin-toilets',
        component: () => import('@/views/admin/ToiletManage.vue'),
        meta: { title: '公共厕所台账' },
      },
      {
        path: 'orders',
        name: 'admin-orders',
        component: () => import('@/views/admin/OrderBoard.vue'),
        meta: { title: '工单看板' },
      },
      {
        path: 'alerts',
        name: 'admin-alerts',
        component: () => import('@/views/admin/OverdueAlert.vue'),
        meta: { title: '超时未打扫预警' },
      },
      {
        path: 'dispatch',
        name: 'admin-dispatch',
        component: () => import('@/views/admin/AiDispatch.vue'),
        meta: { title: 'AI 派单' },
      },
      {
        path: 'evaluations',
        name: 'admin-evaluations',
        component: () => import('@/views/admin/EvaluationManage.vue'),
        meta: { title: '评价管理' },
      },
      {
        path: 'stats',
        name: 'admin-stats',
        component: () => import('@/views/admin/StatsReport.vue'),
        meta: { title: '统计报表' },
      },
      {
        path: 'staffs',
        name: 'admin-staffs',
        component: () => import('@/views/admin/StaffManage.vue'),
        meta: { title: '员工管理' },
      },
      {
        path: 'ai',
        name: 'admin-ai',
        component: () => import('@/views/admin/AiAssistant.vue'),
        meta: { title: 'AI 助手' },
      },
    ],
  },
  {
    path: '/staff',
    component: () => import('@/layouts/StaffLayout.vue'),
    meta: { roles: ['staff'] },
    children: [
      {
        path: 'tasks',
        name: 'staff-tasks',
        component: () => import('@/views/staff/Tasks.vue'),
        meta: { title: '待办工单' },
      },
      {
        path: 'tasks/:id',
        name: 'staff-task-detail',
        component: () => import('@/views/staff/TaskDetail.vue'),
        meta: { title: '工单处理' },
      },
      {
        path: 'checkin',
        name: 'staff-checkin',
        component: () => import('@/views/staff/CheckIn.vue'),
        meta: { title: '清洁打卡' },
      },
      {
        path: 'profile',
        name: 'staff-profile',
        component: () => import('@/views/staff/Profile.vue'),
        meta: { title: '我的' },
      },
    ],
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/Forbidden.vue'),
    meta: { title: '无访问权限' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFound.vue'),
    meta: { public: true, title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const store = useUserStore()

  if (to.meta.public) {
    if (store.isLogin && (to.name === 'login' || to.name === 'register')) {
      return store.homePath
    }
    return true
  }

  if (!store.isLogin) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const roles = to.meta.roles
  if (roles && !roles.includes(store.role)) {
    return '/403'
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 校厕通` : '校厕通 · 校园厕所智能管家'
})

export default router