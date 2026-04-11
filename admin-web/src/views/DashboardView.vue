<template>
  <div class="dashboard">
    <!-- Stat Cards -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <div class="stat-card stat-card--blue">
          <div class="stat-icon"><el-icon :size="28"><DataLine /></el-icon></div>
          <div class="stat-info">
            <span class="stat-value">{{ dashboard.today_events ?? 0 }}</span>
            <span class="stat-label">今日事件</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--green">
          <div class="stat-icon"><el-icon :size="28"><User /></el-icon></div>
          <div class="stat-info">
            <span class="stat-value">{{ dashboard.active_users ?? 0 }}</span>
            <span class="stat-label">活跃用户</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--orange">
          <div class="stat-icon"><el-icon :size="28"><OfficeBuilding /></el-icon></div>
          <div class="stat-info">
            <span class="stat-value">{{ dashboard.campus_count ?? 0 }}</span>
            <span class="stat-label">校区数量</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-card--purple">
          <div class="stat-icon"><el-icon :size="28"><Grid /></el-icon></div>
          <div class="stat-info">
            <span class="stat-value">{{ dashboard.app_count ?? 0 }}</span>
            <span class="stat-label">应用总数</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Event Summary -->
    <el-card class="summary-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">事件汇总</span>
        </div>
      </template>
      <el-table :data="dashboard.event_summary ?? []" stripe>
        <el-table-column prop="event_type" label="事件类型" />
        <el-table-column prop="total" label="总数" width="120" />
      </el-table>
      <el-empty v-if="!((dashboard.event_summary as unknown[])?.length)" description="暂无事件数据" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { DataLine, User, OfficeBuilding, Grid } from '@element-plus/icons-vue'
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

<style scoped>
.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 8px;
  color: #fff;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card--blue { background: linear-gradient(135deg, #0ea5e9, #0284c7); }
.stat-card--green { background: linear-gradient(135deg, #10b981, #059669); }
.stat-card--orange { background: linear-gradient(135deg, #f59e0b, #d97706); }
.stat-card--purple { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  opacity: 0.85;
  margin-top: 2px;
}

.summary-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}
</style>
