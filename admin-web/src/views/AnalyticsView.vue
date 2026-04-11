<template>
  <div class="analytics-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">数据分析</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="fetchUsage"
          />
        </div>
      </template>

      <el-table :data="usageData" stripe>
        <el-table-column prop="campus_name" label="校区" />
        <el-table-column prop="total_events" label="事件总数" width="120" />
        <el-table-column prop="active_users" label="活跃用户" width="120" />
        <el-table-column prop="top_app" label="热门应用" width="160" />
      </el-table>

      <el-empty v-if="!usageData.length" description="选择日期范围查看分析数据" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { analyticsApi } from '@/api/analytics'

const dateRange = ref<[Date, Date] | null>(null)
const usageData = ref<Record<string, unknown>[]>([])

async function fetchUsage() {
  if (!dateRange.value) return
  const [start, end] = dateRange.value
  const fmt = (d: Date) => d.toISOString().slice(0, 10)
  const resp = await analyticsApi.getUsage(fmt(start), fmt(end))
  usageData.value = resp.data?.data ?? []
}
</script>

<style scoped>
.table-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}
</style>
