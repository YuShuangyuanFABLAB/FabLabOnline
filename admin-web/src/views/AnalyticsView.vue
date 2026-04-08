<template>
  <div class="analytics">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据分析</span>
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
        <el-table-column prop="total_events" label="事件总数" />
        <el-table-column prop="active_users" label="活跃用户" />
        <el-table-column prop="top_app" label="热门应用" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { analyticsApi } from '../api/analytics'

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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
