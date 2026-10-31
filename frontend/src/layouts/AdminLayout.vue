<template>
  <div class="admin-shell">
    <aside class="sidebar">
      <div class="logo-row">
        <div class="logo">
          <el-icon :size="20"><Brush /></el-icon>
        </div>
        <div>
          <h1>校厕通</h1>
          <p>管理端</p>
        </div>
      </div>

      <el-menu :default-active="route.path" router class="menu" background-color="transparent" text-color="#cfe4e6" active-text-color="#ffffff">
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">校园厕所智能管家</div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div>
          <h2>{{ route.meta.title }}</h2>
          <p class="muted">欢迎，{{ store.displayName }}（{{ store.roleName }}）</p>
        </div>
        <el-dropdown trigger="click" @command="onCommand">
          <div class="user-chip">
            <span class="avatar">{{ avatarText }}</span>
            <span class="name">{{ store.displayName }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { adminMenus, enabledMenus } from '@/router/menus'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const menus = enabledMenus(adminMenus)
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

.admin-shell {
  display: flex;
  min-height: 100vh;
  background: $cct-bg;
}

.sidebar {
  width: 224px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #0d3f47 0%, #0f5760 100%);
  display: flex;
  flex-direction: column;
  padding: 18px 12px;
}

.logo-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px 18px;

  h1 {
    margin: 0;
    font-size: 17px;
    color: #fff;
    letter-spacing: 2px;
  }

  p {
    margin: 2px 0 0;
    font-size: 11px;
    color: #8fc3c8;
    letter-spacing: 1px;
  }
}

.logo {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu {
  border-right: none;
  flex: 1;

  :deep(.el-menu-item) {
    border-radius: 10px;
    margin-bottom: 4px;
    height: 44px;

    &:hover {
      background: rgba(255, 255, 255, 0.08);
    }

    &.is-active {
      background: rgba(255, 255, 255, 0.16);
      font-weight: 600;
    }
  }
}

.sidebar-footer {
  padding: 12px 8px 0;
  font-size: 11px;
  color: #7fb2b8;
  text-align: center;
}

.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid $cct-border;

  h2 {
    margin: 0;
    font-size: 18px;
  }

  p {
    margin: 4px 0 0;
  }
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 6px;
  border-radius: 999px;
  background: #f2f7f8;
  cursor: pointer;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: $cct-primary;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.name {
  font-size: 13px;
}

.content {
  flex: 1;
  padding: 20px 24px 28px;
  overflow-y: auto;
}
</style>