<template>
  <div class="home">
    <section class="hero">
      <div class="hero-top">
        <div>
          <p class="greeting">你好，{{ store.displayName }}</p>
          <p class="sub">{{ user?.student_no || user?.username }} · {{ dormText }}</p>
        </div>
        <div class="points">
          <span>积分</span>
          <strong>{{ user?.points_balance ?? 0 }}</strong>
        </div>
      </div>
      <div class="hero-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>厕所出现堵塞、脏乱或设施损坏，第一时间提交工单，后勤会尽快处理。</span>
      </div>
    </section>

    <section class="page-card binding" @click="router.push('/student/bind')">
      <div class="binding-main">
        <div class="binding-icon">
          <el-icon :size="20"><House /></el-icon>
        </div>
        <div>
          <h3>{{ binding ? `${binding.building} 栋 ${binding.room_no} 宿舍厕所` : '尚未绑定宿舍厕所' }}</h3>
          <p class="muted">
            {{ binding ? `清洁状态：${cleanStatusText(binding.toilet)}` : '绑定后可一键提交通厕、清洁、报修工单' }}
          </p>
        </div>
      </div>
      <el-icon class="arrow"><ArrowRight /></el-icon>
    </section>

    <section class="entries">
      <button
        v-for="item in entries"
        :key="item.path"
        type="button"
        class="entry"
        :class="{ disabled: !item.enabled }"
        @click="go(item)"
      >
        <div class="entry-icon">
          <el-icon :size="22"><component :is="item.icon" /></el-icon>
        </div>
        <div class="entry-text">
          <strong>{{ item.title }}</strong>
          <span>{{ item.desc }}</span>
        </div>
        <el-tag v-if="!item.enabled" size="small" type="info" effect="plain">即将上线</el-tag>
      </button>
    </section>

    <section class="page-card">
      <div class="flex-between">
        <h3 class="card-title">我的信息</h3>
        <el-button link type="primary" @click="router.push('/student/profile')">编辑</el-button>
      </div>
      <div class="info-row"><span>账号</span><strong>{{ user?.username }}</strong></div>
      <div class="info-row"><span>姓名</span><strong>{{ user?.real_name }}</strong></div>
      <div class="info-row"><span>手机号</span><strong>{{ user?.phone || '未填写' }}</strong></div>
      <div class="info-row"><span>宿舍</span><strong>{{ dormText }}</strong></div>
      <div class="info-row"><span>最近登录</span><strong>{{ lastLoginText }}</strong></div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchMyBinding } from '@/api/dormBinding'
import { useUserStore } from '@/stores/user'
import { studentTabs } from '@/router/menus'
import { cleanStatusText } from '@/utils/dict'

const router = useRouter()
const store = useUserStore()
const user = computed(() => store.user)
const binding = ref(null)

const loadBinding = async () => {
  try {
    binding.value = await fetchMyBinding()
  } catch {
    binding.value = null
  }
}

const descMap = {
  '/student/toilets': '查公共厕所位置与清洁状态',
  '/student/orders': '查看报单进度与处理结果',
  '/student/ai': '描述问题，助手帮你下单',
}

const entries = computed(() =>
  studentTabs
    .filter((item) => !['/student/home', '/student/profile'].includes(item.path))
    .map((item) => ({ ...item, desc: descMap[item.path] || '' })),
)

const dormText = computed(() => {
  if (!user.value?.building || !user.value?.room_no) return '未填写宿舍信息'
  return `${user.value.building} 栋 ${user.value.room_no}`
})

const lastLoginText = computed(() => {
  const raw = user.value?.last_login_at
  if (!raw) return '本次为首次登录'
  return String(raw).replace('T', ' ').slice(0, 16)
})

const go = (item) => {
  if (item.enabled) {
    router.push(item.path)
    return
  }
  ElMessage.info(`「${item.title}」将在后续模块上线`)
}

onMounted(loadBinding)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.home {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero {
  border-radius: $cct-radius;
  padding: 18px;
  color: #fff;
  background: linear-gradient(135deg, $cct-primary 0%, #16b8b6 60%, #38d0b8 100%);
  box-shadow: 0 10px 24px rgba(14, 165, 164, 0.28);
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.greeting {
  margin: 0;
  font-size: 19px;
  font-weight: 600;
}

.sub {
  margin: 6px 0 0;
  font-size: 12px;
  opacity: 0.88;
}

.points {
  text-align: right;

  span {
    display: block;
    font-size: 11px;
    opacity: 0.85;
  }

  strong {
    font-size: 24px;
    line-height: 1.2;
  }
}

.hero-tip {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-top: 16px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 12px;
  line-height: 1.5;
}

.entries {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.binding {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;

  h3 {
    margin: 0 0 4px;
    font-size: 14px;
  }

  .muted {
    margin: 0;
  }
}

.binding-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.binding-icon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: #e6f7f6;
  color: $cct-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.arrow {
  color: #b3c0c6;
}

.entry {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  border: 1px solid $cct-border;
  background: #fff;
  border-radius: $cct-radius;
  padding: 14px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: $cct-shadow;
  }

  &.disabled {
    opacity: 0.72;
  }
}

.entry-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #e6f7f6;
  color: $cct-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.entry-text {
  flex: 1;

  strong {
    display: block;
    font-size: 14px;
    margin-bottom: 3px;
  }

  span {
    font-size: 12px;
    color: $cct-text-light;
  }
}

.card-title {
  margin: 0;
  font-size: 15px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px dashed $cct-border;
  font-size: 13px;

  &:last-child {
    border-bottom: none;
  }

  span {
    color: $cct-text-light;
  }
}
</style>