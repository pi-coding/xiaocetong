<template>
  <div class="student-shell">
    <div class="phone">
      <header class="app-header">
        <div class="brand">
          <div class="logo">
            <el-icon :size="20"><Brush /></el-icon>
          </div>
          <div class="brand-text">
            <h1>校厕通</h1>
            <p>{{ store.roleName }} · {{ store.displayName }}</p>
          </div>
        </div>
        <el-dropdown trigger="click" @command="onCommand">
          <span class="avatar">{{ avatarText }}</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>

      <main class="app-body">
        <router-view />
      </main>

      <nav class="tabbar">
        <button
          v-for="tab in tabs"
          :key="tab.path"
          type="button"
          class="tab"
          :class="{ active: route.path.startsWith(tab.path) }"
          @click="router.push(tab.path)"
        >
          <el-icon :size="20"><component :is="tab.icon" /></el-icon>
          <span>{{ tab.title }}</span>
        </button>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { enabledMenus, studentTabs } from '@/router/menus'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const tabs = enabledMenus(studentTabs)

const avatarText = computed(() => store.displayName.slice(0, 1))

const onCommand = async (command) => {
  if (command === 'profile') {
    router.push('/student/profile')
    return
  }
  if (command === 'logout') {
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
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.student-shell {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  background: linear-gradient(160deg, #e8f6f5 0%, #f4f8f9 45%, #eef3f5 100%);
}

.phone {
  width: 100%;
  max-width: 480px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: $cct-bg;
  box-shadow: 0 0 40px rgba(15, 76, 86, 0.12);
}

.app-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(135deg, $cct-primary 0%, #12b8b6 100%);
  color: #fff;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text h1 {
  margin: 0;
  font-size: 17px;
  letter-spacing: 1px;
}

.brand-text p {
  margin: 2px 0 0;
  font-size: 12px;
  opacity: 0.85;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  cursor: pointer;
}

.app-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px 14px 18px;
}

.tabbar {
  flex-shrink: 0;
  display: flex;
  background: #fff;
  border-top: 1px solid $cct-border;
  padding: 6px 4px calc(6px + env(safe-area-inset-bottom));
}

.tab {
  flex: 1;
  border: none;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 6px 0;
  font-size: 11px;
  color: $cct-text-light;
  cursor: pointer;
  border-radius: 10px;
  transition: color 0.2s ease;

  &.active {
    color: $cct-primary;
    font-weight: 600;
  }
}
</style>