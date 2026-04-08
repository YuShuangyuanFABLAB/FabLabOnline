<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>法贝实验室管理系统</h2>
      <div v-if="!qrUrl" class="loading">加载中...</div>
      <div v-else class="qrcode-section">
        <p>请使用微信扫描二维码登录</p>
        <img :src="qrUrl" alt="登录二维码" class="qrcode-img" />
        <p v-if="expired" class="expired">二维码已过期，<el-link @click="fetchQrCode">点击刷新</el-link></p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const qrUrl = ref('')
const qrState = ref('')
const expired = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

async function fetchQrCode() {
  try {
    const { data } = await authApi.getQrCode()
    qrUrl.value = data.data.url
    qrState.value = data.data.state
    expired.value = false
    startPolling()
  } catch {
    ElMessage.error('获取二维码失败')
  }
}

function startPolling() {
  stopPolling()
  let attempts = 0
  pollTimer = setInterval(async () => {
    attempts++
    if (attempts > 120) {
      expired.value = true
      stopPolling()
      return
    }
    try {
      const { data } = await authApi.getStatus(qrState.value)
      if (data.data?.status === 'authenticated') {
        authStore.setUser(data.data.user)
        stopPolling()
        router.push('/')
      }
    } catch {
      // continue polling
    }
  }, 1000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(fetchQrCode)
onUnmounted(stopPolling)
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
.login-card {
  width: 400px;
  text-align: center;
}
.qrcode-img {
  width: 200px;
  height: 200px;
}
.expired {
  color: #e6a23c;
}
</style>
