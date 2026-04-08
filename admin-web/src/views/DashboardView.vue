<template>
  <div>
    <h2>数据看板</h2>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-statistic title="今日事件" :value="dashboard.today_events ?? 0" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="活跃用户" :value="dashboard.active_users ?? 0" />
      </el-col>
    </el-row>
    <el-table :data="dashboard.event_summary ?? []" style="margin-top: 20px">
      <el-table-column prop="event_type" label="事件类型" />
      <el-table-column prop="total" label="总数" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { analyticsApi } from '@/api/analytics'

const dashboard = ref<Record<string, unknown>>({})

onMounted(async () => {
  try {
    const { data } = await analyticsApi.getDashboard()
    dashboard.value = data.data
  } catch {
    // will show empty state
  }
})
</script>
