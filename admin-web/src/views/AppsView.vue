<template>
  <div class="apps-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <span class="card-title">应用管理</span>
      </template>
      <el-table :data="apps" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="160" />
        <el-table-column prop="name" label="应用名" width="180" />
        <el-table-column prop="app_key" label="App Key" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small" effect="plain">
              {{ row.status === 'active' ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button
              size="small"
              :type="row.status === 'active' ? 'danger' : 'success'"
              plain
              @click="toggleStatus(row)"
            >
              {{ row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { appsApi } from '@/api/apps'

interface AppRow {
  id: string
  name: string
  app_key: string
  status: string
}

const loading = ref(false)
const apps = ref<AppRow[]>([])

async function fetchApps() {
  loading.value = true
  try {
    const { data } = await appsApi.list()
    apps.value = data.data?.items || data.data || []
  } catch {
    apps.value = []
  } finally {
    loading.value = false
  }
}

async function toggleStatus(app: AppRow) {
  try {
    const newStatus = app.status === 'active' ? 'disabled' : 'active'
    await appsApi.toggleStatus(app.id, newStatus)
    ElMessage.success('状态已更新')
    await fetchApps()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

onMounted(fetchApps)
</script>

<style scoped>
.table-card {
  border-radius: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}
</style>
