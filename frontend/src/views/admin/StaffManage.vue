<template>
  <div class="staff-manage">
    <section class="page-card toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索姓名 / 工号 / 电话"
        :prefix-icon="Search"
        clearable
        class="search"
        @keyup.enter="search"
        @clear="search"
      />
      <el-select v-model="filters.work_type" placeholder="全部工种" clearable class="select">
        <el-option label="保洁" value="cleaner" />
        <el-option label="维修" value="plumber" />
        <el-option label="综合" value="all" />
      </el-select>
      <el-select v-model="filters.status" placeholder="全部状态" clearable class="select">
        <el-option label="在岗" value="on" />
        <el-option label="离岗" value="off" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="search">查询</el-button>
      <el-button type="primary" plain :icon="Plus" @click="openCreate">新增员工</el-button>
      <span class="summary muted">共 {{ total }} 名员工</span>
    </section>

    <section class="page-card">
      <el-table v-loading="loading" :data="list" stripe>
        <el-table-column prop="staff_no" label="工号" width="110" />
        <el-table-column prop="name" label="姓名" width="90" />
        <el-table-column prop="phone" label="电话" width="120" />
        <el-table-column label="工种" width="90">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" :type="row.work_type === 'plumber' ? 'warning' : row.work_type === 'all' ? 'success' : 'primary'">
              {{ workTypeText(row.work_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="area" label="负责区域" width="140" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'on' ? 'success' : 'info'" effect="plain">
              {{ row.status === 'on' ? '在岗' : '离岗' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_load" label="在途" width="70" />
        <el-table-column prop="done_count" label="完成" width="70" />
        <el-table-column label="评分" width="80">
          <template #default="{ row }">{{ row.avg_score.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column prop="toilet_count" label="负责厕所" width="90" />
        <el-table-column label="登录账号" width="120">
          <template #default="{ row }">{{ row.account || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link :type="row.status === 'on' ? 'warning' : 'success'" @click="toggleStatus(row)">
              {{ row.status === 'on' ? '设离岗' : '设在岗' }}
            </el-button>
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

    <el-drawer v-model="drawerVisible" :title="editingId ? '编辑员工' : '新增员工'" size="420px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="row">
          <el-form-item label="工号" prop="staff_no">
            <el-input v-model="form.staff_no" :disabled="Boolean(editingId)" placeholder="如 ST009" />
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="form.name" placeholder="员工姓名" maxlength="50" />
          </el-form-item>
        </div>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="手机号" maxlength="20" />
        </el-form-item>
        <div class="row">
          <el-form-item label="工种" prop="work_type">
            <el-select v-model="form.work_type">
              <el-option label="保洁" value="cleaner" />
              <el-option label="维修" value="plumber" />
              <el-option label="综合" value="all" />
            </el-select>
          </el-form-item>
          <el-form-item label="日单量上限" prop="max_daily_orders">
            <el-input-number v-model="form.max_daily_orders" :min="1" :max="100" controls-position="right" />
          </el-form-item>
        </div>
        <el-form-item label="负责区域">
          <el-input v-model="form.area" placeholder="如 A栋,B栋（逗号分隔）" maxlength="64" />
        </el-form-item>
        <el-form-item label="在岗状态">
          <el-radio-group v-model="form.status">
            <el-radio-button value="on">在岗</el-radio-button>
            <el-radio-button value="off">离岗</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="!editingId" label="登录账号（选填）">
          <el-input v-model="form.username" placeholder="填写后自动创建员工账号，默认密码 123456" maxlength="50" />
        </el-form-item>
        <el-alert
          v-if="editingId"
          title="工号与登录账号创建后不可修改；如需停用请设为离岗。"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  createStaff,
  deleteStaff,
  fetchStaffList,
  toggleStaffStatus,
  updateStaff,
} from '@/api/staff'

const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)
const filters = reactive({ keyword: '', work_type: '', status: '' })

const drawerVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formRef = ref()

const emptyForm = () => ({
  staff_no: '',
  name: '',
  phone: '',
  work_type: 'cleaner',
  area: '',
  status: 'on',
  max_daily_orders: 20,
  username: '',
})

const form = reactive(emptyForm())

const rules = {
  staff_no: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    { min: 2, max: 32, message: '工号 2-32 位', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { min: 6, max: 20, message: '电话长度不合法', trigger: 'blur' },
  ],
}

const workTypeText = (type) => ({ cleaner: '保洁', plumber: '维修', all: '综合' })[type] || type

const buildParams = () => {
  const params = { page: page.value, size: size.value }
  if (filters.keyword.trim()) params.keyword = filters.keyword.trim()
  if (filters.work_type) params.work_type = filters.work_type
  if (filters.status) params.status = filters.status
  return params
}

const load = async () => {
  loading.value = true
  try {
    const data = await fetchStaffList(buildParams())
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
    staff_no: row.staff_no,
    name: row.name,
    phone: row.phone,
    work_type: row.work_type,
    area: row.area || '',
    status: row.status,
    max_daily_orders: row.max_daily_orders,
    username: '',
  })
  drawerVisible.value = true
}

const save = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editingId.value) {
      await updateStaff(editingId.value, {
        name: form.name.trim(),
        phone: form.phone.trim(),
        work_type: form.work_type,
        area: form.area.trim() || null,
        max_daily_orders: Number(form.max_daily_orders),
      })
      ElMessage.success('保存成功')
    } else {
      const data = await createStaff({
        staff_no: form.staff_no.trim().toUpperCase(),
        name: form.name.trim(),
        phone: form.phone.trim(),
        work_type: form.work_type,
        area: form.area.trim() || null,
        status: form.status,
        max_daily_orders: Number(form.max_daily_orders),
        username: form.username.trim() || null,
      })
      ElMessage.success(data.account ? `新增成功，账号 ${data.account} 默认密码 123456` : '新增成功')
    }
    drawerVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const toggleStatus = async (row) => {
  await toggleStaffStatus(row.id)
  ElMessage.success(row.status === 'on' ? '已设为离岗' : '已设为在岗')
  await load()
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除员工「${row.name}」吗？存在工单、清洁记录或负责厕所时将无法删除。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  await deleteStaff(row.id)
  ElMessage.success('已删除')
  if (list.value.length === 1 && page.value > 1) page.value -= 1
  await load()
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.staff-manage {
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
  width: 220px;
}

.select {
  width: 130px;
}

.summary {
  margin-left: auto;
  font-size: 12px;
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
</style>