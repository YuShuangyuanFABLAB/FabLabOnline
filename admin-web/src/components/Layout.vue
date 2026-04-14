<template>
  <el-container class="layout-container">
    <!-- Sidebar — always dark -->
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="sidebar-header">
        <img src="@/assets/logo.svg" alt="FabLab" class="sidebar-logo" />
        <transition name="fade-text">
          <span v-if="!collapsed" class="sidebar-title">FabLab</span>
        </transition>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
        background-color="transparent"
        text-color="var(--fab-sidebar-text)"
        active-text-color="var(--fab-sidebar-active)"
      >
        <el-menu-item index="/">
          <el-icon><DataLine /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>

        <el-menu-item v-if="showMenu('user')" index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>

        <el-menu-item v-if="showMenu('campus')" index="/campuses">
          <el-icon><OfficeBuilding /></el-icon>
          <template #title>校区管理</template>
        </el-menu-item>

        <el-menu-item v-if="showMenu('analytics')" index="/analytics">
          <el-icon><TrendCharts /></el-icon>
          <template #title>数据分析</template>
        </el-menu-item>

        <el-menu-item v-if="showMenu('audit')" index="/audit">
          <el-icon><Document /></el-icon>
          <template #title>审计日志</template>
        </el-menu-item>

        <el-menu-item v-if="showMenu('roles')" index="/roles">
          <el-icon><Key /></el-icon>
          <template #title>角色管理</template>
        </el-menu-item>

        <el-menu-item v-if="showMenu('apps')" index="/apps">
          <el-icon><Grid /></el-icon>
          <template #title>应用管理</template>
        </el-menu-item>

        <el-menu-item v-if="showMenu('config')" index="/config">
          <el-icon><Setting /></el-icon>
          <template #title>系统配置</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer" @click="collapsed = !collapsed">
        <el-icon :size="18">
          <DArrowLeft v-if="!collapsed" />
          <DArrowRight v-else />
        </el-icon>
      </div>
    </el-aside>

    <!-- Main area -->
    <el-container class="main-area">
      <el-header class="app-header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-switch
            v-model="isDark"
            :active-icon="Moon"
            :inactive-icon="Sunny"
            inline-prompt
            class="dark-toggle"
          />
          <el-dropdown trigger="click" @command="onDropdownCommand">
            <span class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ authStore.user?.name?.charAt(0) ?? '?' }}
              </el-avatar>
              <span class="user-name">{{ authStore.user?.name }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  {{ authStore.highestRole }}
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDark } from '@vueuse/core'
import { ElMessageBox } from 'element-plus'
import {
  DataLine,
  User,
  OfficeBuilding,
  TrendCharts,
  Document,
  Key,
  Grid,
  Setting,
  DArrowLeft,
  DArrowRight,
  Moon,
  Sunny,
  ArrowDown,
  SwitchButton,
} from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const collapsed = ref(false)
const isDark = useDark()

const pageTitles: Record<string, string> = {
  '/': '数据看板',
  '/users': '用户管理',
  '/campuses': '校区管理',
  '/analytics': '数据分析',
  '/audit': '审计日志',
  '/roles': '角色管理',
  '/apps': '应用管理',
  '/config': '系统配置',
}

const pageTitle = computed(() => pageTitles[route.path] ?? '法贝实验室')

const menuVisibility: Record<string, string[]> = {
  user: ['super_admin', 'admin'],
  campus: ['super_admin', 'admin'],
  analytics: ['super_admin', 'admin'],
  audit: ['super_admin', 'admin'],
  roles: ['super_admin'],
  apps: ['super_admin'],
  config: ['super_admin'],
}

function showMenu(resource: string): boolean {
  const allowed = menuVisibility[resource]
  if (!allowed) return true
  const role = authStore.highestRole
  if (!role) return false
  return allowed.includes(role)
}

function onDropdownCommand(cmd: string) {
  if (cmd === 'logout') handleLogout()
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定退出登录？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await authApi.logout()
  } catch {
    // ignore
  }
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
}

/* ─── Sidebar ─── */
.sidebar {
  background: var(--fab-sidebar-bg);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-logo {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.sidebar-menu {
  flex: 1;
  border-right: none !important;
  padding-top: 8px;
}

.sidebar-menu .el-menu-item {
  height: 44px;
  line-height: 44px;
  margin: 2px 8px;
  border-radius: 6px;
}

.sidebar-menu .el-menu-item.is-active {
  background: rgba(14, 165, 233, 0.12) !important;
  color: var(--fab-sidebar-active) !important;
}

.sidebar-menu .el-menu-item:hover:not(.is-active) {
  background: rgba(255, 255, 255, 0.05) !important;
}

.sidebar-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px 0;
  cursor: pointer;
  color: var(--fab-sidebar-text);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  transition: background 0.2s;
}

.sidebar-footer:hover {
  background: rgba(255, 255, 255, 0.05);
}

/* ─── Main Area ─── */
.main-area {
  background: var(--fab-bg);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--fab-header-bg);
  border-bottom: 1px solid var(--fab-header-border);
  padding: 0 24px;
  height: 56px;
  transition: background 0.3s, border-color 0.3s;
}

.header-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--fab-text);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.dark-toggle {
  --el-switch-on-color: #334155;
  --el-switch-off-color: #e2e8f0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--fab-text);
}

.user-avatar {
  background: var(--fab-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
}

.app-main {
  padding: 24px;
  background: var(--fab-bg);
  min-height: calc(100vh - 56px);
}

/* ─── Transitions ─── */
.fade-text-enter-active,
.fade-text-leave-active {
  transition: opacity 0.2s;
}
.fade-text-enter-from,
.fade-text-leave-to {
  opacity: 0;
}
</style>
