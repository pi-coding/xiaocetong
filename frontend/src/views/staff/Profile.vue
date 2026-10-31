<template>
  <div v-loading="loading" class="staff-profile">
    <template v-if="profile">
      <section class="hero">
        <div class="head">
          <div class="avatar">{{ profile.name.slice(0, 1) }}</div>
          <div>
            <h2>{{ profile.name }}</h2>
            <p class="sub">工号 {{ profile.staff_no }} · {{ workTypeText(profile.work_type) }}</p>
          </div>
        </div>
        <div class="stats">
          <div><strong>{{ profile.done_count }}</strong><span>累计完成</span></div>
          <div><strong>{{ profile.avg_duration_min.toFixed(0) }}</strong><span>平均分钟</span></div>
          <div><strong>{{ profile.avg_score.toFixed(1) }}</strong><span>服务评分</span></div>
        </div>
      </section>

      <section class="page-card">
        <h3 class="card-title">工作信息</h3>
        <div class="info-row"><span>负责区域</span><strong>{{ profile.area || '未设置' }}</strong></div>
        <div class="info-row"><span>负责厕所</span><strong>{{ profile.toilet_count }} 间</strong></div>
        <div class="info-row"><span>在途工单</span><strong>{{ profile.current_load }} 单</strong></div>
        <div class="info-row"><span>今日接单</span><strong>{{ profile.today_orders }} 单</strong></div>
        <div class="info-row">
          <span>在岗状态</span>
          <el-tag size="small" :type="profile.status === 'on' ? 'success' : 'info'" effect="plain">
            {{ profile.status === 'on' ? '在岗' : '离岗' }}
          </el-tag>
        </div>
        <div class="info-row"><span>联系电话</span><strong>{{ profile.phone }}</strong></div>
      </section>

      <section class="page-card link-card" @click="router.push('/staff/checkin')">
        <div>
          <h3 class="card-title">清洁打卡</h3>
          <p class="muted">完成保洁后上传照片并刷新清洁时间</p>
        </div>
        <el-icon><ArrowRight /></el-icon>
      </section>

      <el-button class="logout" type="danger" plain @click="logout">退出登录</el-button>
    </template>

    <el-empty v-else-if="!loading" description="未找到员工档案">
      <el-button type="primary" @click="logout">重新登录</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { fetchMyStaffProfile } from '@/api/staff'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()
const profile = ref(null)
const loading = ref(false)

const workTypeText = (type) => ({ cleaner: '保洁', plumber: '维修', all: '综合' })[type] || type

const load = async () => {
  loading.value = true
  try {
    profile.value = await fetchMyStaffProfile()
  } catch {
    profile.value = null
  } finally {
    loading.value = false
  }
}

const logout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  store.logout()
  router.replace('/login')
}

onMounted(load)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.staff-profile {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 160px;
}

.hero {
  border-radius: $cct-radius;
  padding: 18px;
  color: #fff;
  background: linear-gradient(135deg, #0f5760 0%, #148a92 100%);
  box-shadow: 0 10px 24px rgba(15, 87, 96, 0.25);
}

.head {
  display: flex;
  align-items: center;
  gap: 12px;

  h2 {
    margin: 0 0 4px;
    font-size: 19px;
  }
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}

.sub {
  margin: 0;
  font-size: 12px;
  opacity: 0.85;
}

.stats {
  display: flex;
  gap: 36px;
  margin-top: 16px;
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
  margin: 0 0 10px;
  font-size: 15px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 0;
  border-bottom: 1px dashed $cct-border;
  font-size: 13px;

  &:last-child {
    border-bottom: none;
  }

  span {
    color: $cct-text-light;
  }

  strong {
    font-weight: 500;
  }
}

.link-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;

  .card-title {
    margin: 0 0 4px;
  }

  .muted {
    margin: 0;
  }

  .el-icon {
    color: #b3c0c6;
  }
}

.logout {
  width: 100%;
}
</style>