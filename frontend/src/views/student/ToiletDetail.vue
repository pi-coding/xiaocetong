<template>
  <div v-loading="loading" class="detail">
    <template v-if="toilet">
      <section class="hero">
        <div class="hero-head">
          <div>
            <h2>{{ toilet.name }}</h2>
            <p class="code">{{ toilet.code }} · {{ toilet.type === 'dorm' ? '宿舍厕所' : '公共厕所' }}</p>
          </div>
          <el-tag :type="toiletStatus(toilet.status).type" effect="dark" round>
            {{ toiletStatus(toilet.status).label }}
          </el-tag>
        </div>
        <div class="hero-score">
          <div><strong>{{ scoreText(toilet.avg_score) }}</strong><span>平均评分</span></div>
          <div><strong>{{ toilet.order_count }}</strong><span>累计工单</span></div>
          <div><strong>{{ toilet.stall_count }}</strong><span>蹲位数量</span></div>
        </div>
      </section>

      <el-alert
        v-if="toilet.warn_level > 0"
        :title="warnTitle"
        :type="toilet.warn_level >= 2 ? 'error' : 'warning'"
        :closable="false"
        show-icon
      />

      <section class="page-card">
        <h3 class="card-title">基础信息</h3>
        <div class="info-row"><span>位置</span><strong>{{ toilet.location_desc || '-' }}</strong></div>
        <div class="info-row"><span>楼栋 / 楼层</span><strong>{{ toilet.building }} 栋 {{ toilet.floor }} 层</strong></div>
        <div class="info-row"><span>适用人群</span><strong>{{ GENDER_TEXT[toilet.gender] || toilet.gender }}</strong></div>
        <div class="info-row"><span>负责保洁</span><strong>{{ toilet.cleaner_name || '待指派' }}</strong></div>
        <div class="info-row"><span>清洁周期</span><strong>{{ formatDuration(toilet.clean_interval_min) }}</strong></div>
        <div class="info-row"><span>最近清洁</span><strong>{{ formatTime(toilet.last_cleaned_at) }}</strong></div>
        <div class="info-row"><span>清洁状态</span><strong :class="toilet.warn_level ? 'text-danger' : 'text-ok'">{{ cleanStatusText(toilet) }}</strong></div>
        <div class="info-row"><span>处理中工单</span><strong>{{ toilet.active_order_count }} 单</strong></div>
        <div v-if="toilet.remark" class="info-row"><span>备注</span><strong>{{ toilet.remark }}</strong></div>
      </section>

      <section v-if="logs.length" class="page-card">
        <h3 class="card-title">最近清洁记录</h3>
        <div v-for="log in logs" :key="log.id" class="cleaning-log">
          <div class="log-head">
            <strong>{{ formatTime(log.cleaned_at) }}</strong>
            <el-tag size="small" :type="log.result === 'pass' ? 'success' : 'danger'" effect="plain">
              {{ log.result === 'pass' ? '合格' : '不合格' }}
            </el-tag>
          </div>
          <p class="log-meta">
            {{ log.staff_name }} · {{ log.clean_type_text }}
            <span v-if="log.duration_min"> · 耗时 {{ log.duration_min }} 分钟</span>
          </p>
          <div class="log-tags">
            <el-tag v-for="item in log.clean_items" :key="item" size="small" effect="plain" type="info">{{ item }}</el-tag>
          </div>
        </div>
      </section>

      <section class="page-card">
        <h3 class="card-title">遇到问题？</h3>
        <div class="actions">
          <button v-for="action in actions" :key="action.type" type="button" class="action" @click="createOrder(action.type)">
            <el-icon :size="22"><component :is="action.icon" /></el-icon>
            <div>
              <strong>{{ action.title }}</strong>
              <span>{{ action.desc }}</span>
            </div>
          </button>
        </div>
      </section>

      <el-button class="back" @click="router.back()">返回</el-button>
    </template>

    <el-empty v-else-if="!loading" description="未找到该厕所">
      <el-button type="primary" @click="router.replace('/student/toilets')">返回列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchToiletCleaningLogs } from '@/api/cleaning'
import { fetchToiletDetail } from '@/api/toilet'
import { studentTabs } from '@/router/menus'
import {
  GENDER_TEXT,
  cleanStatusText,
  formatDuration,
  formatTime,
  scoreText,
  toiletStatus,
} from '@/utils/dict'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const toilet = ref(null)
const logs = ref([])

const actions = [
  { type: 'unclog', title: '通厕所', desc: '堵塞、反水、异味', icon: 'MagicStick' },
  { type: 'clean', title: '要清洁', desc: '脏乱、垃圾满溢', icon: 'Brush' },
  { type: 'repair', title: '报修', desc: '冲水阀、门锁、灯具损坏', icon: 'Tools' },
]

const orderEnabled = computed(() => Boolean(studentTabs.find((item) => item.path === '/student/orders')?.enabled))

const warnTitle = computed(() => {
  if (!toilet.value) return ''
  if (toilet.value.never_cleaned) return '该厕所暂无清洁记录，建议尽快安排保洁'
  return `该厕所已超出清洁周期：${cleanStatusText(toilet.value)}`
})

const load = async () => {
  loading.value = true
  try {
    const [detail, logPage] = await Promise.all([
      fetchToiletDetail(route.params.id),
      fetchToiletCleaningLogs(route.params.id, { page: 1, size: 3 }),
    ])
    toilet.value = detail
    logs.value = logPage.list
  } catch {
    toilet.value = null
    logs.value = []
  } finally {
    loading.value = false
  }
}

const createOrder = (type) => {
  if (!orderEnabled.value) {
    ElMessage.info('工单模块将在下一模块上线，届时可从本页直接下单')
    return
  }
  router.push({ path: '/student/orders/create', query: { toiletId: toilet.value.id, type } })
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}

.hero {
  border-radius: $cct-radius;
  padding: 18px;
  color: #fff;
  background: linear-gradient(135deg, #0e7c80 0%, #12b8b6 100%);
  box-shadow: 0 10px 24px rgba(14, 165, 164, 0.26);
}

.hero-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;

  h2 {
    margin: 0 0 6px;
    font-size: 19px;
  }
}

.code {
  margin: 0;
  font-size: 12px;
  opacity: 0.85;
}

.hero-score {
  display: flex;
  gap: 30px;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.22);

  strong {
    display: block;
    font-size: 20px;
  }

  span {
    font-size: 11px;
    opacity: 0.82;
  }
}

.card-title {
  margin: 0 0 12px;
  font-size: 15px;
}

.cleaning-log {
  padding: 10px 0;
  border-bottom: 1px dashed $cct-border;

  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
}

.log-head {
  display: flex;
  align-items: center;
  justify-content: space-between;

  strong {
    font-size: 13px;
    font-weight: 500;
  }
}

.log-meta {
  margin: 4px 0 6px;
  font-size: 11px;
  color: $cct-text-light;
}

.log-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 9px 0;
  border-bottom: 1px dashed $cct-border;
  font-size: 13px;

  &:last-child {
    border-bottom: none;
  }

  span {
    color: $cct-text-light;
    flex-shrink: 0;
  }

  strong {
    text-align: right;
    font-weight: 500;
  }
}

.text-danger {
  color: $cct-danger;
}

.text-ok {
  color: #16a34a;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid $cct-border;
  background: #fafcfc;
  text-align: left;
  cursor: pointer;

  &:hover {
    border-color: $cct-primary;
    background: #f1fbfb;
  }

  div {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  strong {
    font-size: 14px;
  }

  span {
    font-size: 12px;
    color: $cct-text-light;
  }

  .el-icon {
    color: $cct-primary;
  }
}

.back {
  width: 100%;
}
</style>