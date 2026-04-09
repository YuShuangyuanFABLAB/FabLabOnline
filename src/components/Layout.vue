<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px">
      <el-menu :default-active="route.path" router>
        <h3 style="padding: 16px; margin: 0">法贝实验室</h3>
        <el-menu-item index="/">
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item v-if="showMenu('user')" index="/users">
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item v-if="showMenu('campus')" index="/campuses">
          <span>校区管理</span>
        </el-menu-item>
        <el-menu-item v-if="showMenu('analytics')" index="/analytics">
          <span>数据分析</span>
        </el-menu-item>
        <el-menu-item v-if="showMenu('audit')" index="/audit">
          <span>审计日志</span>
        </el-menu-item>
        <el-menu-item v-if="showMenu('roles')" index="/roles">
          <span>角色管理</span>
        </el-menu-item>
        <el-menu-item v-if="showMenu('apps')" index="/apps">
          <span>应用管理</span>
        </el-menu-item>
        <el-menu-item v-if="showMenu('config')" index="/config">
          <span>系统配置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; justify-content: flex-end; align-items: center">
        <span v-if="authStore.user">{{ authStore.user.name }}</span>
        <el-button type="text" @click="handleLogout">退出</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

/** 根据角色决定菜单可见性 */
const menuVisibility: Record<string, string[]> = {
  user: ['super_admin', 'org_admin', 'campus_admin'],
  campus: ['super_admin', 'org_admin', 'campus_admin'],
  analytics: ['super_admin', 'org_admin', 'campus_admin'],
  audit: ['super_admin', 'org_admin'],
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

async function handleLogout() {
  try {
    await authApi.logout()
  } catch {
    // ignore
  }
  authStore.logout()
  router.push('/login')
}
</script>
