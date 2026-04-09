<template>
  <div>
    <h2>应用管理</h2>
    <el-table :data="apps" v-loading="loading">
      <el-table-column prop="id" label="ID" />
      <el-table-column prop="name" label="应用名" />
      <el-table-column prop="app_key" label="App Key" />
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button
            size="small"
            :type="row.status === 'active' ? 'danger' : 'success'"
            @click="toggleStatus(row)"
          >
            {{ row.status === 'active' ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import client from '@/api/client'

const loading = ref(false)
const apps = ref<any[]>([])

async function fetchApps() {
  loading.value = true
  try {
    const { data } = await client.get('/apps')
    apps.value = data.data?.items || data.data || []
  } catch {
    apps.value = []
  } finally {
    loading.value = false
  }
}

async function toggleStatus(app: any) {
  try {
    const newStatus = app.status === 'active' ? 'disabled' : 'active'
    await client.put(`/apps/${app.id}/status`, { status: newStatus })
    ElMessage.success('状态已更新')
    await fetchApps()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

onMounted(fetchApps)
</script>
