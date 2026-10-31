<template>
  <div class="manage">
    <section class="page-card toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索名称 / 编号 / 位置"
        :prefix-icon="Search"
        clearable
        class="search"
        @keyup.enter="search"
        @clear="search"
      />
      <el-select v-model="filters.building" placeholder="全部楼栋" clearable class="select">
        <el-option v-for="item in buildings" :key="item" :label="`${item} 栋`" :value="item" />
      </el-select>
      <el-select v-model="filters.type" placeholder="全部类型" clearable class="select">
        <el-option label="公共厕所" value="public" />
        <el-option label="宿舍厕所" value="dorm" />
      </el-select>
      <el-select v-model="filters.status" placeholder="全部状态" clearable class="select">
        <el-option v-for="(meta, key) in TOILET_STATUS" :key="key" :label="meta.label" :value="key" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="search">查询</el-button>
      <el-button type="primary" plain :icon="Plus" @click="openCreate">新增厕所</el-button>
    </section>

    <section class="page-card">
      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column prop="code" label="编号" width="120" />
        <el-table-column prop="name" label="名称" min-width="170" show-overflow-tooltip />
        <el-table-column label="位置" width="120">
          <template #default="{ row }">{{ row.building }} 栋 {{ row.floor }} 层</template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" :type="row.type === 'public' ? 'primary' : 'info'">
              {{ row.type === 'public' ? '公共' : '宿舍' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="stall_count" label="蹲位" width="70" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="toiletStatus(row.status).type">{{ toiletStatus(row.status).label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="清洁状态" width="150">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" :type="warnMeta(row.warn_level).type">{{ cleanStatusText(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="负责保洁" width="100">
          <template #default="{ row }">{{ row.cleaner_name || '待指派' }}</template>
        </el-table-column>
        <el-table-column label="评分" width="80">
          <template #default="{ row }">{{ scoreText(row.avg_score) }}</template>
        </el-table-column>
        <el-table-column label="工单" width="70">
          <template #default="{ row }">{{ row.order_count }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="showQr(row)">二维码</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="size"
          :current-page="page"
          @current-change="onPageChange"
        />
      </div>
    </section>

    <el-drawer v-model="drawerVisible" :title="editingId ? '编辑厕所' : '新增厕所'" size="420px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="厕所编号" prop="code">
          <el-input v-model="form.code" :disabled="Boolean(editingId)" placeholder="如 A-1F-01，字母数字与短横线" />
        </el-form-item>
        <el-form-item label="厕所名称" prop="name">
          <el-input v-model="form.name" placeholder="如 A栋1层东侧公厕" maxlength="64" />
        </el-form-item>
        <div class="row">
          <el-form-item label="类型" prop="type">
            <el-select v-model="form.type">
              <el-option label="公共厕所" value="public" />
              <el-option label="宿舍厕所" value="dorm" />
            </el-select>
          </el-form-item>
          <el-form-item label="适用人群" prop="gender">
            <el-select v-model="form.gender">
              <el-option label="男厕" value="male" />
              <el-option label="女厕" value="female" />
              <el-option label="通用" value="all" />
            </el-select>
          </el-form-item>
        </div>
        <div class="row">
          <el-form-item label="楼栋" prop="building">
            <el-select v-model="form.building">
              <el-option v-for="item in buildings" :key="item" :label="`${item} 栋`" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="楼层" prop="floor">
            <el-input-number v-model="form.floor" :min="0" :max="99" controls-position="right" />
          </el-form-item>
        </div>
        <div class="row">
          <el-form-item label="蹲位数量" prop="stall_count">
            <el-input-number v-model="form.stall_count" :min="1" :max="99" controls-position="right" />
          </el-form-item>
          <el-form-item label="清洁周期（分钟）" prop="clean_interval_min">
            <el-input-number v-model="form.clean_interval_min" :min="30" :max="10080" :step="30" controls-position="right" />
          </el-form-item>
        </div>
        <el-form-item label="运行状态" prop="status">
          <el-select v-model="form.status">
            <el-option v-for="(meta, key) in TOILET_STATUS" :key="key" :label="meta.label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置描述">
          <el-input v-model="form.location_desc" maxlength="128" placeholder="如 A栋1层走廊尽头东侧" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="qrVisible" title="厕所标识码" width="360px" align-center>
      <div class="qr-box">
        <img v-if="qrImage" :src="qrImage" alt="厕所二维码" />
        <p class="qr-name">{{ qrData?.name }}</p>
        <p class="qr-content">{{ qrContent }}</p>
      </div>
      <template #footer>
        <el-button @click="copyQr">复制链接</el-button>
        <el-button type="primary" :disabled="!qrImage" @click="downloadQr">下载二维码</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  createToilet,
  deleteToilet,
  fetchToiletQr,
  fetchToilets,
  updateToilet,
} from '@/api/toilet'
import { TOILET_STATUS, cleanStatusText, scoreText, toiletStatus, warnMeta } from '@/utils/dict'
import { buildQrDataUrl, downloadDataUrl } from '@/utils/qrcode'

const buildings = ['A', 'B', 'C', 'D']
const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const filters = reactive({ keyword: '', building: '', type: '', status: '' })

const drawerVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const formRef = ref()

const qrVisible = ref(false)
const qrData = ref(null)
const qrImage = ref('')
const qrContent = ref('')

const emptyForm = () => ({
  code: '',
  name: '',
  type: 'public',
  building: 'A',
  floor: 1,
  gender: 'male',
  stall_count: 4,
  status: 'normal',
  clean_interval_min: 240,
  location_desc: '',
  remark: '',
})

const form = reactive(emptyForm())

const rules = {
  code: [
    { required: true, message: '请输入厕所编号', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9-]+$/, message: '仅支持字母、数字、短横线', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入厕所名称', trigger: 'blur' }],
  building: [{ required: true, message: '请选择楼栋', trigger: 'change' }],
}

const buildParams = () => {
  const params = { page: page.value, size: size.value, sort: 'default' }
  if (filters.keyword.trim()) params.keyword = filters.keyword.trim()
  if (filters.building) params.building = filters.building
  if (filters.type) params.type = filters.type
  if (filters.status) params.status = filters.status
  return params
}

const load = async () => {
  loading.value = true
  try {
    const data = await fetchToilets(buildParams())
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

const search = () => {
  page.value = 1
  load()
}

const onPageChange = (value) => {
  page.value = value
  load()
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, emptyForm())
  drawerVisible.value = true
}

const openEdit = (row) => {
  editingId.value = row.id
  Object.assign(form, {
    code: row.code,
    name: row.name,
    type: row.type,
    building: row.building,
    floor: row.floor,
    gender: row.gender,
    stall_count: row.stall_count,
    status: row.status,
    clean_interval_min: row.clean_interval_min,
    location_desc: row.location_desc || '',
    remark: row.remark || '',
  })
  drawerVisible.value = true
}

const save = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = {
      code: form.code.trim().toUpperCase(),
      name: form.name.trim(),
      type: form.type,
      building: form.building,
      floor: Number(form.floor),
      gender: form.gender,
      stall_count: Number(form.stall_count),
      status: form.status,
      clean_interval_min: Number(form.clean_interval_min),
      location_desc: form.location_desc.trim() || null,
      remark: form.remark.trim() || null,
    }
    if (editingId.value) {
      delete payload.code
      await updateToilet(editingId.value, payload)
      ElMessage.success('保存成功')
    } else {
      await createToilet(payload)
      ElMessage.success('新增成功')
    }
    drawerVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除「${row.name}」吗？存在绑定或工单记录的厕所无法删除。`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteToilet(row.id)
    ElMessage.success('已删除')
    if (list.value.length === 1 && page.value > 1) page.value -= 1
    await load()
  } catch {
    /* 用户取消 */
  }
}

const showQr = async (row) => {
  qrVisible.value = true
  qrData.value = null
  qrImage.value = ''
  qrContent.value = ''
  const data = await fetchToiletQr(row.id)
  qrData.value = data
  qrContent.value = data.content
  qrImage.value = await buildQrDataUrl(data.content, 240)
}

const copyQr = async () => {
  if (!qrContent.value) return
  try {
    await navigator.clipboard.writeText(qrContent.value)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选择文本复制')
  }
}

const downloadQr = () => {
  if (!qrImage.value) return
  downloadDataUrl(qrImage.value, `${qrData.value?.code || 'toilet'}-qrcode.png`)
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.manage {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.search {
  width: 240px;
}

.select {
  width: 130px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding-top: 14px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.qr-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;

  img {
    width: 240px;
    height: 240px;
    border: 1px solid $cct-border;
    border-radius: 12px;
  }
}

.qr-name {
  margin: 0;
  font-weight: 600;
}

.qr-content {
  margin: 0;
  font-size: 12px;
  color: $cct-text-light;
  word-break: break-all;
  text-align: center;
}
</style>