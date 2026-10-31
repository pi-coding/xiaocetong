<template>
  <div class="result-page">
    <el-result icon="info" title="页面不存在" sub-title="你访问的地址不存在，可能已被移除或输入有误。">
      <template #extra>
        <el-button type="primary" @click="goHome">回到首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

const goHome = () => router.replace(store.isLogin ? store.homePath : '/login')
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