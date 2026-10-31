<template>
  <div class="points">
    <section class="balance-card">
      <div>
        <p class="label">我的积分</p>
        <strong>{{ balance }}</strong>
        <p class="hint">提交工单、完成服务、评价均可获得积分</p>
      </div>
      <el-icon :size="40"><Trophy /></el-icon>
    </section>

    <section class="page-card">
      <h3 class="card-title">积分规则</h3>
      <div v-for="rule in rules" :key="rule.source" class="rule">
        <div>
          <strong>{{ rule.label }}</strong>
          <p class="muted">{{ rule.desc }}</p>
        </div>
        <span class="plus">+{{ rule.points }}</span>
      </div>
    </section>

    <section class="page-card">
      <h3 class="card-title">积分排行榜</h3>
      <div v-for="item in ranking" :key="item.user_id" class="rank-row" :class="{ top: item.rank <= 3 }">
        <span class="rank">{{ item.rank }}</span>
        <span class="name">
          {{ item.name }}
          <small v-if="item.building"> · {{ item.building }} 栋</small>
        </span>
        <strong>{{ item.points_balance }}</strong>
      </div>
    </section>

    <section class="page-card">
      <div class="flex-between">
        <h3 class="card-title">积分明细</h3>
        <span class="muted">共 {{ total }} 条</span>
      </div>
      <div v-loading="loading">
        <div v-for="record in records" :key="record.id" class="record">
          <div>
            <strong>{{ record.source_text }}</strong>
            <p class="muted">{{ record.remark || record.source_text }} · {{ formatTime(record.created_at) }}</p>
          </div>
          <span :class="record.amount > 0 ? 'plus' : 'minus'">
            {{ record.amount > 0 ? '+' : '' }}{{ record.amount }}
          </span>
        </div>
        <el-empty v-if="!loading && !records.length" description="暂无积分记录" :image-size="70" />
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
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { fetchMyPoints, fetchPointsRanking, fetchPointsRules } from '@/api/points'
import { formatTime } from '@/utils/dict'

const balance = ref(0)
const records = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)
const ranking = ref([])
const rules = ref([])

const loadPoints = async () => {
  loading.value = true
  try {
    const data = await fetchMyPoints({ page: page.value, size: size.value })
    balance.value = data.balance
    records.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

const onPageChange = (value) => {
  page.value = value
  loadPoints()
}

onMounted(async () => {
  const [rankData, ruleData] = await Promise.all([fetchPointsRanking(10), fetchPointsRules()])
  ranking.value = rankData
  rules.value = ruleData.rules
  await loadPoints()
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.points {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.balance-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 20px;
  border-radius: $cct-radius;
  color: #fff;
  background: linear-gradient(135deg, #0e7c80 0%, #12b8b6 55%, #38d0b8 100%);
  box-shadow: 0 10px 24px rgba(14, 165, 164, 0.26);

  .label {
    margin: 0 0 6px;
    font-size: 12px;
    opacity: 0.88;
  }

  strong {
    font-size: 38px;
    line-height: 1;
  }

  .hint {
    margin: 10px 0 0;
    font-size: 11px;
    opacity: 0.82;
  }
}

.card-title {
  margin: 0 0 12px;
  font-size: 15px;
}

.rule {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px dashed $cct-border;

  &:last-child {
    border-bottom: none;
  }

  strong {
    font-size: 13px;
  }

  .muted {
    margin: 3px 0 0;
    font-size: 11px;
  }
}

.plus {
  color: #16a34a;
  font-weight: 600;
}

.minus {
  color: $cct-danger;
  font-weight: 600;
}

.rank-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px dashed $cct-border;
  font-size: 13px;

  &:last-child {
    border-bottom: none;
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
  }

  .name {
    flex: 1;
    small {
      color: $cct-text-light;
      font-size: 11px;
    }
  }

  &.top .rank {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: #fff;
    font-weight: 600;
  }
}

.record {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed $cct-border;

  &:last-child {
    border-bottom: none;
  }

  strong {
    font-size: 13px;
  }

  .muted {
    margin: 3px 0 0;
    font-size: 11px;
  }
}

.pager {
  justify-content: center;
  padding-top: 10px;
}
</style>