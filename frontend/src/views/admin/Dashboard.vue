<template>
  <div v-loading="loading" class="dashboard">
    <section class="welcome">
      <div>
        <h2>欢迎，{{ store.displayName }}</h2>
        <p class="muted">数据驾驶舱 · 实时掌握厕所、工单与服务质量</p>
      </div>
      <div class="welcome-actions">
        <span class="time">{{ serverTime }}</span>
        <el-button :icon="Refresh" size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </section>

    <section class="cards">
      <div class="stat-card">
        <span class="label">厕所总数</span>
        <strong>{{ overview?.toilet_total ?? 0 }}</strong>
        <span class="hint">公共 {{ overview?.public_total ?? 0 }} · 宿舍 {{ overview?.dorm_total ?? 0 }}</span>
      </div>
      <div class="stat-card">
        <span class="label">今日工单</span>
        <strong>{{ overview?.today_orders ?? 0 }}</strong>
        <span class="hint">完成 {{ overview?.today_done ?? 0 }} · 处理中 {{ overview?.processing_orders ?? 0 }}</span>
      </div>
      <div class="stat-card clickable" @click="router.push('/admin/orders')">
        <span class="label">待派单</span>
        <strong class="warning">{{ overview?.pending_orders ?? 0 }}</strong>
        <span class="hint">点击进入工单看板</span>
      </div>
      <div class="stat-card clickable" @click="router.push('/admin/alerts')">
        <span class="label">超时工单</span>
        <strong class="danger">{{ overview?.overdue_orders ?? 0 }}</strong>
        <span class="hint">超出响应时限</span>
      </div>
      <div class="stat-card clickable" @click="router.push('/admin/alerts')">
        <span class="label">超时未打扫</span>
        <strong class="danger">{{ overview?.overdue_toilets ?? 0 }}</strong>
        <span class="hint">紧急 {{ alertSummary?.overdue_toilets?.urgent ?? 0 }} 间</span>
      </div>
      <div class="stat-card">
        <span class="label">服务满意度</span>
        <strong>{{ overview?.avg_rating ?? 0 }}</strong>
        <span class="hint">共 {{ overview?.evaluation_count ?? 0 }} 条评价 · 平均 {{ overview?.avg_duration_min ?? 0 }} 分钟</span>
      </div>
    </section>

    <section class="charts">
      <div class="page-card chart-card wide">
        <div class="card-head">
          <h3>近 7 天工单趋势</h3>
          <span class="muted">新建 / 完成</span>
        </div>
        <EChart :option="trendOption" height="280px" />
      </div>
      <div class="page-card chart-card">
        <div class="card-head">
          <h3>工单类型分布</h3>
        </div>
        <EChart :option="typeOption" height="280px" />
      </div>
    </section>

    <section class="charts">
      <div class="page-card chart-card">
        <div class="card-head">
          <h3>厕所评分 Top5</h3>
          <span class="muted">满分 5 分</span>
        </div>
        <EChart :option="toiletOption" height="260px" />
      </div>
      <div class="page-card chart-card">
        <div class="card-head">
          <h3>员工绩效 Top5</h3>
          <el-button link type="primary" size="small" @click="router.push('/admin/staffs')">员工管理</el-button>
        </div>
        <div class="staff-list">
          <div v-for="(staff, index) in staffRank" :key="staff.id" class="staff-row">
            <span class="rank" :class="{ top: index < 3 }">{{ index + 1 }}</span>
            <div class="staff-info">
              <strong>{{ staff.name }}</strong>
              <span class="muted">{{ staff.staff_no }} · {{ workTypeText(staff.work_type) }}</span>
            </div>
            <div class="staff-metrics">
              <strong>{{ staff.done_count }}</strong>
              <span>完成单</span>
            </div>
            <div class="staff-metrics">
              <strong>{{ staff.avg_duration_min }}′</strong>
              <span>平均时效</span>
            </div>
            <el-tag size="small" type="success" effect="plain">{{ staff.avg_score.toFixed(1) }} 分</el-tag>
          </div>
          <el-empty v-if="!staffRank.length" description="暂无员工绩效数据" :image-size="60" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import EChart from '@/components/EChart.vue'
import { fetchAlertSummary } from '@/api/alert'
import {
  fetchOrdersTrend,
  fetchOverview,
  fetchStaffRanking,
  fetchToiletRanking,
  fetchTypeDistribution,
} from '@/api/stats'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

const loading = ref(false)
const overview = ref(null)
const trend = ref(null)
const distribution = ref(null)
const toiletRank = ref([])
const staffRank = ref([])
const alertSummary = ref(null)

const serverTime = computed(() => {
  const raw = overview.value?.server_time
  return raw ? String(raw).replace('T', ' ').slice(0, 16) : ''
})

const workTypeText = (type) => ({ cleaner: '保洁', plumber: '维修', all: '综合' })[type] || type

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['新建工单', '完成工单'], right: 0, top: 0, itemWidth: 12, itemHeight: 8 },
  grid: { left: 8, right: 16, top: 42, bottom: 4, containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: trend.value?.dates || [],
    axisLine: { lineStyle: { color: '#dbe7e9' } },
    axisLabel: { color: '#7b8b95', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    minInterval: 1,
    splitLine: { lineStyle: { color: '#eef4f5' } },
    axisLabel: { color: '#7b8b95', fontSize: 11 },
  },
  series: [
    {
      name: '新建工单',
      type: 'line',
      smooth: true,
      symbolSize: 6,
      data: trend.value?.created || [],
      itemStyle: { color: '#0ea5a4' },
      lineStyle: { width: 2.5 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(14,165,164,0.28)' },
            { offset: 1, color: 'rgba(14,165,164,0.02)' },
          ],
        },
      },
    },
    {
      name: '完成工单',
      type: 'line',
      smooth: true,
      symbolSize: 6,
      data: trend.value?.finished || [],
      itemStyle: { color: '#22c55e' },
      lineStyle: { width: 2.5, type: 'dashed' },
    },
  ],
}))

const typeOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}：{c} 单（{d}%）' },
  legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
  color: ['#0ea5a4', '#38bdf8', '#f59e0b', '#a78bfa'],
  series: [
    {
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{c}' },
      data: (distribution.value?.types || []).map((item) => ({ name: item.label, value: item.value })),
    },
  ],
}))

const toiletOption = computed(() => {
  const items = toiletRank.value
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 40, top: 10, bottom: 4, containLabel: true },
    xAxis: {
      type: 'value',
      max: 5,
      splitLine: { lineStyle: { color: '#eef4f5' } },
      axisLabel: { color: '#7b8b95', fontSize: 11 },
    },
    yAxis: {
      type: 'category',
      data: items.map((item) => item.code).reverse(),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#5c6f78', fontSize: 11 },
    },
    series: [
      {
        type: 'bar',
        barWidth: 12,
        data: items.map((item) => item.avg_score).reverse(),
        itemStyle: { color: '#0ea5a4', borderRadius: [0, 6, 6, 0] },
        label: { show: true, position: 'right', formatter: '{c}', color: '#5c6f78', fontSize: 11 },
      },
    ],
  }
})

const load = async () => {
  loading.value = true
  try {
    const [ov, tr, di, toi, sta, al] = await Promise.all([
      fetchOverview(),
      fetchOrdersTrend(7),
      fetchTypeDistribution(),
      fetchToiletRanking(5),
      fetchStaffRanking(5),
      fetchAlertSummary(),
    ])
    overview.value = ov
    trend.value = tr
    distribution.value = di
    toiletRank.value = toi
    staffRank.value = sta
    alertSummary.value = al
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.dashboard {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 300px;
}

.welcome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;

  h2 {
    margin: 0 0 6px;
    font-size: 21px;
  }

  p {
    margin: 0;
  }
}

.welcome-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time {
  font-size: 12px;
  color: $cct-text-light;
}

.cards {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
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
  transition: transform 0.15s ease;

  &.clickable {
    cursor: pointer;

    &:hover {
      transform: translateY(-2px);
    }
  }

  .label {
    font-size: 12px;
    color: $cct-text-light;
  }

  strong {
    font-size: 26px;
  }

  .hint {
    font-size: 11px;
    color: #9aa8b0;
  }
}

.warning {
  color: $cct-warning;
}

.danger {
  color: $cct-danger;
}

.charts {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
}

.chart-card {
  min-width: 0;
}

.card-head {
  display: flex;
  align-items: center;
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

.staff-list {
  display: flex;
  flex-direction: column;
  padding-top: 4px;
}

.staff-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed $cct-border;

  &:last-child {
    border-bottom: none;
  }
}

.rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #f1f6f7;
  color: $cct-text-light;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  flex-shrink: 0;

  &.top {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: #fff;
    font-weight: 600;
  }
}

.staff-info {
  flex: 1;
  min-width: 0;

  strong {
    display: block;
    font-size: 13px;
  }

  span {
    font-size: 11px;
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.staff-metrics {
  text-align: center;
  min-width: 52px;

  strong {
    display: block;
    font-size: 14px;
  }

  span {
    font-size: 10px;
    color: $cct-text-light;
  }
}

@media (max-width: 1400px) {
  .cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1000px) {
  .charts {
    grid-template-columns: 1fr;
  }
}
</style>