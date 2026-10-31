<template>
  <div class="tasks">
    <section class="hero">
      <div>
        <p class="greeting">{{ greeting }}，{{ store.displayName }}</p>
        <p class="sub">工号 {{ store.user?.username }} · 今日待办 {{ total }} 单</p>
      </div>
      <el-button class="refresh" size="small" :loading="loading" @click="load">刷新</el-button>
    </section>

    <div v-loading="loading" class="groups">
      <section class="group">
        <div class="group-head">
          <h3>待接单 <span class="count">{{ assigned.length }}</span></h3>
          <span class="muted">尽快接单避免超时</span>
        </div>
        <article v-for="order in assigned" :key="order.id" class="task-card" @click="go(order.id)">
          <div class="task-head">
            <el-tag size="small" type="primary" effect="plain">{{ order.type_text }}</el-tag>
            <el-tag size="small" :type="priorityMeta(order.priority).type" effect="plain">{{ order.priority_text }}</el-tag>
            <el-tag v-if="isOrderOverdue(order)" size="small" type="danger" effect="dark">超时</el-tag>
          </div>
          <h4>{{ order.title }}</h4>
          <p class="loc">{{ order.toilet_name }} · {{ order.building }} 栋 {{ order.floor }} 层</p>
          <div class="task-foot">
            <span>{{ formatTime(order.assigned_at) }} 派单</span>
            <span :class="{ danger: isOrderOverdue(order) }">{{ timeLeftText(order) }}</span>
          </div>
        </article>
        <el-empty v-if="!assigned.length" description="暂无待接工单" :image-size="70" />
      </section>

      <section class="group">
        <div class="group-head">
          <h3>处理中 <span class="count">{{ processing.length }}</span></h3>
          <span class="muted">完工后请上传照片</span>
        </div>
        <article v-for="order in processing" :key="order.id" class="task-card" @click="go(order.id)">
          <div class="task-head">
            <el-tag size="small" type="success" effect="plain">{{ order.type_text }}</el-tag>
            <el-tag v-if="isOrderOverdue(order)" size="small" type="danger" effect="dark">超时</el-tag>
          </div>
          <h4>{{ order.title }}</h4>
          <p class="loc">{{ order.toilet_name }} · {{ order.building }} 栋 {{ order.floor }} 层</p>
          <div class="task-foot">
            <span>{{ formatTime(order.accepted_at) }} 接单</span>
            <span :class="{ danger: isOrderOverdue(order) }">{{ timeLeftText(order) }}</span>
          </div>
        </article>
        <el-empty v-if="!processing.length" description="暂无处理中工单" :image-size="70" />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchStaffTasks } from '@/api/order'
import { useUserStore } from '@/stores/user'
import { formatTime, isOrderOverdue, priorityMeta, timeLeftText } from '@/utils/dict'

const router = useRouter()
const store = useUserStore()
const loading = ref(false)
const assigned = ref([])
const processing = ref([])

const total = computed(() => assigned.value.length + processing.value.length)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '凌晨好'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const load = async () => {
  loading.value = true
  try {
    const data = await fetchStaffTasks({ page: 1, size: 50 })
    assigned.value = data.list.filter((item) => item.status === 'assigned')
    processing.value = data.list.filter((item) => item.status === 'processing')
  } finally {
    loading.value = false
  }
}

const go = (id) => router.push(`/staff/tasks/${id}`)

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.tasks {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px;
  border-radius: $cct-radius;
  color: #fff;
  background: linear-gradient(135deg, #0f5760 0%, #148a92 100%);
  box-shadow: 0 10px 24px rgba(15, 87, 96, 0.25);
}

.refresh {
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #fff;
}

.greeting {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.sub {
  margin: 6px 0 0;
  font-size: 12px;
  opacity: 0.85;
}

.groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 160px;
}

.group-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;

  h3 {
    margin: 0;
    font-size: 15px;
  }

  .muted {
    font-size: 11px;
  }
}

.count {
  display: inline-block;
  min-width: 20px;
  padding: 0 6px;
  margin-left: 4px;
  border-radius: 999px;
  background: #e6f7f6;
  color: $cct-primary;
  font-size: 11px;
  text-align: center;
}

.task-card {
  background: #fff;
  border-radius: $cct-radius;
  box-shadow: $cct-shadow;
  padding: 14px;
  margin-bottom: 10px;
  cursor: pointer;

  h4 {
    margin: 8px 0 6px;
    font-size: 15px;
  }
}

.task-head {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.loc {
  margin: 0 0 10px;
  font-size: 12px;
  color: $cct-text-light;
}

.task-foot {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #9aa8b0;
}

.danger {
  color: $cct-danger;
  font-weight: 600;
}
</style>