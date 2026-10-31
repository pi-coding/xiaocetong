<template>
  <div class="orders">
    <div class="status-bar">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="chip"
        :class="{ active: status === tab.value }"
        @click="switchStatus(tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-loading="loading" class="list">
      <article v-for="order in list" :key="order.id" class="order-card" @click="go(order.id)">
        <div class="head">
          <div class="type">
            <el-icon :size="16"><component :is="ORDER_TYPE_ICON[order.type] || 'Tickets'" /></el-icon>
            <span>{{ order.type_text }}</span>
          </div>
          <el-tag :type="orderStatus(order.status).type" size="small">{{ order.status_text }}</el-tag>
        </div>
        <h3>{{ order.title }}</h3>
        <p class="location">{{ order.toilet_name }} · {{ order.building }} 栋 {{ order.floor }} 层</p>
        <div class="foot">
          <span class="time">{{ formatTime(order.created_at) }}</span>
          <div class="badges">
            <el-tag v-if="isOrderOverdue(order)" size="small" type="danger" effect="dark">超时</el-tag>
            <el-tag size="small" effect="plain" :type="priorityMeta(order.priority).type">
              {{ order.priority_text }}
            </el-tag>
            <el-tag v-if="order.urge_count" size="small" effect="plain" type="warning">已催 {{ order.urge_count }} 次</el-tag>
          </div>
        </div>
      </article>

      <el-empty v-if="!loading && !list.length" description="暂无工单" :image-size="90" />
    </div>

    <el-pagination
      v-if="total > size"
      class="pager"
      small
      background
      layout="prev, pager, next"
      :total="total"
      :page-size="size"
      :current-page="page"
      @current-change="onPageChange"
    />

    <button type="button" class="new-order" @click="router.push('/student/orders/create')">
      <el-icon :size="18"><Plus /></el-icon>
      <span>提交新工单</span>
    </button>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMyOrders } from '@/api/order'
import {
  ORDER_TYPE_ICON,
  formatTime,
  isOrderOverdue,
  orderStatus,
  priorityMeta,
} from '@/utils/dict'

const router = useRouter()
const tabs = [
  { label: '全部', value: '' },
  { label: '待派单', value: 'pending' },
  { label: '已派单', value: 'assigned' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'done' },
  { label: '已取消', value: 'cancelled' },
]

const status = ref('')
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (status.value) params.status = status.value
    const data = await fetchMyOrders(params)
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

const switchStatus = (value) => {
  status.value = value
  page.value = 1
  load()
}

const onPageChange = (value) => {
  page.value = value
  load()
}

const go = (id) => router.push(`/student/orders/${id}`)

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.orders {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 52px;
}

.status-bar {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;

  &::-webkit-scrollbar {
    display: none;
  }
}

.chip {
  flex-shrink: 0;
  border: 1px solid $cct-border;
  background: #fff;
  color: $cct-text-light;
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  cursor: pointer;

  &.active {
    background: $cct-primary;
    border-color: $cct-primary;
    color: #fff;
  }
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 140px;
}

.order-card {
  background: #fff;
  border-radius: $cct-radius;
  box-shadow: $cct-shadow;
  padding: 14px;
  cursor: pointer;

  h3 {
    margin: 8px 0 6px;
    font-size: 15px;
  }
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.type {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: $cct-primary;
}

.location {
  margin: 0 0 10px;
  font-size: 12px;
  color: $cct-text-light;
}

.foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.time {
  font-size: 11px;
  color: #9aa8b0;
}

.badges {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.pager {
  justify-content: center;
}

.new-order {
  position: fixed;
  bottom: 74px;
  left: 50%;
  transform: translateX(-50%);
  width: min(420px, calc(100vw - 64px));
  height: 44px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, $cct-primary, #12b8b6);
  color: #fff;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  box-shadow: 0 8px 20px rgba(14, 165, 164, 0.35);
  cursor: pointer;
}
</style>