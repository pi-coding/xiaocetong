<template>
  <div class="alerts-page">
    <section class="summary-cards">
      <div class="stat-card">
        <span class="label">超时未打扫</span>
        <strong class="danger">{{ summary?.overdue_toilets?.total ?? 0 }}</strong>
        <span class="hint">含预警 / 严重 / 紧急</span>
      </div>
      <div class="stat-card">
        <span class="label">预警</span>
        <strong class="warning">{{ summary?.overdue_toilets?.warning ?? 0 }}</strong>
        <span class="hint">超周期 1 倍以内</span>
      </div>
      <div class="stat-card">
        <span class="label">严重</span>
        <strong class="danger">{{ summary?.overdue_toilets?.serious ?? 0 }}</strong>
        <span class="hint">超周期 1-2 倍</span>
      </div>
      <div class="stat-card">
        <span class="label">紧急</span>
        <strong class="danger">{{ summary?.overdue_toilets?.urgent ?? 0 }}</strong>
        <span class="hint">超周期 2 倍以上 / 无记录</span>
      </div>
      <div class="stat-card">
        <span class="label">超时工单</span>
        <strong class="warning">{{ summary?.overdue_orders?.total ?? 0 }}</strong>
        <span class="hint">超出响应时限</span>
      </div>
    </section>

    <section class="page-card">
      <div class="toolbar">
        <div class="tabs">
          <button type="button" class="tab" :class="{ active: tab === 'toilets' }" @click="switchTab('toilets')">
            超时未打扫厕所
          </button>
          <button type="button" class="tab" :class="{ active: tab === 'orders' }" @click="switchTab('orders')">
            超时工单
          </button>
        </div>
        <div class="tools">
          <el-select v-if="tab === 'toilets'" v-model="minLevel" size="small" class="level-select" @change="reloadToilets">
            <el-option label="全部等级" :value="1" />
            <el-option label="严重及以上" :value="2" />
            <el-option label="仅紧急" :value="3" />
          </el-select>
          <el-button size="small" :icon="Refresh" :loading="loading" @click="loadAll">刷新</el-button>
        </div>
      </div>

      <template v-if="tab === 'toilets'">
        <el-table v-loading="loading" :data="toiletList" stripe>
          <el-table-column label="厕所" min-width="190">
            <template #default="{ row }">
              <div class="toilet-name">{{ row.name }}</div>
              <span class="muted">{{ row.code }} · {{ row.building }} 栋 {{ row.floor }} 层</span>
            </template>
          </el-table-column>
          <el-table-column label="超时情况" width="150">
            <template #default="{ row }">
              <span class="danger-text">{{ row.never_cleaned ? '暂无清洁记录' : formatDuration(row.overdue_minutes) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="等级" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="warnMeta(row.warn_level).type" effect="dark">{{ row.level_text }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="责任保洁" width="100">
            <template #default="{ row }">{{ row.cleaner_name || '未指派' }}</template>
          </el-table-column>
          <el-table-column label="最近清洁" width="150">
            <template #default="{ row }">{{ formatTime(row.last_cleaned_at) }}</template>
          </el-table-column>
          <el-table-column label="处理中工单" width="100">
            <template #default="{ row }">{{ row.active_order_count }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :loading="creatingId === row.id" @click="createOrder(row)">
                生成清洁单
              </el-button>
              <el-button link type="primary" @click="router.push(`/admin/toilets`)">台账</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pager">
          <el-pagination
            background
            layout="total, prev, pager, next"
            :total="toiletTotal"
            :page-size="10"
            :current-page="toiletPage"
            @current-change="onToiletPage"
          />
        </div>
      </template>

      <template v-else>
        <el-table v-loading="loading" :data="orderList" stripe>
          <el-table-column prop="order_no" label="工单号" width="160" />
          <el-table-column label="工单" min-width="200">
            <template #default="{ row }">
              <div class="toilet-name">{{ row.title }}</div>
              <span class="muted">{{ row.type_text }} · {{ row.toilet_name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="优先级" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="priorityMeta(row.priority).type" effect="plain">{{ row.priority_text }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="报单人" width="100">
            <template #default="{ row }">{{ row.user_name }}</template>
          </el-table-column>
          <el-table-column label="处理人" width="100">
            <template #default="{ row }">{{ row.assignee_name || '待派单' }}</template>
          </el-table-column>
          <el-table-column label="超时时长" width="120">
            <template #default="{ row }">
              <span class="danger-text">{{ overdueOrderText(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="router.push('/admin/dispatch')">去派单</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pager">
          <el-pagination
            background
            layout="total, prev, pager, next"
            :total="orderTotal"
            :page-size="10"
            :current-page="orderPage"
            @current-change="onOrderPage"
          />
        </div>
      </template>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import {
  createCleanOrder,
  fetchAlertSummary,
  fetchOverdueOrders,
  fetchOverdueToilets,
} from '@/api/alert'
import {
  formatDuration,
  formatTime,
  priorityMeta,
  warnMeta,
} from '@/utils/dict'

const router = useRouter()
const summary = ref(null)
const tab = ref('toilets')
const loading = ref(false)
const creatingId = ref(null)

const minLevel = ref(1)
const toiletList = ref([])
const toiletTotal = ref(0)
const toiletPage = ref(1)

const orderList = ref([])
const orderTotal = ref(0)
const orderPage = ref(1)

const loadSummary = async () => {
  summary.value = await fetchAlertSummary()
}

const loadToilets = async () => {
  const data = await fetchOverdueToilets({ min_level: minLevel.value, page: toiletPage.value, size: 10 })
  toiletList.value = data.list
  toiletTotal.value = data.total
}

const loadOrders = async () => {
  const data = await fetchOverdueOrders({ page: orderPage.value, size: 10 })
  orderList.value = data.list
  orderTotal.value = data.total
}

const loadAll = async () => {
  loading.value = true
  try {
    await Promise.all([loadSummary(), loadToilets(), loadOrders()])
  } finally {
    loading.value = false
  }
}

const reloadToilets = async () => {
  toiletPage.value = 1
  loading.value = true
  try {
    await loadToilets()
  } finally {
    loading.value = false
  }
}

const switchTab = (value) => {
  tab.value = value
}

const onToiletPage = (value) => {
  toiletPage.value = value
  loadToilets()
}

const onOrderPage = (value) => {
  orderPage.value = value
  loadOrders()
}

const overdueOrderText = (order) => {
  if (!order.expect_finish_at) return '-'
  const minutes = Math.floor((Date.now() - new Date(order.expect_finish_at).getTime()) / 60000)
  return minutes > 0 ? formatDuration(minutes) : '-'
}

const createOrder = async (toilet) => {
  try {
    await ElMessageBox.confirm(
      `将为「${toilet.name}」生成清洁工单，派单后由保洁处理，确定继续吗？`,
      '生成清洁工单',
      { confirmButtonText: '生成', cancelButtonText: '取消', type: 'info' },
    )
  } catch {
    return
  }
  creatingId.value = toilet.id
  try {
    await createCleanOrder(toilet.id)
    ElMessage.success('清洁工单已生成，可前往 AI 派单')
    await loadAll()
  } finally {
    creatingId.value = null
  }
}

onMounted(loadAll)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.alerts-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.stat-card {
  background: #fff;
  border-radius: $cct-radius;
  box-shadow: $cct-shadow;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;

  .label {
    font-size: 12px;
    color: $cct-text-light;
  }

  strong {
    font-size: 24px;
  }

  .hint {
    font-size: 11px;
    color: #9aa8b0;
  }
}

.danger {
  color: $cct-danger;
}

.warning {
  color: $cct-warning;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  gap: 12px;
  flex-wrap: wrap;
}

.tabs {
  display: flex;
  gap: 6px;
  background: #f2f7f8;
  padding: 4px;
  border-radius: 10px;
}

.tab {
  border: none;
  background: transparent;
  padding: 7px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: $cct-text-light;
  cursor: pointer;

  &.active {
    background: #fff;
    color: $cct-primary;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(15, 76, 86, 0.08);
  }
}

.tools {
  display: flex;
  gap: 10px;
  align-items: center;
}

.level-select {
  width: 130px;
}

.toilet-name {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 2px;
}

.danger-text {
  color: $cct-danger;
  font-weight: 600;
  font-size: 13px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding-top: 14px;
}

@media (max-width: 1200px) {
  .summary-cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>