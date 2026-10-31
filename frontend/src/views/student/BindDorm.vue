<template>
  <div v-loading="loading" class="bind">
    <section v-if="binding && mode === 'view'" class="page-card bound">
      <div class="bound-head">
        <div class="icon"><el-icon :size="22"><House /></el-icon></div>
        <div>
          <h3>{{ binding.building }} 栋 {{ binding.room_no }}</h3>
          <p class="muted">{{ binding.bind_type === 'owner' ? '本人宿舍' : '宿舍共用' }} · 宿舍厕所</p>
        </div>
        <el-tag size="small" :type="toiletStatus(binding.toilet?.status).type" effect="plain">
          {{ toiletStatus(binding.toilet?.status).label }}
        </el-tag>
      </div>

      <div v-if="binding.toilet" class="bound-info">
        <div class="info-row"><span>厕所编号</span><strong>{{ binding.toilet.code }}</strong></div>
        <div class="info-row"><span>清洁状态</span><strong :class="binding.toilet.warn_level ? 'danger' : 'ok'">{{ cleanStatusText(binding.toilet) }}</strong></div>
        <div class="info-row"><span>最近清洁</span><strong>{{ formatTime(binding.toilet.last_cleaned_at) }}</strong></div>
        <div class="info-row"><span>负责保洁</span><strong>{{ binding.toilet.cleaner_name || '待指派' }}</strong></div>
      </div>

      <p class="hint">绑定后可在此厕所一键提交通厕、清洁、报修工单。</p>

      <div class="bound-actions">
        <el-button type="primary" plain @click="startRebind">换绑</el-button>
        <el-button type="danger" plain @click="removeBinding">解绑</el-button>
      </div>
    </section>

    <section v-else class="page-card">
      <h3 class="card-title">{{ mode === 'rebind' ? '换绑宿舍厕所' : '绑定宿舍厕所' }}</h3>
      <p class="muted">填写宿舍信息后，系统会匹配已有的宿舍厕所；若不存在将自动创建。</p>

      <el-form :model="form" label-position="top" size="default">
        <div class="row">
          <el-form-item label="楼栋">
            <el-select v-model="form.building" placeholder="选择楼栋" @change="resetMatch">
              <el-option v-for="item in buildings" :key="item" :label="`${item} 栋`" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="宿舍号">
            <el-input v-model="form.room_no" placeholder="如 301" maxlength="16" @input="resetMatch" />
          </el-form-item>
        </div>

        <el-form-item label="绑定类型">
          <el-radio-group v-model="form.bind_type">
            <el-radio-button value="owner">本人宿舍</el-radio-button>
            <el-radio-button value="shared">宿舍共用</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <div class="match-row">
          <el-button :loading="matching" @click="checkMatch">检查宿舍厕所</el-button>
          <span v-if="matchResult" class="match-text">
            <el-tag size="small" :type="matchResult.exists ? 'success' : 'info'" effect="plain">
              {{ matchResult.exists ? '已存在该宿舍厕所' : '将新建宿舍厕所' }}
            </el-tag>
            <span class="muted">{{ matchResult.code }}</span>
          </span>
        </div>

        <div class="submit-row">
          <el-button v-if="mode === 'rebind'" @click="mode = 'view'">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submit">
            {{ mode === 'rebind' ? '确认换绑' : '确认绑定' }}
          </el-button>
        </div>
      </el-form>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createBinding,
  deleteBinding,
  fetchMyBinding,
  matchBinding,
  updateBinding,
} from '@/api/dormBinding'
import { useUserStore } from '@/stores/user'
import { cleanStatusText, formatTime, toiletStatus } from '@/utils/dict'

const store = useUserStore()
const buildings = ['A', 'B', 'C', 'D']
const loading = ref(false)
const saving = ref(false)
const matching = ref(false)
const binding = ref(null)
const matchResult = ref(null)
const mode = ref('bind')

const form = reactive({
  building: store.user?.building || 'D',
  room_no: store.user?.room_no || '',
  bind_type: 'owner',
})

const load = async () => {
  loading.value = true
  try {
    binding.value = await fetchMyBinding()
    mode.value = binding.value ? 'view' : 'bind'
    if (binding.value) {
      form.building = binding.value.building
      form.room_no = binding.value.room_no
      form.bind_type = binding.value.bind_type
    }
  } finally {
    loading.value = false
  }
}

const resetMatch = () => {
  matchResult.value = null
}

const startRebind = () => {
  form.building = binding.value?.building || 'D'
  form.room_no = binding.value?.room_no || ''
  form.bind_type = binding.value?.bind_type || 'owner'
  matchResult.value = null
  mode.value = 'rebind'
}

const checkMatch = async () => {
  if (!form.building || !form.room_no.trim()) {
    ElMessage.warning('请先选择楼栋并填写宿舍号')
    return
  }
  matching.value = true
  try {
    matchResult.value = await matchBinding({
      building: form.building,
      room_no: form.room_no.trim(),
    })
  } finally {
    matching.value = false
  }
}

const submit = async () => {
  if (!form.building || !form.room_no.trim()) {
    ElMessage.warning('请填写完整的宿舍信息')
    return
  }
  saving.value = true
  try {
    const payload = {
      building: form.building,
      room_no: form.room_no.trim(),
      bind_type: form.bind_type,
    }
    if (mode.value === 'rebind' && binding.value) {
      await updateBinding(binding.value.id, payload)
      ElMessage.success('换绑成功')
    } else {
      await createBinding(payload)
      ElMessage.success('绑定成功')
    }
    await load()
    if (store.user) {
      store.updateLocal({ ...store.user, building: form.building, room_no: form.room_no.trim() })
    }
  } finally {
    saving.value = false
  }
}

const removeBinding = async () => {
  try {
    await ElMessageBox.confirm('解绑后将无法在本页快速报单，确定解绑吗？', '解绑确认', {
      confirmButtonText: '解绑',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteBinding(binding.value.id)
    ElMessage.success('已解绑')
    binding.value = null
    mode.value = 'bind'
    form.room_no = ''
    matchResult.value = null
  } catch {
    /* 用户取消 */
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.bind {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 160px;
}

.bound-head {
  display: flex;
  align-items: center;
  gap: 12px;

  h3 {
    margin: 0 0 4px;
    font-size: 16px;
  }

  .muted {
    margin: 0;
  }

  .el-tag {
    margin-left: auto;
  }
}

.icon {
  width: 46px;
  height: 46px;
  border-radius: 13px;
  background: #e6f7f6;
  color: $cct-primary;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bound-info {
  margin-top: 14px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 9px 0;
  border-bottom: 1px dashed $cct-border;
  font-size: 13px;

  span {
    color: $cct-text-light;
  }
}

.danger {
  color: $cct-danger;
}

.ok {
  color: #16a34a;
}

.hint {
  margin: 14px 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f1f8f8;
  font-size: 12px;
  color: $cct-text-light;
  line-height: 1.5;
}

.bound-actions {
  display: flex;
  gap: 10px;

  .el-button {
    flex: 1;
  }
}

.card-title {
  margin: 0 0 6px;
  font-size: 16px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.match-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin: 6px 0 18px;
}

.match-text {
  display: flex;
  align-items: center;
  gap: 6px;
}

.submit-row {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>