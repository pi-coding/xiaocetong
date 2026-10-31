<template>
  <div class="board-page">
    <section class="page-card toolbar">
      <div class="summary">
        <div class="summary-item">
          <span>待派单</span><strong class="warning">{{ board.pending.length }}</strong>
        </div>
        <div class="summary-item">
          <span>处理中</span><strong>{{ board.assigned.length + board.processing.length }}</strong>
        </div>
        <div class="summary-item">
          <span>超时</span><strong class="danger">{{ timeoutCount }}</strong>
        </div>
        <div class="summary-item">
          <span>今日完成</span><strong class="success">{{ board.done.length }}</strong>
        </div>
      </div>
      <div class="tools">
        <el-input
          v-model="keyword"
          placeholder="搜索编号或标题"
          :prefix-icon="Search"
          clearable
          class="search"
          @keyup.enter="load"
          @clear="load"
        />
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </section>

    <section v-loading="loading" class="board">
      <div v-for="column in columns" :key="column.key" class="column">
        <header :style="{ borderTopColor: column.color }">
          <span>{{ column.title }}</span>
          <b>{{ board[column.key].length }}</b>
        </header>
        <div class="column-body">
          <article v-for="order in board[column.key]" :key="order.id" class="order-card" @click="openDetail(order)">
            <div class="card-top">
              <span class="type">{{ order.type_text }}</span>
              <el-tag v-if="isOrderOverdue(order)" size="small" type="danger" effect="dark">超时</el-tag>
              <el-tag v-else size="small" :type="priorityMeta(order.priority).type" effect="plain">
                {{ order.priority_text }}
              </el-tag>
            </div>
            <h4>{{ order.title }}</h4>
            <p class="loc">{{ order.toilet_name }}</p>
            <div class="card-foot">
              <span>{{ order.assignee_name || '未派单' }}</span>
              <span>{{ formatTime(order.created_at) }}</span>
            </div>
          </article>
          <el-empty v-if="!board[column.key].length" description="暂无工单" :image-size="48" />
        </div>
      </div>
    </section>

    <el-drawer v-model="drawer" title="工单详情" size="460px">
      <template v-if="current">
        <div class="drawer-head">
          <div>
            <p class="muted">{{ current.order_no }}</p>
            <h3>{{ current.title }}</h3>
          </div>
          <el-tag :type="orderStatus(current.status).type">{{ current.status_text }}</el-tag>
        </div>

        <div class="detail-grid">
          <div><span>类型</span><strong>{{ current.type_text }}</strong></div>
          <div><span>优先级</span><strong>{{ current.priority_text }}</strong></div>
          <div><span>厕所</span><strong>{{ current.toilet_name }}</strong></div>
          <div><span>位置</span><strong>{{ current.building }} 栋 {{ current.floor }} 层</strong></div>
          <div><span>报单人</span><strong>{{ current.user_name }}</strong></div>
          <div><span>联系电话</span><strong>{{ current.user_phone || '-' }}</strong></div>
          <div><span>响应时限</span><strong :class="{ danger: isOrderOverdue(current) }">{{ formatTime(current.expect_finish_at) }}</strong></div>
          <div><span>处理人</span><strong>{{ current.assignee_name || '待派单' }}</strong></div>
        </div>

        <p v-if="current.description" class="desc">{{ current.description }}</p>

        <div v-if="current.images.length" class="image-list">
          <el-image
            v-for="url in current.images"
            :key="url"
            :src="url"
            :preview-src-list="current.images"
            fit="cover"
            class="image"
          />
        </div>

        <div v-if="canAssign" class="assign-block">
          <h4>{{ current.assignee_id ? '改派处理人' : '指派处理人' }}</h4>
          <el-select v-model="selectedStaff" placeholder="选择员工" class="full">
            <el-option
              v-for="staff in candidates"
              :key="staff.id"
              :label="`${staff.name} · ${workTypeText(staff.work_type)} · 在途 ${staff.current_load} 单`"
              :value="staff.id"
            />
          </el-select>
          <el-button type="primary" class="full" :loading="acting" :disabled="!selectedStaff" @click="assign">
            {{ current.assignee_id ? '确认改派' : '确认派单' }}
          </el-button>
          <p class="muted tip">列表已按工种与工单类型过滤，仅显示在岗员工。</p>
        </div>

        <div class="drawer-actions">
          <el-button v-if="treeEvents.length" @click="showTimeline">查看进度</el-button>
          <el-button v-if="canClose" type="danger" plain :loading="acting" @click="close">关闭工单</el-button>
        </div>

        <el-timeline v-if="timelineVisible" class="timeline">
          <el-timeline-item
            v-for="node in treeEvents"
            :key="node.key"
            :timestamp="formatTime(node.time)"
            :type="node.key === 'finished' ? 'success' : 'primary'"
          >
            <p class="node-title">{{ node.title }}</p>
          </el-timeline-item>
        </el-timeline>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { assignOrder, closeOrder, fetchAdminOrders } from '@/api/order'
import { fetchStaffOptions } from '@/api/staff'
import {
  formatTime,
  isOrderOverdue,
  orderStatus,
  priorityMeta,
} from '@/utils/dict'

const columns = [
  { key: 'pending', title: '待派单', color: '#f59e0b' },
  { key: 'assigned', title: '已派单', color: '#0ea5a4' },
  { key: 'processing', title: '处理中', color: '#3b82f6' },
  { key: 'done', title: '已完成', color: '#22c55e' },
]

const board = reactive({ pending: [], assigned: [], processing: [], done: [] })
const loading = ref(false)
const keyword = ref('')
const staffOptions = ref([])

const drawer = ref(false)
const current = ref(null)
const selectedStaff = ref(null)
const acting = ref(false)
const timelineVisible = ref(false)

const timeoutCount = computed(() =>
  [...board.pending, ...board.assigned, ...board.processing].filter((item) => isOrderOverdue(item)).length,
)

const canAssign = computed(() => ['pending', 'assigned'].includes(current.value?.status))
const canClose = computed(() => current.value && !['closed', 'cancelled'].includes(current.value.status))

const candidates = computed(() => {
  const type = current.value?.type
  return staffOptions.value.filter((staff) => {
    if (staff.status !== 'on') return false
    if (staff.work_type === 'all') return true
    if (type === 'repair') return staff.work_type === 'plumber'
    return staff.work_type === 'cleaner'
  })
})

const treeEvents = computed(() => {
  const order = current.value
  if (!order) return []
  const nodes = [{ key: 'created', title: '提交工单', time: order.created_at }]
  if (order.assigned_at) nodes.push({ key: 'assigned', title: '已派单', time: order.assigned_at })
  if (order.accepted_at) nodes.push({ key: 'accepted', title: '员工接单', time: order.accepted_at })
  if (order.finished_at) nodes.push({ key: 'finished', title: '处理完成', time: order.finished_at })
  return nodes
})

const workTypeText = (type) => ({ cleaner: '保洁', plumber: '维修', all: '综合' })[type] || type

const load = async () => {
  loading.value = true
  try {
    const params = (status) => {
      const query = { status, page: 1, size: 50 }
      if (keyword.value.trim()) query.keyword = keyword.value.trim()
      return query
    }
    const results = await Promise.all(columns.map((column) => fetchAdminOrders(params(column.key))))
    columns.forEach((column, index) => {
      board[column.key] = results[index].list
    })
  } finally {
    loading.value = false
  }
}

const openDetail = (order) => {
  current.value = order
  selectedStaff.value = order.assignee_id
  timelineVisible.value = false
  drawer.value = true
}

const assign = async () => {
  acting.value = true
  try {
    await assignOrder(current.value.id, selectedStaff.value)
    ElMessage.success('派单成功')
    drawer.value = false
    await load()
  } finally {
    acting.value = false
  }
}

const close = async () => {
  let reason = ''
  try {
    const result = await ElMessageBox.prompt('请输入关闭原因（选填）', '关闭工单', {
      confirmButtonText: '确认关闭',
      cancelButtonText: '取消',
      inputPlaceholder: '如：重复报单 / 现场无此问题',
    })
    reason = result.value || ''
  } catch {
    return
  }
  acting.value = true
  try {
    await closeOrder(current.value.id, reason || null)
    ElMessage.success('工单已关闭')
    drawer.value = false
    await load()
  } finally {
    acting.value = false
  }
}

const showTimeline = () => {
  timelineVisible.value = !timelineVisible.value
}

const loadStaff = async () => {
  staffOptions.value = await fetchStaffOptions()
}

onMounted(async () => {
  await Promise.all([load(), loadStaff()])
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.board-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.summary {
  display: flex;
  gap: 36px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;

  span {
    font-size: 12px;
    color: $cct-text-light;
  }

  strong {
    font-size: 22px;
  }
}

.warning {
  color: $cct-warning;
}

.danger {
  color: $cct-danger;
}

.success {
  color: #16a34a;
}

.tools {
  display: flex;
  gap: 10px;
}

.search {
  width: 220px;
}

.board {
  display: grid;
  grid-template-columns: repeat(4, minmax(220px, 1fr));
  gap: 14px;
  min-height: 320px;
}

.column {
  background: #f7fafb;
  border-radius: $cct-radius;
  border: 1px solid $cct-border;
  display: flex;
  flex-direction: column;
  min-height: 360px;

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-top: 3px solid $cct-primary;
    border-radius: $cct-radius $cct-radius 0 0;
    background: #fff;
    font-size: 13px;
    font-weight: 600;

    b {
      color: $cct-text-light;
      font-weight: 500;
    }
  }
}

.column-body {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.order-card {
  background: #fff;
  border-radius: 10px;
  padding: 12px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: border-color 0.15s ease;

  &:hover {
    border-color: $cct-primary;
  }

  h4 {
    margin: 8px 0 4px;
    font-size: 13px;
  }
}

.card-top {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: space-between;
}

.type {
  font-size: 11px;
  color: $cct-primary;
}

.loc {
  margin: 0 0 8px;
  font-size: 11px;
  color: $cct-text-light;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-foot {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #9aa8b0;
}

.drawer-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;

  .muted {
    margin: 0 0 4px;
  }

  h3 {
    margin: 0;
    font-size: 17px;
  }
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 18px 0;

  div {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  span {
    font-size: 11px;
    color: $cct-text-light;
  }

  strong {
    font-size: 13px;
    font-weight: 500;
  }
}

.desc {
  margin: 0 0 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f6fafb;
  font-size: 12px;
  line-height: 1.6;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.image {
  width: 80px;
  height: 80px;
  border-radius: 10px;
}

.assign-block {
  padding: 14px;
  border-radius: 12px;
  background: #f1f8f8;
  margin-bottom: 14px;

  h4 {
    margin: 0 0 10px;
    font-size: 13px;
  }
}

.full {
  width: 100%;
}

.assign-block .el-button {
  margin-top: 10px;
}

.tip {
  margin: 8px 0 0;
  font-size: 11px;
}

.drawer-actions {
  display: flex;
  gap: 10px;

  .el-button {
    flex: 1;
  }
}

.timeline {
  margin-top: 16px;
}

.node-title {
  margin: 0;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .board {
    grid-template-columns: repeat(2, minmax(220px, 1fr));
  }
}
</style>