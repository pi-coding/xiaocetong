<template>
  <div class="result-page">
    <el-result icon="warning" title="无访问权限" sub-title="当前账号的角色无法访问该页面，请切换到对应工作台。">
      <template #extra>
        <el-button type="primary" @click="goHome">返回我的工作台</el-button>
        <el-button @click="logout">切换账号</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

const goHome = () => router.replace(store.homePath)

const logout = () => {
  store.logout()
  router.replace('/login')
}
</script>

<style scoped>
.result-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4f8f9;
}
</style>