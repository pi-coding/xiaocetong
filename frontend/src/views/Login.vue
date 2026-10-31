<template>
  <div class="login-page">
    <section class="brand-panel">
      <div class="brand-head">
        <div class="mark"><el-icon :size="24"><Brush /></el-icon></div>
        <span>校厕通</span>
      </div>

      <h2>校园厕所智能管家</h2>
      <p class="slogan">一个报单入口 · 一条处置链路 · 一套运营数据</p>

      <ul class="highlights">
        <li v-for="item in highlights" :key="item.title">
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <div>
            <strong>{{ item.title }}</strong>
            <span>{{ item.desc }}</span>
          </div>
        </li>
      </ul>

      <div class="stats">
        <div><strong>三端协同</strong><span>学生 / 管理 / 员工</span></div>
        <div><strong>AI 派单</strong><span>可解释加权评分</span></div>
        <div><strong>超时预警</strong><span>三级分级提醒</span></div>
      </div>
    </section>

    <section class="form-panel">
      <div class="form-card">
        <h3>欢迎回来</h3>
        <p class="muted">登录后自动进入对应工作台</p>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="submit">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="学号 / 工号 / 用户名" :prefix-icon="User" clearable />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="密码" :prefix-icon="Lock" />
          </el-form-item>
          <el-button type="primary" class="submit" :loading="loading" @click="submit">登 录</el-button>
        </el-form>

        <div class="demo">
          <span class="muted">演示账号（点击填充）</span>
          <div class="demo-tags">
            <el-tag
              v-for="account in demoAccounts"
              :key="account.username"
              effect="plain"
              class="demo-tag"
              @click="fill(account)"
            >
              {{ account.label }}
            </el-tag>
          </div>
        </div>

        <div class="foot">
          还没有账号？<router-link to="/register">学生注册</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const highlights = [
  { icon: 'ChatDotRound', title: '学生一键报单', desc: '绑定宿舍厕所，通厕 / 清洁 / 报修直达' },
  { icon: 'MagicStick', title: 'AI 智能派单', desc: '区域、负载、时效、评分四维打分' },
  { icon: 'AlarmClock', title: '超时未打扫预警', desc: '按清洁周期自动分级提醒' },
  { icon: 'TrendCharts', title: '运营统计报表', desc: '投诉热力、满意度、员工绩效' },
]

const demoAccounts = [
  { username: '2023101', label: '学生 2023101' },
  { username: 'admin', label: '管理员 admin' },
  { username: 'staff001', label: '员工 staff001' },
]

const fill = (account) => {
  form.username = account.username
  form.password = '123456'
}

const submit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await store.login({ username: form.username.trim(), password: form.password })
    ElMessage.success(`欢迎回来，${store.displayName}`)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    const section = store.homePath.split('/')[1]
    const target = redirect.startsWith(`/${section}/`) ? redirect : store.homePath
    router.replace(target)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (typeof route.query.username === 'string') {
    form.username = route.query.username
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.login-page {
  min-height: 100vh;
  display: flex;
  background: #f6fafb;
}

.brand-panel {
  flex: 1.15;
  padding: 56px 64px;
  color: #fff;
  background: linear-gradient(150deg, #0b4a52 0%, #0e7c80 55%, #12b3b0 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;

  &::after {
    content: '';
    position: absolute;
    width: 420px;
    height: 420px;
    right: -120px;
    bottom: -140px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
  }
}

.brand-head {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 3px;
  margin-bottom: 40px;
}

.mark {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-panel h2 {
  font-size: 34px;
  margin: 0 0 14px;
  letter-spacing: 1px;
}

.slogan {
  margin: 0 0 36px;
  font-size: 15px;
  opacity: 0.86;
  letter-spacing: 0.5px;
}

.highlights {
  list-style: none;
  padding: 0;
  margin: 0 0 40px;
  display: grid;
  gap: 18px;
  max-width: 440px;

  li {
    display: flex;
    gap: 14px;
    align-items: flex-start;
  }

  strong {
    display: block;
    font-size: 15px;
    margin-bottom: 4px;
  }

  span {
    font-size: 13px;
    opacity: 0.8;
  }
}

.stats {
  display: flex;
  gap: 36px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);

  strong {
    display: block;
    font-size: 18px;
  }

  span {
    font-size: 12px;
    opacity: 0.75;
  }
}

.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}

.form-card {
  width: 100%;
  max-width: 380px;

  h3 {
    margin: 0 0 6px;
    font-size: 24px;
  }

  .muted {
    margin: 0 0 26px;
  }
}

.submit {
  width: 100%;
  height: 46px;
  font-size: 15px;
  letter-spacing: 4px;
  margin-top: 6px;
}

.demo {
  margin-top: 26px;
  padding: 14px;
  border-radius: 12px;
  background: #f1f8f8;
}

.demo-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.demo-tag {
  cursor: pointer;

  &:hover {
    color: $cct-primary;
    border-color: $cct-primary;
  }
}

.foot {
  margin-top: 22px;
  font-size: 13px;
  color: $cct-text-light;
  text-align: center;
}

@media (max-width: 900px) {
  .brand-panel {
    display: none;
  }

  .form-panel {
    padding: 28px 18px;
  }
}
</style>