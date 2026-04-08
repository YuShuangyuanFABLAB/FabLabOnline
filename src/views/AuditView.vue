<template>
  <div class="audit">
    <el-card>
      <template #header>
        <span>审计日志</span>
      </template>
      <el-table :data="logs" stripe v-loading="loading">
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="user_id" label="操作人" width="120" />
        <el-table-column prop="action" label="动作" width="100" />
        <el-table-column prop="resource_type" label="资源类型" width="120" />
        <el-table-column prop="resource_id" label="资源ID" width="120" />
        <el-table-column label="变更详情">
          <template #default="{ row }">
            <pre v-if="row.changes">{{ JSON.stringify(row.changes, null, 2) }}</pre>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page"
        :page-size="20"
        :total="total"
        @current-change="fetchLogs"
        style="margin-top: 16px"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import client from '@/api/client'

const logs = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

async function fetchLogs() {
  loading.value = true
  try {
    const { data } = await client.get('/audit/logs', { params: { page: page.value, size: 20 } })
    logs.value = data.data ?? []
    total.value = data.total ?? 0
  } catch {
    logs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>
