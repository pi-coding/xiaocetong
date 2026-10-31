<template>
  <div class="staff-shell">
    <div class="phone">
      <header class="app-header">
        <div class="brand">
          <div class="logo">
            <el-icon :size="20"><Tools /></el-icon>
          </div>
          <div class="brand-text">
            <h1>校厕通 · 员工端</h1>
            <p>{{ store.displayName }} · {{ store.user?.username }}</p>
          </div>
        </div>
        <el-dropdown trigger="click" @command="onCommand">
          <span class="avatar">{{ avatarText }}</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
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
import { enabledMenus, staffTabs } from '@/router/menus'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const tabs = enabledMenus(staffTabs)
const avatarText = computed(() => store.displayName.slice(0, 1))

const onCommand = async (command) => {
  if (command !== 'logout') return
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

.staff-shell {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  background: linear-gradient(160deg, #eaf3f7 0%, #f5f8f9 100%);
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
  background: linear-gradient(135deg, #0f5760 0%, #148a92 100%);
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
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text h1 {
  margin: 0;
  font-size: 16px;
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
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  cursor: pointer;
}

.app-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
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

  &.active {
    color: $cct-primary;
    font-weight: 600;
  }
}
</style>