<template>
  <div class="register-page">
    <div class="card">
      <div class="head">
        <div class="mark"><el-icon :size="22"><Brush /></el-icon></div>
        <div>
          <h3>学生注册</h3>
          <p class="muted">注册后即可绑定宿舍厕所并提交工单</p>
        </div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="账号（学号）" prop="username">
          <el-input v-model="form.username" placeholder="如 2023201，仅字母数字下划线" clearable />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入真实姓名" clearable />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="选填，便于联系" clearable />
        </el-form-item>
        <div class="row">
          <el-form-item label="楼栋" prop="building">
            <el-select v-model="form.building" placeholder="选择楼栋">
              <el-option v-for="item in buildings" :key="item" :label="`${item} 栋`" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="宿舍号" prop="room_no">
            <el-input v-model="form.room_no" placeholder="如 301" clearable />
          </el-form-item>
        </div>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="6-32 位" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password placeholder="再次输入密码" />
        </el-form-item>

        <el-button type="primary" class="submit" :loading="loading" @click="submit">注 册</el-button>
      </el-form>

      <div class="foot">已有账号？<router-link to="/login">返回登录</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { registerApi } from '@/api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const buildings = ['A', 'B', 'C', 'D']

const form = reactive({
  username: '',
  real_name: '',
  phone: '',
  building: 'D',
  room_no: '',
  password: '',
  confirm: '',
})

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 50, message: '长度 3-50 位', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_]+$/, message: '仅支持字母、数字、下划线', trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  building: [{ required: true, message: '请选择楼栋', trigger: 'change' }],
  room_no: [{ required: true, message: '请输入宿舍号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码 6-32 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

const submit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await registerApi({
      username: form.username.trim(),
      password: form.password,
      real_name: form.real_name.trim(),
      phone: form.phone.trim() || null,
      student_no: form.username.trim(),
      building: form.building,
      room_no: form.room_no.trim(),
    })
    await ElMessageBox.alert('注册成功，请使用该账号登录', '注册完成', {
      confirmButtonText: '去登录',
      type: 'success',
    })
    ElMessage.success('请登录')
    router.replace({ path: '/login', query: { username: form.username.trim() } })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background: linear-gradient(150deg, #e9f6f6 0%, #f6fafb 55%, #eef3f6 100%);
}

.card {
  width: 100%;
  max-width: 460px;
  background: #fff;
  border-radius: 18px;
  box-shadow: $cct-shadow;
  padding: 28px 26px;
}

.head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 22px;

  h3 {
    margin: 0 0 4px;
    font-size: 20px;
  }

  .muted {
    margin: 0;
  }
}

.mark {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  background: linear-gradient(135deg, $cct-primary, #12b8b6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.submit {
  width: 100%;
  height: 44px;
  font-size: 15px;
  letter-spacing: 4px;
  margin-top: 4px;
}

.foot {
  margin-top: 18px;
  text-align: center;
  font-size: 13px;
  color: $cct-text-light;
}
</style>