export const ROLE_HOME = {
  student: '/student/home',
  admin: '/admin/dashboard',
  staff: '/staff/tasks',
}

export const studentTabs = [
  { title: '首页', path: '/student/home', icon: 'HomeFilled', enabled: true },
  { title: '找厕所', path: '/student/toilets', icon: 'Location', enabled: true },
  { title: '工单', path: '/student/orders', icon: 'Tickets', enabled: true },
  { title: 'AI 助手', path: '/student/ai', icon: 'ChatDotRound', enabled: true },
  { title: '我的', path: '/student/profile', icon: 'User', enabled: true },
]

export const adminMenus = [
  { title: '数据驾驶舱', path: '/admin/dashboard', icon: 'DataAnalysis', enabled: true },
  { title: '公共厕所台账', path: '/admin/toilets', icon: 'OfficeBuilding', enabled: true },
  { title: '超时未打扫预警', path: '/admin/alerts', icon: 'AlarmClock', enabled: true },
  { title: '工单看板', path: '/admin/orders', icon: 'Tickets', enabled: true },
  { title: 'AI 派单', path: '/admin/dispatch', icon: 'MagicStick', enabled: true },
  { title: '统计报表', path: '/admin/stats', icon: 'TrendCharts', enabled: true },
  { title: '员工管理', path: '/admin/staffs', icon: 'UserFilled', enabled: true },
  { title: '评价管理', path: '/admin/evaluations', icon: 'ChatLineSquare', enabled: true },
  { title: 'AI 助手', path: '/admin/ai', icon: 'ChatDotRound', enabled: true },
]

export const staffTabs = [
  { title: '待办工单', path: '/staff/tasks', icon: 'Tickets', enabled: true },
  { title: '清洁打卡', path: '/staff/checkin', icon: 'Camera', enabled: true },
  { title: '我的', path: '/staff/profile', icon: 'User', enabled: true },
]

export const enabledMenus = (menus) => menus.filter((item) => item.enabled)