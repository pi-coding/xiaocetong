export const TOILET_STATUS = {
  normal: { label: '正常', type: 'success' },
  dirty: { label: '脏乱待清洁', type: 'warning' },
  fault: { label: '设施故障', type: 'danger' },
  maintenance: { label: '维护中', type: 'info' },
}

export const WARN_LEVEL = {
  0: { label: '清洁正常', type: 'success' },
  1: { label: '需清洁', type: 'warning' },
  2: { label: '超时较久', type: 'danger' },
  3: { label: '严重超时', type: 'danger' },
}

export const GENDER_TEXT = { male: '男厕', female: '女厕', all: '通用' }

export const ROLE_TEXT = { student: '学生', admin: '管理员', staff: '后勤员工' }

export const ORDER_TYPE_TEXT = { unclog: '通厕所', clean: '清洁', repair: '报修' }

export const toiletStatus = (status) => TOILET_STATUS[status] || { label: status || '未知', type: 'info' }

export const warnMeta = (level) => WARN_LEVEL[level] || WARN_LEVEL[0]

export function formatTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 16)
}

export function formatDuration(minutes) {
  const value = Math.max(0, Number(minutes) || 0)
  if (value < 60) return `${value} 分钟`
  const hours = Math.floor(value / 60)
  const rest = value % 60
  return rest ? `${hours} 小时 ${rest} 分` : `${hours} 小时`
}

export function cleanStatusText(toilet) {
  if (!toilet) return '-'
  if (toilet.never_cleaned) return '暂无清洁记录'
  if (toilet.overdue_minutes > 0) return `超时 ${formatDuration(toilet.overdue_minutes)}`
  return '清洁正常'
}

export function scoreText(value) {
  const score = Number(value)
  if (Number.isNaN(score)) return '-'
  return score.toFixed(1)
}
export const ORDER_STATUS = {
  pending: { label: '待派单', type: 'warning' },
  assigned: { label: '已派单', type: 'primary' },
  processing: { label: '处理中', type: 'primary' },
  done: { label: '已完成', type: 'success' },
  closed: { label: '已关闭', type: 'info' },
  cancelled: { label: '已取消', type: 'info' },
}

export const PRIORITY = {
  low: { label: '低', type: 'info' },
  normal: { label: '普通', type: 'primary' },
  high: { label: '高', type: 'warning' },
  urgent: { label: '紧急', type: 'danger' },
}

export const ORDER_TYPE_ICON = { unclog: 'MagicStick', clean: 'Brush', repair: 'Tools' }

export const orderStatus = (status) => ORDER_STATUS[status] || { label: status || '未知', type: 'info' }

export const priorityMeta = (priority) => PRIORITY[priority] || PRIORITY.normal

export function isOrderOverdue(order) {
  if (!order || !order.expect_finish_at) return false
  if (!['pending', 'assigned', 'processing'].includes(order.status)) return false
  return new Date(order.expect_finish_at).getTime() < Date.now()
}

export function timeLeftText(order) {
  if (!order?.expect_finish_at) return '-'
  const diff = new Date(order.expect_finish_at).getTime() - Date.now()
  if (diff <= 0) return `已超时 ${formatDuration(Math.floor(-diff / 60000))}`
  return `剩余 ${formatDuration(Math.floor(diff / 60000))}`
}