<template>
  <div class="checkin">
    <section class="hero">
      <div>
        <p class="greeting">清洁打卡</p>
        <p class="sub">完成保洁后上传前后照片并提交，系统自动刷新清洁时间</p>
      </div>
      <el-icon :size="32"><Camera /></el-icon>
    </section>

    <section class="page-card">
      <h3 class="card-title">选择厕所</h3>
      <el-select v-model="form.toilet_id" placeholder="选择我负责的厕所" class="full" :loading="loading">
        <el-option
          v-for="item in toilets"
          :key="item.id"
          :label="`${item.name}（${item.code}）`"
          :value="item.id"
        >
          <div class="option">
            <span>{{ item.name }}</span>
            <el-tag size="small" :type="warnMeta(item.warn_level).type" effect="plain">{{ cleanStatusText(item) }}</el-tag>
          </div>
        </el-option>
      </el-select>
      <p v-if="selected" class="muted location">
        {{ selected.building }} 栋 {{ selected.floor }} 层 · 上次清洁 {{ formatTime(selected.last_cleaned_at) }}
      </p>
      <el-empty v-if="!loading && !toilets.length" description="暂未分配责任厕所，请联系管理员" :image-size="70" />
    </section>

    <section v-if="form.toilet_id" class="page-card">
      <h3 class="card-title">清洁内容</h3>
      <el-checkbox-group v-model="form.clean_items" class="items">
        <el-checkbox-button v-for="item in cleanItems" :key="item" :value="item">{{ item }}</el-checkbox-button>
      </el-checkbox-group>

      <div class="image-row">
        <div class="image-col">
          <p class="label">清洁前</p>
          <ImageUpload v-model="form.before_images" :limit="2" />
        </div>
        <div class="image-col">
          <p class="label">清洁后</p>
          <ImageUpload v-model="form.after_images" :limit="2" />
        </div>
      </div>

      <div class="row">
        <el-form-item label="耗时（分钟）">
          <el-input-number v-model="form.duration_min" :min="1" :max="600" controls-position="right" />
        </el-form-item>
        <el-form-item label="清洁结果">
          <el-radio-group v-model="form.result">
            <el-radio-button value="pass">合格</el-radio-button>
            <el-radio-button value="fail">不合格</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </div>

      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="255" show-word-limit placeholder="如：耗材已补充，异味已处理" />
      </el-form-item>

      <el-button type="primary" class="submit" :loading="submitting" @click="submit">提交打卡</el-button>
    </section>

    <section class="page-card">
      <div class="flex-between">
        <h3 class="card-title">今日打卡记录</h3>
        <el-button link type="primary" @click="loadLogs">刷新</el-button>
      </div>
      <div v-if="logs.length" class="log-list">
        <div v-for="log in logs" :key="log.id" class="log-item">
          <div>
            <strong>{{ log.toilet_name }}</strong>
            <p class="muted">{{ formatTime(log.cleaned_at) }} · {{ log.clean_type_text }}</p>
          </div>
          <el-tag size="small" :type="log.result === 'pass' ? 'success' : 'danger'" effect="plain">
            {{ log.result === 'pass' ? '合格' : '不合格' }}
          </el-tag>
        </div>
      </div>
      <el-empty v-else description="今日暂无打卡记录" :image-size="60" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import ImageUpload from '@/components/ImageUpload.vue'
import { createCleaningLog, fetchMyCleaningLogs } from '@/api/cleaning'
import { fetchMyToilets } from '@/api/staff'
import { cleanStatusText, formatTime, warnMeta } from '@/utils/dict'

const cleanItems = ['地面', '便池', '洗手台', '镜面', '异味处理', '耗材补充']

const toilets = ref([])
const loading = ref(false)
const submitting = ref(false)
const logs = ref([])

const form = reactive({
  toilet_id: null,
  clean_items: ['地面', '便池'],
  before_images: [],
  after_images: [],
  duration_min: 15,
  result: 'pass',
  remark: '',
})

const selected = computed(() => toilets.value.find((item) => item.id === form.toilet_id))

const loadToilets = async () => {
  loading.value = true
  try {
    toilets.value = await fetchMyToilets()
    if (!form.toilet_id && toilets.value.length) {
      form.toilet_id = toilets.value[0].id
    }
  } finally {
    loading.value = false
  }
}

const loadLogs = async () => {
  const data = await fetchMyCleaningLogs({ page: 1, size: 5 })
  logs.value = data.list
}

const submit = async () => {
  if (!form.toilet_id) {
    ElMessage.warning('请选择厕所')
    return
  }
  if (!form.clean_items.length) {
    ElMessage.warning('请至少选择一项清洁内容')
    return
  }
  submitting.value = true
  try {
    await createCleaningLog({
      toilet_id: form.toilet_id,
      clean_type: 'routine',
      clean_items: form.clean_items,
      before_images: form.before_images,
      after_images: form.after_images,
      duration_min: form.duration_min,
      result: form.result,
      remark: form.remark.trim() || null,
    })
    ElMessage.success('打卡成功，清洁时间已更新')
    form.before_images = []
    form.after_images = []
    form.remark = ''
    await Promise.all([loadToilets(), loadLogs()])
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadToilets()
  await loadLogs()
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.checkin {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.card-title {
  margin: 0 0 12px;
  font-size: 15px;
}

.full {
  width: 100%;
}

.option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.location {
  margin: 8px 0 0;
}

.items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.image-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 8px;
}

.label {
  margin: 0 0 6px;
  font-size: 12px;
  color: $cct-text-light;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.submit {
  width: 100%;
  height: 42px;
}

.log-list {
  display: flex;
  flex-direction: column;
}

.log-item {
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
</style>