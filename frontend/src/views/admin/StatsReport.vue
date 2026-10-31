<template>
  <div v-loading="loading" class="stats">
    <section class="page-card toolbar">
      <div class="filters">
        <el-radio-group v-model="days" size="small" @change="loadTrend">
          <el-radio-button :value="7">近 7 天</el-radio-button>
          <el-radio-button :value="14">近 14 天</el-radio-button>
          <el-radio-button :value="30">近 30 天</el-radio-button>
        </el-radio-group>
        <span class="muted">按工单提交日期统计</span>
      </div>
      <div class="actions">
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
        <el-button type="primary" :icon="Download" :loading="exporting" @click="exportCsv">导出工单明细</el-button>
      </div>
    </section>

    <section class="page-card">
      <div class="card-head">
        <h3>工单量趋势</h3>
        <span class="muted">新建工单与完工对比</span>
      </div>
      <EChart :option="trendOption" height="300px" />
    </section>

    <section class="grid-2">
      <div class="page-card">
        <div class="card-head"><h3>工单类型分布</h3></div>
        <EChart :option="typeOption" height="280px" />
      </div>
      <div class="page-card">
        <div class="card-head"><h3>工单状态分布</h3></div>
        <EChart :option="statusOption" height="280px" />
      </div>
    </section>

    <section class="grid-2">
      <div class="page-card">
        <div class="card-head"><h3>楼栋工单热力</h3><span class="muted">工单量 / 超时数</span></div>
        <EChart :option="buildingOption" height="280px" />
      </div>
      <div class="page-card">
        <div class="card-head"><h3>评价星级分布</h3><span class="muted">共 {{ evaluation.total }} 条</span></div>
        <EChart :option="evaluationOption" height="280px" />
      </div>
    </section>

    <section class="grid-2">
      <div class="page-card">
        <div class="card-head"><h3>厕所评分排行</h3></div>
        <el-table :data="toiletRank" size="small" stripe>
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="code" label="编号" width="110" />
          <el-table-column prop="name" label="厕所" min-width="150" show-overflow-tooltip />
          <el-table-column prop="building" label="楼栋" width="70" />
          <el-table-column label="评分" width="90">
            <template #default="{ row }">{{ row.avg_score.toFixed(1) }}</template>
          </el-table-column>
          <el-table-column prop="order_count" label="工单" width="70" />
        </el-table>
      </div>
      <div class="page-card">
        <div class="card-head"><h3>员工绩效排行</h3></div>
        <el-table :data="staffRank" size="small" stripe>
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="staff_no" label="工号" width="100" />
          <el-table-column prop="name" label="姓名" width="90" />
          <el-table-column prop="done_count" label="完成单" width="80" />
          <el-table-column label="平均时效" width="90">
            <template #default="{ row }">{{ row.avg_duration_min }} 分</template>
          </el-table-column>
          <el-table-column label="评分" width="80">
            <template #default="{ row }">{{ row.avg_score.toFixed(1) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh } from '@element-plus/icons-vue'
import EChart from '@/components/EChart.vue'
import {
  downloadOrdersCsv,
  fetchBuildingHeat,
  fetchEvaluationSummary,
  fetchOrdersTrend,
  fetchStaffRanking,
  fetchToiletRanking,
  fetchTypeDistribution,
} from '@/api/stats'

const loading = ref(false)
const exporting = ref(false)
const days = ref(7)
const trend = ref(null)
const distribution = ref(null)
const building = ref([])
const evaluation = ref({ distribution: [], total: 0 })
const toiletRank = ref([])
const staffRank = ref([])

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['新建工单', '完成工单'], right: 0, top: 0, itemWidth: 12, itemHeight: 8 },
  grid: { left: 8, right: 20, top: 42, bottom: 4, containLabel: true },
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
            { offset: 0, color: 'rgba(14,165,164,0.3)' },
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
      radius: ['40%', '66%'],
      center: ['50%', '46%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{c}' },
      data: (distribution.value?.types || []).map((item) => ({ name: item.label, value: item.value })),
    },
  ],
}))

const statusOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}：{c} 单（{d}%）' },
  legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
  color: ['#f59e0b', '#0ea5a4', '#3b82f6', '#22c55e', '#94a3b8', '#cbd5e1'],
  series: [
    {
      type: 'pie',
      radius: ['52%', '72%'],
      center: ['50%', '46%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: (distribution.value?.statuses || []).map((item) => ({ name: item.label, value: item.value })),
    },
  ],
}))

const buildingOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { data: ['工单量', '超时数'], right: 0, top: 0, itemWidth: 12, itemHeight: 8 },
  grid: { left: 8, right: 16, top: 42, bottom: 4, containLabel: true },
  xAxis: {
    type: 'category',
    data: building.value.map((item) => `${item.building} 栋`),
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
      name: '工单量',
      type: 'bar',
      barWidth: 18,
      data: building.value.map((item) => item.order_count),
      itemStyle: { color: '#0ea5a4', borderRadius: [6, 6, 0, 0] },
    },
    {
      name: '超时数',
      type: 'bar',
      barWidth: 18,
      data: building.value.map((item) => item.timeout_count),
      itemStyle: { color: '#f59e0b', borderRadius: [6, 6, 0, 0] },
    },
  ],
}))

const evaluationOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 8, right: 16, top: 20, bottom: 4, containLabel: true },
  xAxis: {
    type: 'category',
    data: evaluation.value.distribution.map((item) => `${item.score} 星`),
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
      type: 'bar',
      barWidth: 26,
      data: evaluation.value.distribution.map((item) => item.count),
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: '#38c9c8' },
            { offset: 1, color: '#0e7c80' },
          ],
        },
      },
      label: { show: true, position: 'top', color: '#5c6f78', fontSize: 11 },
    },
  ],
}))

const loadTrend = async () => {
  trend.value = await fetchOrdersTrend(days.value)
}

const load = async () => {
  loading.value = true
  try {
    const [tr, di, bh, es, toi, sta] = await Promise.all([
      fetchOrdersTrend(days.value),
      fetchTypeDistribution(),
      fetchBuildingHeat(),
      fetchEvaluationSummary(),
      fetchToiletRanking(10),
      fetchStaffRanking(10),
    ])
    trend.value = tr
    distribution.value = di
    building.value = bh
    evaluation.value = es
    toiletRank.value = toi
    staffRank.value = sta
  } finally {
    loading.value = false
  }
}

const exportCsv = async () => {
  exporting.value = true
  try {
    const response = await downloadOrdersCsv()
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `校厕通工单明细-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 300px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.filters {
  display: flex;
  align-items: center;
  gap: 12px;
}

.actions {
  display: flex;
  gap: 10px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;

  h3 {
    margin: 0;
    font-size: 15px;
  }

  .muted {
    font-size: 11px;
  }
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 1100px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
</style>