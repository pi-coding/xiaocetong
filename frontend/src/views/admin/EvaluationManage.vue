<template>
  <div class="evaluations">
    <section class="page-card toolbar">
      <el-select v-model="filters.score" placeholder="全部评分" clearable class="select">
        <el-option label="差评（1-3 星）" :value="3" />
        <el-option label="4 星" :value="4" />
        <el-option label="5 星" :value="5" />
      </el-select>
      <el-checkbox v-model="filters.only_appeal">仅看申诉</el-checkbox>
      <el-button type="primary" :icon="Search" @click="search">查询</el-button>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      <div class="summary">
        <span>共 <b>{{ total }}</b> 条评价</span>
        <span class="muted">平均星级统计见统计报表</span>
      </div>
    </section>

    <section class="page-card">
      <el-table v-loading="loading" :data="list" stripe>
        <el-table-column prop="order_no" label="工单号" width="150" />
        <el-table-column label="厕所" min-width="150">
          <template #default="{ row }">
            <div>{{ row.toilet_name }}</div>
            <span class="muted">{{ row.building }} 栋</span>
          </template>
        </el-table-column>
        <el-table-column label="学生" width="100">
          <template #default="{ row }">{{ row.user_name }}</template>
        </el-table-column>
        <el-table-column label="处理员工" width="100">
          <template #default="{ row }">{{ row.staff_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="评分" width="150">
          <template #default="{ row }">
            <el-rate :model-value="row.score" disabled size="small" />
          </template>
        </el-table-column>
        <el-table-column label="评价内容" min-width="220">
          <template #default="{ row }">
            <div class="content">{{ row.content || '未填写' }}</div>
            <div class="tags">
              <el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain" type="info">{{ tag }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="回复" min-width="180">
          <template #default="{ row }">
            <span v-if="row.reply">{{ row.reply }}</span>
            <span v-else class="muted">未回复</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.is_appeal" size="small" type="danger" effect="plain">申诉中</el-tag>
            <el-tag v-else size="small" type="success" effect="plain">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="150">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openReply(row)">回复</el-button>
            <el-button link :type="row.is_appeal ? 'info' : 'warning'" @click="toggleAppeal(row)">
              {{ row.is_appeal ? '取消申诉' : '标记申诉' }}
            </el-button>
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

    <el-dialog v-model="replyVisible" title="回复评价" width="420px">
      <div v-if="current" class="reply-head">
        <el-rate :model-value="current.score" disabled size="small" />
        <p class="muted">{{ current.toilet_name }} · {{ current.user_name }} · {{ current.order_no }}</p>
        <p class="content">{{ current.content || '学生未填写评价内容' }}</p>
      </div>
      <el-input v-model="replyText" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="请输入回复内容" />
      <template #footer>
        <el-button @click="replyVisible = false">取消</el-button>
        <el-button type="primary" :loading="replying" @click="submitReply">提交回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import {
  appealEvaluation,
  fetchEvaluations,
  replyEvaluation,
} from '@/api/evaluation'
import { formatTime } from '@/utils/dict'

const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)
const filters = reactive({ score: null, only_appeal: false })

const replyVisible = ref(false)
const current = ref(null)
const replyText = ref('')
const replying = ref(false)

const buildParams = () => {
  const params = { page: page.value, size: size.value }
  if (filters.score) params.score = filters.score
  if (filters.only_appeal) params.only_appeal = true
  return params
}

const load = async () => {
  loading.value = true
  try {
    const data = await fetchEvaluations(buildParams())
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

const openReply = (row) => {
  current.value = row
  replyText.value = row.reply || ''
  replyVisible.value = true
}

const submitReply = async () => {
  if (!replyText.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  replying.value = true
  try {
    await replyEvaluation(current.value.id, replyText.value.trim())
    ElMessage.success('回复成功')
    replyVisible.value = false
    await load()
  } finally {
    replying.value = false
  }
}

const toggleAppeal = async (row) => {
  await appealEvaluation(row.id)
  ElMessage.success(row.is_appeal ? '已取消申诉标记' : '已标记申诉')
  await load()
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.evaluations {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.select {
  width: 160px;
}

.summary {
  margin-left: auto;
  font-size: 12px;
  color: $cct-text-light;
  display: flex;
  gap: 12px;
}

.content {
  font-size: 12px;
  line-height: 1.5;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding-top: 14px;
}

.reply-head {
  margin-bottom: 12px;
}

.reply-head .muted {
  margin: 6px 0;
}

.reply-head .content {
  margin: 0;
  padding: 10px;
  border-radius: 8px;
  background: #f6fafb;
}
</style>