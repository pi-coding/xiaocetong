<template>
  <div class="create-order">
    <section class="page-card">
      <h3 class="card-title">选择厕所</h3>
      <el-select v-model="form.toilet_id" placeholder="选择需要处理的厕所" class="full" :disabled="fixedToilet">
        <el-option v-for="item in toiletOptions" :key="item.id" :label="`${item.name}（${item.code}）`" :value="item.id" />
      </el-select>
      <p v-if="selectedToilet" class="muted location">
        {{ selectedToilet.location_desc || `${selectedToilet.building} 栋 ${selectedToilet.floor} 层` }}
      </p>
      <el-empty v-if="!loading && !toiletOptions.length" description="暂无可选厕所，请先绑定宿舍厕所" :image-size="70" />
    </section>

    <section class="page-card">
      <h3 class="card-title">问题类型</h3>
      <div class="types">
        <button
          v-for="item in typeOptions"
          :key="item.value"
          type="button"
          class="type"
          :class="{ active: form.type === item.value }"
          @click="selectType(item.value)"
        >
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <strong>{{ item.label }}</strong>
          <span>{{ item.desc }}</span>
        </button>
      </div>
    </section>

    <section class="page-card">
      <div class="flex-between">
        <h3 class="card-title">问题描述</h3>
        <el-button size="small" type="primary" plain :loading="polishing" @click="polish">
          AI 帮我写
        </el-button>
      </div>
      <el-form label-position="top" size="default">
        <el-form-item label="问题标题">
          <el-input v-model="form.title" maxlength="64" show-word-limit placeholder="一句话描述问题" />
        </el-form-item>
        <div class="presets">
          <el-tag
            v-for="preset in presets"
            :key="preset"
            size="small"
            effect="plain"
            class="preset"
            @click="form.title = preset"
          >
            {{ preset }}
          </el-tag>
        </div>
        <el-form-item label="补充说明">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="1000" show-word-limit placeholder="如：位于第 3 个隔间，水位持续上涨" />
        </el-form-item>
        <el-form-item label="现场照片（选填，最多 3 张）">
          <ImageUpload v-model="form.images" :limit="3" />
        </el-form-item>
        <el-form-item label="紧急程度">
          <el-radio-group v-model="form.priority">
            <el-radio-button v-for="(meta, key) in PRIORITY" :key="key" :value="key">{{ meta.label }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <p class="muted sla">预计响应时限：{{ slaText }}</p>
      </el-form>
    </section>

    <div class="footer">
      <el-button type="primary" class="submit" :loading="submitting" @click="submit">提交工单</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ImageUpload from '@/components/ImageUpload.vue'
import { describeProblem } from '@/api/ai'
import { createOrder } from '@/api/order'
import { fetchNearbyToilets, fetchToiletDetail } from '@/api/toilet'
import { fetchMyBinding } from '@/api/dormBinding'
import { PRIORITY } from '@/utils/dict'

const route = useRoute()
const router = useRouter()

const typeOptions = [
  { value: 'unclog', label: '通厕所', desc: '堵塞 / 反水 / 异味', icon: 'MagicStick' },
  { value: 'clean', label: '要清洁', desc: '脏乱 / 垃圾满溢', icon: 'Brush' },
  { value: 'repair', label: '报修', desc: '冲水阀 / 门锁 / 灯具', icon: 'Tools' },
]

const TITLE_PRESETS = {
  unclog: ['蹲位堵塞无法冲水', '下水道反水有异味', '便池水位异常'],
  clean: ['地面污渍较多', '垃圾桶已满需清理', '洗手台积垢'],
  repair: ['冲水阀漏水', '门锁损坏无法关闭', '灯管不亮'],
}

const SLA_MINUTES = { urgent: 120, high: 240, normal: 480, low: 1440 }

const initialType = ['unclog', 'clean', 'repair'].includes(route.query.type) ? route.query.type : 'clean'
const fixedToilet = ref(Boolean(route.query.toiletId))

const form = reactive({
  toilet_id: route.query.toiletId ? Number(route.query.toiletId) : null,
  type: initialType,
  title: TITLE_PRESETS[initialType][0],
  description: '',
  images: [],
  priority: 'normal',
})

const toiletOptions = ref([])
const loading = ref(false)
const submitting = ref(false)
const polishing = ref(false)

const polish = async () => {
  const text = `${form.title} ${form.description}`.trim()
  if (text.length < 4) {
    ElMessage.warning('请先输入问题描述')
    return
  }
  polishing.value = true
  try {
    const data = await describeProblem(text)
    form.type = data.type
    form.title = data.title
    form.description = data.description
    form.priority = data.priority
    ElMessage.success(`已识别为「${data.type_text}」问题，并生成规范描述`)
  } finally {
    polishing.value = false
  }
}

const presets = computed(() => TITLE_PRESETS[form.type] || [])

const selectedToilet = computed(() => toiletOptions.value.find((item) => item.id === form.toilet_id))

const slaText = computed(() => {
  const minutes = SLA_MINUTES[form.priority] || 480
  if (minutes < 60) return `${minutes} 分钟`
  return `${minutes / 60} 小时`
})

const selectType = (value) => {
  form.type = value
  form.title = TITLE_PRESETS[value][0]
}

const loadOptions = async () => {
  loading.value = true
  try {
    const list = []
    if (route.query.toiletId) {
      const detail = await fetchToiletDetail(route.query.toiletId)
      list.push(detail)
    } else {
      const [binding, nearby] = await Promise.allSettled([fetchMyBinding(), fetchNearbyToilets(5)])
      if (binding.status === 'fulfilled' && binding.value?.toilet) {
        list.push(binding.value.toilet)
      }
      if (nearby.status === 'fulfilled') {
        for (const item of nearby.value) {
          if (!list.some((existing) => existing.id === item.id)) list.push(item)
        }
      }
    }
    toiletOptions.value = list
    if (!form.toilet_id && list.length) {
      form.toilet_id = list[0].id
    }
  } finally {
    loading.value = false
  }
}

const submit = async () => {
  if (!form.toilet_id) {
    ElMessage.warning('请选择要处理的厕所')
    return
  }
  if (!form.title.trim()) {
    ElMessage.warning('请填写问题标题')
    return
  }
  submitting.value = true
  try {
    const data = await createOrder({
      toilet_id: form.toilet_id,
      type: form.type,
      title: form.title.trim(),
      description: form.description.trim() || null,
      images: form.images,
      priority: form.priority,
    })
    ElMessage.success('工单已提交')
    router.replace(`/student/orders/${data.id}`)
  } finally {
    submitting.value = false
  }
}

onMounted(loadOptions)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.create-order {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-title {
  margin: 0 0 12px;
  font-size: 15px;
}

.full {
  width: 100%;
}

.location {
  margin: 8px 0 0;
}

.types {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.type {
  border: 1px solid $cct-border;
  border-radius: 12px;
  background: #fafcfc;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: $cct-text-light;

  strong {
    font-size: 13px;
    color: $cct-text;
  }

  span {
    font-size: 11px;
  }

  &.active {
    border-color: $cct-primary;
    background: #eaf8f7;
    color: $cct-primary;

    strong {
      color: $cct-primary;
    }
  }
}

.presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: -10px 0 16px;
}

.preset {
  cursor: pointer;

  &:hover {
    color: $cct-primary;
    border-color: $cct-primary;
  }
}

.sla {
  margin: -6px 0 0;
}

.footer {
  padding-bottom: 8px;
}

.submit {
  width: 100%;
  height: 44px;
  font-size: 15px;
}
</style>