<template>
  <div v-loading="loading" class="detail">
    <template v-if="order">
      <section class="hero" :class="`status-${order.status}`">
        <div class="hero-top">
          <div>
            <p class="no">{{ order.order_no }}</p>
            <h2>{{ order.title }}</h2>
          </div>
          <el-tag :type="orderStatus(order.status).type" effect="dark" round>{{ order.status_text }}</el-tag>
        </div>
        <div class="hero-meta">
          <span>{{ order.type_text }}</span>
          <span>{{ order.priority_text }}优先级</span>
          <span>{{ order.toilet_name }}</span>
        </div>
        <div v-if="active" class="countdown" :class="{ overdue: isOrderOverdue(order) }">
          <el-icon><Timer /></el-icon>
          <span>{{ isOrderOverdue(order) ? '已超时，请耐心等待或催单' : timeLeftText(order) }}</span>
        </div>
      </section>

      <section class="page-card">
        <h3 class="card-title">处理进度</h3>
        <el-timeline>
          <el-timeline-item
            v-for="node in order.timeline"
            :key="node.key"
            :timestamp="formatTime(node.time)"
            :type="node.key === 'finished' ? 'success' : node.key === 'cancelled' ? 'info' : 'primary'"
          >
            <p class="node-title">{{ node.title }}</p>
            <p v-if="node.desc" class="node-desc">{{ node.desc }}</p>
          </el-timeline-item>
        </el-timeline>
      </section>

      <section class="page-card">
        <h3 class="card-title">工单信息</h3>
        <div class="info-row"><span>厕所</span><strong>{{ order.toilet_name }}</strong></div>
        <div class="info-row"><span>位置</span><strong>{{ order.location_desc || `${order.building} 栋 ${order.floor} 层` }}</strong></div>
        <div v-if="order.description" class="info-row"><span>问题描述</span><strong>{{ order.description }}</strong></div>
        <div class="info-row"><span>提交时间</span><strong>{{ formatTime(order.created_at) }}</strong></div>
        <div class="info-row"><span>响应时限</span><strong :class="{ danger: isOrderOverdue(order) }">{{ formatTime(order.expect_finish_at) }}</strong></div>
        <div class="info-row"><span>处理人</span><strong>{{ order.assignee_name || '待派单' }}</strong></div>
        <div v-if="order.assignee_phone" class="info-row"><span>联系电话</span><strong>{{ order.assignee_phone }}</strong></div>
        <div v-if="order.finished_at" class="info-row"><span>完成时间</span><strong>{{ formatTime(order.finished_at) }}</strong></div>
        <div v-if="order.finish_remark" class="info-row"><span>处理说明</span><strong>{{ order.finish_remark }}</strong></div>
      </section>

      <section v-if="order.images.length || order.finish_images.length" class="page-card">
        <h3 class="card-title">现场图片</h3>
        <div v-if="order.images.length" class="image-block">
          <p class="muted">报单照片</p>
          <div class="image-list">
            <el-image
              v-for="url in order.images"
              :key="url"
              :src="url"
              :preview-src-list="order.images"
              fit="cover"
              class="image"
            />
          </div>
        </div>
        <div v-if="order.finish_images.length" class="image-block">
          <p class="muted">完工照片</p>
          <div class="image-list">
            <el-image
              v-for="url in order.finish_images"
              :key="url"
              :src="url"
              :preview-src-list="order.finish_images"
              fit="cover"
              class="image"
            />
          </div>
        </div>
      </section>

      <section class="actions">
        <el-button v-if="order.can_urge" type="warning" plain :loading="acting" @click="urge">催单</el-button>
        <el-button v-if="order.can_cancel" type="danger" plain :loading="acting" @click="cancel">取消工单</el-button>
        <el-button v-if="order.can_evaluate" type="primary" @click="evaluate">去评价</el-button>
        <el-button @click="router.push('/student/orders')">返回列表</el-button>
      </section>

      <el-dialog v-model="evaluateVisible" title="服务评价" width="380px" align-center>
        <div class="evaluate-box">
          <div class="rate-row">
            <span>服务评分</span>
            <el-rate
              v-model="evaluationForm.score"
              show-text
              :texts="['很差', '较差', '一般', '满意', '非常满意']"
            />
          </div>
          <div class="tag-row">
            <el-tag
              v-for="tag in evaluateTags"
              :key="tag"
              size="small"
              :effect="evaluationForm.tags.includes(tag) ? 'dark' : 'plain'"
              :type="evaluationForm.tags.includes(tag) ? 'primary' : 'info'"
              class="tag"
              @click="toggleTag(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
          <el-input
            v-model="evaluationForm.content"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="说说这次服务的感受（选填）"
          />
          <p class="muted tip">评价成功可获得 5 积分</p>
        </div>
        <template #footer>
          <el-button @click="evaluateVisible = false">取消</el-button>
          <el-button type="primary" :loading="evaluating" @click="submitEvaluation">提交评价</el-button>
        </template>
      </el-dialog>
    </template>

    <el-empty v-else-if="!loading" description="工单不存在或无权查看">
      <el-button type="primary" @click="router.replace('/student/orders')">返回工单列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cancelOrder, fetchOrderDetail, urgeOrder } from '@/api/order'
import { createEvaluation } from '@/api/evaluation'
import { useUserStore } from '@/stores/user'
import {
  formatTime,
  isOrderOverdue,
  orderStatus,
  timeLeftText,
} from '@/utils/dict'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const order = ref(null)
const loading = ref(false)
const acting = ref(false)
const evaluateVisible = ref(false)
const evaluating = ref(false)
const evaluateTags = ['响应快', '态度好', '解决彻底', '沟通顺畅', '处理较慢', '未解决']
const evaluationForm = reactive({ score: 5, tags: [], content: '' })

const active = computed(() => ['pending', 'assigned', 'processing'].includes(order.value?.status))

const load = async () => {
  loading.value = true
  try {
    order.value = await fetchOrderDetail(route.params.id)
  } catch {
    order.value = null
  } finally {
    loading.value = false
  }
}

const urge = async () => {
  acting.value = true
  try {
    await urgeOrder(order.value.id)
    ElMessage.success('已催单，后勤会优先处理')
    await load()
  } finally {
    acting.value = false
  }
}

const cancel = async () => {
  try {
    await ElMessageBox.confirm('取消后需要重新提交工单，确定取消吗？', '取消工单', {
      confirmButtonText: '确定取消',
      cancelButtonText: '再想想',
      type: 'warning',
    })
  } catch {
    return
  }
  acting.value = true
  try {
    await cancelOrder(order.value.id)
    ElMessage.success('工单已取消')
    await load()
  } finally {
    acting.value = false
  }
}

const evaluate = () => {
  evaluationForm.score = 5
  evaluationForm.tags = []
  evaluationForm.content = ''
  evaluateVisible.value = true
}

const toggleTag = (tag) => {
  const index = evaluationForm.tags.indexOf(tag)
  if (index >= 0) {
    evaluationForm.tags.splice(index, 1)
  } else {
    evaluationForm.tags.push(tag)
  }
}

const submitEvaluation = async () => {
  evaluating.value = true
  try {
    await createEvaluation(order.value.id, {
      score: evaluationForm.score,
      tags: evaluationForm.tags,
      content: evaluationForm.content.trim() || null,
    })
    ElMessage.success('评价成功，积分 +5')
    evaluateVisible.value = false
    await load()
    await store.refreshMe()
  } finally {
    evaluating.value = false
  }
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

  &.status-done {
    background: linear-gradient(135deg, #15803d 0%, #22c55e 100%);
  }

  &.status-cancelled,
  &.status-closed {
    background: linear-gradient(135deg, #5b6b73 0%, #8a9aa3 100%);
  }
}

.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;

  h2 {
    margin: 4px 0 0;
    font-size: 19px;
  }
}

.no {
  margin: 0;
  font-size: 11px;
  opacity: 0.8;
  letter-spacing: 0.5px;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  font-size: 12px;
  opacity: 0.9;

  span + span::before {
    content: '·';
    margin-right: 8px;
    opacity: 0.6;
  }
}

.countdown {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 12px;

  &.overdue {
    background: rgba(239, 68, 68, 0.28);
  }
}

.card-title {
  margin: 0 0 12px;
  font-size: 15px;
}

.node-title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
}

.node-desc {
  margin: 3px 0 0;
  font-size: 12px;
  color: $cct-text-light;
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
    font-weight: 500;
    text-align: right;
  }
}

.danger {
  color: $cct-danger;
}

.image-block + .image-block {
  margin-top: 12px;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.image {
  width: 84px;
  height: 84px;
  border-radius: 10px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;

  .el-button {
    flex: 1;
    margin-left: 0;
  }
}

.evaluate-box {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rate-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: $cct-text-light;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  cursor: pointer;
}

.tip {
  margin: 0;
  font-size: 11px;
}
</style>