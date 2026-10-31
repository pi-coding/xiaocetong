<template>
  <div class="dispatch-page">
    <section class="page-card intro">
      <div class="intro-head">
        <div>
          <h2>AI 智能派单</h2>
          <p class="muted">基于可解释加权评分，为每张待派工单推荐最合适的在岗员工</p>
        </div>
        <div class="intro-actions">
          <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
          <el-button type="primary" :loading="batchRunning" :disabled="!items.length" @click="batchDispatch">
            一键 AI 派单
          </el-button>
        </div>
      </div>
      <div class="weights">
        <div v-for="weight in weightList" :key="weight.key" class="weight">
          <span class="weight-label">{{ weight.label }}</span>
          <div class="weight-bar"><i :style="{ width: `${weight.value * 100}%` }" /></div>
          <span class="weight-value">{{ Math.round(weight.value * 100) }}%</span>
        </div>
      </div>
      <p class="muted hint">候选员工已按「在岗 + 工种匹配 + 未超日单量」过滤，得分越高越优先。</p>
    </section>

    <div v-loading="loading" class="dispatch-list">
      <section v-for="item in items" :key="item.order.id" class="order-block page-card">
        <header class="order-head">
          <div>
            <div class="order-title">
              <el-tag size="small" effect="plain">{{ item.order.type_text }}</el-tag>
              <h3>{{ item.order.title }}</h3>
            </div>
            <p class="muted">
              {{ item.order.order_no }} · {{ item.order.toilet_name }} · {{ item.order.building }} 栋
              {{ item.order.floor }} 层 · {{ item.order.priority_text }}优先级
            </p>
          </div>
          <span class="wait">已等待 {{ waitText(item.order.created_at) }}</span>
        </header>

        <div v-if="item.candidates.length" class="candidates">
          <div
            v-for="(staff, index) in item.candidates"
            :key="staff.staff_id"
            class="candidate"
            :class="{ best: index === 0 }"
          >
            <div class="candidate-main">
              <div class="rank">{{ index + 1 }}</div>
              <div class="who">
                <strong>{{ staff.name }}</strong>
                <span class="muted">{{ staff.staff_no }} · {{ workTypeText(staff.work_type) }} · {{ staff.area || '未设区域' }}</span>
              </div>
              <div class="score" :class="scoreClass(staff.score)">
                <strong>{{ staff.score }}</strong>
                <span>综合分</span>
              </div>
            </div>

            <div class="factors">
              <div v-for="factor in factorList(staff.factors)" :key="factor.key" class="factor">
                <span>{{ factor.label }}</span>
                <div class="factor-bar"><i :style="{ width: `${factor.value}%` }" /></div>
                <span class="factor-value">{{ factor.value }}</span>
              </div>
            </div>

            <div class="candidate-foot">
              <div class="reasons">
                <span v-for="reason in staff.reasons" :key="reason" class="reason">{{ reason }}</span>
              </div>
              <el-button
                type="primary"
                size="small"
                :loading="actingId === `${item.order.id}-${staff.staff_id}`"
                @click="dispatch(item.order, staff)"
              >
                派给 TA
              </el-button>
            </div>
          </div>
        </div>

        <el-empty v-else description="暂无满足条件的员工，请检查排班或日单量上限" :image-size="60" />
      </section>

      <el-empty v-if="!loading && !items.length" description="当前没有待派工单" :image-size="90" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { assignOrder, fetchDispatchSuggestions, runAiDispatch } from '@/api/order'

const items = ref([])
const loading = ref(false)
const batchRunning = ref(false)
const actingId = ref('')
const weights = ref({ idle: 0.35, speed: 0.25, rating: 0.2, area: 0.2 })

const weightList = computed(() => [
  { key: 'idle', label: '空闲度', value: weights.value.idle },
  { key: 'speed', label: '历史时效', value: weights.value.speed },
  { key: 'rating', label: '服务评分', value: weights.value.rating },
  { key: 'area', label: '区域匹配', value: weights.value.area },
])

const factorList = (factors) => [
  { key: 'idle', label: '空闲', value: factors.idle },
  { key: 'speed', label: '时效', value: factors.speed },
  { key: 'rating', label: '评分', value: factors.rating },
  { key: 'area', label: '区域', value: factors.area },
]

const workTypeText = (type) => ({ cleaner: '保洁', plumber: '维修', all: '综合' })[type] || type

const scoreClass = (score) => (score >= 80 ? 'high' : score >= 65 ? 'mid' : 'low')

const waitText = (createdAt) => {
  if (!createdAt) return '-'
  const minutes = Math.max(0, Math.floor((Date.now() - new Date(createdAt).getTime()) / 60000))
  if (minutes < 60) return `${minutes} 分钟`
  return `${Math.floor(minutes / 60)} 小时 ${minutes % 60} 分`
}

const load = async () => {
  loading.value = true
  try {
    const data = await fetchDispatchSuggestions({ limit: 3 })
    items.value = data
    if (data.length) weights.value = data[0].weights
  } finally {
    loading.value = false
  }
}

const dispatch = async (order, staff) => {
  actingId.value = `${order.id}-${staff.staff_id}`
  try {
    await assignOrder(order.id, staff.staff_id, { from_ai: true, dispatch_score: staff.score })
    ElMessage.success(`已派给 ${staff.name}（${staff.score} 分）`)
    await load()
  } finally {
    actingId.value = ''
  }
}

const batchDispatch = async () => {
  try {
    await ElMessageBox.confirm(
      `将按 AI 推荐为当前 ${items.value.length} 张待派工单自动派单，确定继续吗？`,
      '一键 AI 派单',
      { confirmButtonText: '开始派单', cancelButtonText: '取消', type: 'info' },
    )
  } catch {
    return
  }
  batchRunning.value = true
  try {
    const result = await runAiDispatch([])
    ElMessage.success(`成功 ${result.dispatched.length} 单${result.failed.length ? `，失败 ${result.failed.length} 单` : ''}`)
    await load()
  } finally {
    batchRunning.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.dispatch-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.intro-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;

  h2 {
    margin: 0 0 6px;
    font-size: 20px;
  }

  p {
    margin: 0;
  }
}

.intro-actions {
  display: flex;
  gap: 10px;
}

.weights {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-top: 18px;
}

.weight {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.weight-label {
  width: 56px;
  color: $cct-text-light;
  flex-shrink: 0;
}

.weight-bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: #eaf2f3;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    background: linear-gradient(90deg, $cct-primary, #38d0b8);
    border-radius: 4px;
  }
}

.weight-value {
  width: 34px;
  text-align: right;
  color: $cct-primary;
  font-weight: 600;
}

.hint {
  margin: 14px 0 0;
}

.dispatch-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.order-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed $cct-border;
}

.order-title {
  display: flex;
  align-items: center;
  gap: 8px;

  h3 {
    margin: 0;
    font-size: 16px;
  }
}

.order-head .muted {
  margin: 6px 0 0;
}

.wait {
  font-size: 12px;
  color: $cct-warning;
  white-space: nowrap;
}

.candidates {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.candidate {
  border: 1px solid $cct-border;
  border-radius: 12px;
  padding: 14px;
  background: #fbfdfd;
  display: flex;
  flex-direction: column;
  gap: 10px;

  &.best {
    border-color: #9fe0df;
    background: #f3fbfb;
    box-shadow: 0 6px 16px rgba(14, 165, 164, 0.1);
  }
}

.candidate-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #e6f7f6;
  color: $cct-primary;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.who {
  flex: 1;
  min-width: 0;

  strong {
    display: block;
    font-size: 14px;
  }

  span {
    font-size: 11px;
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.score {
  text-align: right;

  strong {
    display: block;
    font-size: 20px;
    line-height: 1.1;
  }

  span {
    font-size: 10px;
    color: $cct-text-light;
  }

  &.high strong {
    color: #16a34a;
  }

  &.mid strong {
    color: $cct-warning;
  }

  &.low strong {
    color: #9aa8b0;
  }
}

.factors {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}

.factor {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: $cct-text-light;
}

.factor-bar {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  background: #e8f1f2;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    background: $cct-primary;
  }
}

.factor-value {
  width: 26px;
  text-align: right;
}

.candidate-foot {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
}

.reasons {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.reason {
  font-size: 11px;
  color: #7b8b95;
  line-height: 1.4;

  &::before {
    content: '·';
    margin-right: 4px;
    color: $cct-primary;
  }
}

@media (max-width: 1200px) {
  .candidates {
    grid-template-columns: 1fr;
  }

  .weights {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>