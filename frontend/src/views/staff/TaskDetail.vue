<template>
  <div v-loading="loading" class="task-detail">
    <template v-if="order">
      <section class="hero">
        <div class="hero-top">
          <div>
            <p class="no">{{ order.order_no }}</p>
            <h2>{{ order.title }}</h2>
          </div>
          <el-tag :type="orderStatus(order.status).type" effect="dark" round>{{ order.status_text }}</el-tag>
        </div>
        <p class="meta">{{ order.type_text }} · {{ order.toilet_name }} · {{ order.building }} 栋 {{ order.floor }} 层</p>
        <div v-if="active" class="countdown" :class="{ overdue: isOrderOverdue(order) }">
          <el-icon><Timer /></el-icon>
          <span>{{ isOrderOverdue(order) ? '已超时，请尽快处理' : timeLeftText(order) }}</span>
        </div>
      </section>

      <section class="page-card">
        <h3 class="card-title">现场情况</h3>
        <div class="info-row"><span>报单人</span><strong>{{ order.user_name }} {{ order.user_phone || '' }}</strong></div>
        <div class="info-row"><span>位置</span><strong>{{ order.location_desc || '-' }}</strong></div>
        <div class="info-row"><span>优先级</span><strong>{{ order.priority_text }}</strong></div>
        <div class="info-row"><span>提交时间</span><strong>{{ formatTime(order.created_at) }}</strong></div>
        <p v-if="order.description" class="desc">{{ order.description }}</p>
        <div v-if="order.images.length" class="image-list">
          <el-image
            v-for="url in order.images"
            :key="url"
            :src="url"
            :preview-src-list="order.images"
            fit="cover"
            class="image"
          />
        </div>
      </section>

      <section v-if="order.status === 'assigned'" class="page-card">
        <h3 class="card-title">开始处理</h3>
        <p class="muted">确认已到场后点击接单，系统开始记录处理时长。</p>
        <el-button type="primary" class="full" :loading="acting" @click="accept">接单处理</el-button>
      </section>

      <section v-if="order.status === 'processing'" class="page-card">
        <h3 class="card-title">完工提交</h3>
        <el-form label-position="top">
          <el-form-item label="完工照片（选填，最多 3 张）">
            <ImageUpload v-model="finish.images" :limit="3" />
          </el-form-item>
          <el-form-item label="处理说明">
            <el-input v-model="finish.remark" type="textarea" :rows="2" maxlength="255" show-word-limit placeholder="如：疏通完成，地面已清洁" />
          </el-form-item>
        </el-form>
        <el-button type="primary" class="full" :loading="acting" @click="submitFinish">提交完工</el-button>
      </section>

      <section v-if="order.status === 'done'" class="page-card done-card">
        <el-icon :size="34" color="#22c55e"><CircleCheckFilled /></el-icon>
        <h3>该工单已完工</h3>
        <p class="muted">完成时间：{{ formatTime(order.finished_at) }}</p>
        <p v-if="order.finish_remark" class="muted">{{ order.finish_remark }}</p>
      </section>

      <el-button class="back" @click="router.push('/staff/tasks')">返回待办</el-button>
    </template>

    <el-empty v-else-if="!loading" description="工单不存在或未指派给你">
      <el-button type="primary" @click="router.push('/staff/tasks')">返回待办</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ImageUpload from '@/components/ImageUpload.vue'
import { acceptOrder, fetchOrderDetail, finishOrder } from '@/api/order'
import {
  formatTime,
  isOrderOverdue,
  orderStatus,
  timeLeftText,
} from '@/utils/dict'

const route = useRoute()
const router = useRouter()
const order = ref(null)
const loading = ref(false)
const acting = ref(false)
const finish = reactive({ images: [], remark: '' })

const active = computed(() => ['assigned', 'processing'].includes(order.value?.status))

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

const accept = async () => {
  acting.value = true
  try {
    await acceptOrder(order.value.id)
    ElMessage.success('已接单，请尽快到场处理')
    await load()
  } finally {
    acting.value = false
  }
}

const submitFinish = async () => {
  acting.value = true
  try {
    await finishOrder(order.value.id, {
      finish_images: finish.images,
      finish_remark: finish.remark.trim() || null,
    })
    ElMessage.success('完工已提交，感谢处理')
    await load()
  } finally {
    acting.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.task-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}

.hero {
  border-radius: $cct-radius;
  padding: 18px;
  color: #fff;
  background: linear-gradient(135deg, #0f5760 0%, #148a92 100%);
  box-shadow: 0 10px 24px rgba(15, 87, 96, 0.25);
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;

  h2 {
    margin: 4px 0 0;
    font-size: 18px;
  }
}

.no {
  margin: 0;
  font-size: 11px;
  opacity: 0.8;
}

.meta {
  margin: 10px 0 0;
  font-size: 12px;
  opacity: 0.88;
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
    background: rgba(239, 68, 68, 0.3);
  }
}

.card-title {
  margin: 0 0 12px;
  font-size: 15px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 9px 0;
  border-bottom: 1px dashed $cct-border;
  font-size: 13px;

  span {
    color: $cct-text-light;
  }

  strong {
    font-weight: 500;
    text-align: right;
  }
}

.desc {
  margin: 12px 0 0;
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
  margin-top: 10px;
}

.image {
  width: 80px;
  height: 80px;
  border-radius: 10px;
}

.full {
  width: 100%;
  height: 42px;
}

.done-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;

  h3 {
    margin: 4px 0;
    font-size: 16px;
  }

  .muted {
    margin: 0;
  }
}

.back {
  width: 100%;
}
</style>