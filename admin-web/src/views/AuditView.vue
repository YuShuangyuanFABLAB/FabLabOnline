<template>
  <div class="audit-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <span class="card-title">审计日志</span>
      </template>
      <el-table :data="logs" stripe v-loading="loading">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="user_id" label="操作人" width="120" />
        <el-table-column prop="action" label="动作" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type" label="资源类型" width="120" />
        <el-table-column prop="resource_id" label="资源 ID" width="140" />
        <el-table-column label="变更详情">
          <template #default="{ row }">
            <el-popover
              v-if="row.changes"
              trigger="hover"
              :width="360"
              placement="left"
            >
              <template #reference>
                <el-button size="small" text type="primary">查看详情</el-button>
              </template>
              <pre class="changes-json">{{ JSON.stringify(row.changes, null, 2) }}</pre>
            </el-popover>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        :page-size="20"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchLogs"
        class="pagination"
      />

      <el-empty v-if="!loading && logs.length === 0" description="暂无审计日志" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { auditApi } from '@/api/audit'

const logs = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

function formatTime(ts: unknown): string {
  if (!ts) return ''
  const d = new Date(ts as string)
  return d.toLocaleString('zh-CN')
}

async function fetchLogs() {
  loading.value = true
  try {
    const { data } = await auditApi.list(page.value)
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

<style scoped>
.table-card {
  border-radius: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}

.changes-json {
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
