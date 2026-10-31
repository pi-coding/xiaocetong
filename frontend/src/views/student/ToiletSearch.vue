<template>
  <div class="toilets">
    <section class="page-card filters">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索厕所名称、编号或位置"
        :prefix-icon="Search"
        clearable
        @keyup.enter="search"
        @clear="search"
      />
      <div class="filter-row">
        <el-select v-model="filters.building" placeholder="全部楼栋" clearable size="small" class="grow">
          <el-option v-for="item in buildings" :key="item" :label="`${item} 栋`" :value="item" />
        </el-select>
        <el-select v-model="filters.type" placeholder="全部类型" clearable size="small" class="grow">
          <el-option label="公共厕所" value="public" />
          <el-option label="宿舍厕所" value="dorm" />
        </el-select>
        <el-select v-model="filters.status" placeholder="全部状态" clearable size="small" class="grow">
          <el-option v-for="(meta, key) in TOILET_STATUS" :key="key" :label="meta.label" :value="key" />
        </el-select>
      </div>
      <div class="filter-row">
        <el-radio-group v-model="filters.sort" size="small" @change="search">
          <el-radio-button value="default">综合</el-radio-button>
          <el-radio-button value="score">评分</el-radio-button>
          <el-radio-button value="cleaned">最近清洁</el-radio-button>
        </el-radio-group>
        <el-button size="small" type="primary" @click="search">查询</el-button>
      </div>
    </section>

    <div class="result-head">
      <span>共 {{ total }} 个厕所</span>
      <el-button link type="primary" size="small" @click="goBind">我的宿舍绑定</el-button>
    </div>

    <div v-loading="loading" class="list">
      <article v-for="item in list" :key="item.id" class="toilet-card" @click="goDetail(item.id)">
        <div class="card-head">
          <strong>{{ item.name }}</strong>
          <el-tag :type="toiletStatus(item.status).type" size="small" effect="light">
            {{ toiletStatus(item.status).label }}
          </el-tag>
        </div>
        <p class="location">{{ item.location_desc || `${item.building} 栋 ${item.floor} 层` }} · {{ item.code }}</p>
        <div class="meta">
          <span>{{ item.building }} 栋 {{ item.floor }} 层</span>
          <span>{{ GENDER_TEXT[item.gender] || item.gender }}</span>
          <span>{{ item.stall_count }} 个蹲位</span>
        </div>
        <div class="tags">
          <el-tag size="small" effect="plain" :type="warnMeta(item.warn_level).type">
            {{ cleanStatusText(item) }}
          </el-tag>
          <el-tag size="small" effect="plain" type="info">评分 {{ scoreText(item.avg_score) }}</el-tag>
          <el-tag v-if="item.active_order_count" size="small" effect="plain" type="warning">
            {{ item.active_order_count }} 单处理中
          </el-tag>
        </div>
      </article>

      <el-empty v-if="!loading && !list.length" description="没有找到符合条件的厕所" :image-size="90" />
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
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { fetchToilets } from '@/api/toilet'
import { GENDER_TEXT, TOILET_STATUS, cleanStatusText, scoreText, toiletStatus, warnMeta } from '@/utils/dict'

const router = useRouter()
const buildings = ['A', 'B', 'C', 'D']
const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const filters = reactive({ keyword: '', building: '', type: '', status: '', sort: 'default' })

const buildParams = () => {
  const params = { page: page.value, size: size.value, sort: filters.sort }
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

const goDetail = (id) => router.push(`/student/toilets/${id}`)
const goBind = () => router.push('/student/bind')

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.toilets {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filters {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.grow {
  flex: 1;
}

.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: $cct-text-light;
  padding: 0 2px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 120px;
}

.toilet-card {
  background: #fff;
  border-radius: $cct-radius;
  box-shadow: $cct-shadow;
  padding: 14px;
  cursor: pointer;
  transition: transform 0.15s ease;

  &:active {
    transform: scale(0.99);
  }
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;

  strong {
    font-size: 15px;
  }
}

.location {
  margin: 6px 0 10px;
  font-size: 12px;
  color: $cct-text-light;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #5c6f78;
  margin-bottom: 10px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pager {
  justify-content: center;
  padding: 6px 0 12px;
}
</style>