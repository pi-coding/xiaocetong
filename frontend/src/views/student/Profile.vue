<template>
  <div class="profile">
    <section class="page-card">
      <div class="head">
        <div class="avatar">{{ avatarText }}</div>
        <div>
          <h3>{{ user?.real_name }}</h3>
          <p class="muted">{{ store.roleName }} · {{ user?.username }}</p>
        </div>
        <el-tag type="success" effect="plain" size="small">积分 {{ user?.points_balance ?? 0 }}</el-tag>
      </div>
    </section>

    <section class="page-card link-card" @click="router.push('/student/bind')">
      <div>
        <h3 class="card-title">宿舍厕所绑定</h3>
        <p class="muted">绑定后可一键通厕、清洁、报修</p>
      </div>
      <el-icon><ArrowRight /></el-icon>
    </section>

    <section class="page-card link-card" @click="router.push('/student/points')">
      <div>
        <h3 class="card-title">我的积分</h3>
        <p class="muted">当前 {{ user?.points_balance ?? 0 }} 分，查看明细与排行榜</p>
      </div>
      <el-icon><ArrowRight /></el-icon>
    </section>

    <section class="page-card">
      <h3 class="card-title">个人资料</h3>
      <el-form :model="profile" label-position="top" size="default">
        <el-form-item label="姓名">
          <el-input v-model="profile.real_name" maxlength="50" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="profile.phone" maxlength="20" placeholder="选填" />
        </el-form-item>
        <div class="row">
          <el-form-item label="楼栋">
            <el-select v-model="profile.building" placeholder="选择楼栋">
              <el-option v-for="item in buildings" :key="item" :label="`${item} 栋`" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="宿舍号">
            <el-input v-model="profile.room_no" maxlength="16" placeholder="如 301" />
          </el-form-item>
        </div>
        <el-button type="primary" :loading="savingProfile" @click="saveProfile">保存资料</el-button>
      </el-form>
    </section>

    <section class="page-card">
      <h3 class="card-title">修改密码</h3>
      <el-form :model="password" label-position="top" size="default">
        <el-form-item label="原密码">
          <el-input v-model="password.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="password.new_password" type="password" show-password placeholder="6-32 位" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="password.confirm" type="password" show-password />
        </el-form-item>
        <el-button type="primary" plain :loading="savingPassword" @click="savePassword">修改密码</el-button>
      </el-form>
    </section>

    <el-button class="logout" type="danger" plain @click="logout">退出登录</el-button>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { changePassword, updateMe } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()
const user = computed(() => store.user)
const avatarText = computed(() => store.displayName.slice(0, 1))
const buildings = ['A', 'B', 'C', 'D']

const profile = reactive({
  real_name: user.value?.real_name || '',
  phone: user.value?.phone || '',
  building: user.value?.building || '',
  room_no: user.value?.room_no || '',
})

const password = reactive({ old_password: '', new_password: '', confirm: '' })

const savingProfile = ref(false)
const savingPassword = ref(false)

const saveProfile = async () => {
  if (!profile.real_name.trim()) {
    ElMessage.warning('姓名不能为空')
    return
  }
  savingProfile.value = true
  try {
    const data = await updateMe({
      real_name: profile.real_name.trim(),
      phone: profile.phone.trim() || null,
      building: profile.building || null,
      room_no: profile.room_no.trim() || null,
    })
    store.updateLocal(data)
    ElMessage.success('资料已保存')
  } finally {
    savingProfile.value = false
  }
}

const savePassword = async () => {
  if (!password.old_password || !password.new_password) {
    ElMessage.warning('请填写完整密码信息')
    return
  }
  if (password.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (password.new_password !== password.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  savingPassword.value = true
  try {
    await changePassword({
      old_password: password.old_password,
      new_password: password.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    store.logout()
    router.replace('/login')
  } finally {
    savingPassword.value = false
  }
}

const logout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    store.logout()
    router.replace('/login')
  } catch {
    /* 用户取消 */
  }
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.profile {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.head {
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

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, $cct-primary, #38d0b8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}

.card-title {
  margin: 0 0 14px;
  font-size: 15px;
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

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.logout {
  width: 100%;
}
</style>