<template>
  <div class="login-wrapper">
    <!-- Brand Panel -->
    <div class="brand-panel">
      <div class="brand-content">
        <img src="@/assets/logo.svg" alt="FabLab" class="brand-logo" />
        <h1 class="brand-title">FabLab</h1>
        <p class="brand-subtitle">法贝实验室管理系统</p>
        <div class="brand-features">
          <div class="feature-item">
            <el-icon><DataLine /></el-icon>
            <span>数据驱动决策</span>
          </div>
          <div class="feature-item">
            <el-icon><User /></el-icon>
            <span>智能用户管理</span>
          </div>
          <div class="feature-item">
            <el-icon><TrendCharts /></el-icon>
            <span>实时数据分析</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Login Form Panel -->
    <div class="form-panel">
      <div class="form-content">
        <h2 class="form-title">欢迎登录</h2>
        <p class="form-desc">登录以访问管理后台</p>

        <el-form @submit.prevent="handleLogin" class="login-form" :model="formState" :rules="formRules">
          <el-form-item prop="userId">
            <el-input
              v-model="userId"
              placeholder="用户 ID"
              size="large"
              prefix-icon="User"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="password"
              type="password"
              placeholder="密码"
              size="large"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-btn"
          >
            登录
          </el-button>
        </el-form>

        <el-divider>
          <span class="divider-text">或使用微信扫码</span>
        </el-divider>

        <div v-if="!qrUrl" class="qr-placeholder">
          <el-icon :size="40" color="var(--fab-text-secondary)"><Connection /></el-icon>
          <p>微信扫码暂未开放</p>
        </div>
        <div v-else class="qr-section">
          <img :src="qrUrl" alt="登录二维码" class="qr-img" />
          <p>打开微信扫一扫</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormRules } from 'element-plus'
import { DataLine, User, TrendCharts, Connection } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const userId = ref('')
const password = ref('')
const loading = ref(false)

const formState = reactive({ userId, password })
const formRules: FormRules = {
  userId: [{ required: true, message: '请输入用户 ID', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
}

const ERROR_MAP: Record<string, string> = {
  '用户不存在': '账号不存在，请检查用户 ID',
  '密码错误': '密码不正确，请重新输入',
  '密码未设置': '该账号未设置密码，请联系管理员',
}

function friendlyError(detail: string): string {
  if (!detail) return '登录失败，请重试'
  for (const [key, msg] of Object.entries(ERROR_MAP)) {
    if (detail.includes(key)) return msg
  }
  return detail
}

const qrUrl = ref('')
const qrState = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null

async function handleLogin() {
  if (!userId.value || !password.value) {
    ElMessage.warning('请输入用户ID和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await authApi.login(userId.value, password.value)
    const user = data.data.user
    // Token is set via HttpOnly Cookie by backend — no localStorage needed
    authStore.setUser(user)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { detail?: string } } }
    const status = err.response?.status
    const detail = err.response?.data?.detail || ''
    if (status === 429) {
      ElMessage.warning('登录失败次数过多，请稍后再试')
    } else {
      ElMessage.error(friendlyError(detail))
    }
  } finally {
    loading.value = false
  }
}

async function fetchQrCode() {
  try {
    const { data } = await authApi.getQrCode()
    qrUrl.value = data.data.url
    qrState.value = data.data.state
    startPolling()
  } catch {
    // no WeChat config — QR code unavailable
  }
}

function startPolling() {
  stopPolling()
  let attempts = 0
  pollTimer = setInterval(async () => {
    attempts++
    if (attempts > 120) { stopPolling(); return }
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
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

onMounted(fetchQrCode)
onUnmounted(stopPolling)
</script>

<style scoped>
.login-wrapper {
  display: flex;
  min-height: 100vh;
}

/* ─── Brand Panel ─── */
.brand-panel {
  flex: 1;
  background: linear-gradient(135deg, #0c4a6e 0%, #0ea5e9 50%, #38bdf8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  position: relative;
  overflow: hidden;
}

.brand-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.08) 0%, transparent 50%);
}

.brand-content {
  position: relative;
  z-index: 1;
  text-align: center;
  color: #fff;
}

.brand-logo {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  filter: brightness(0) invert(1);
}

.brand-title {
  font-size: 42px;
  font-weight: 800;
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.brand-subtitle {
  font-size: 16px;
  opacity: 0.85;
  margin-bottom: 40px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: left;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  opacity: 0.9;
}

/* ─── Form Panel ─── */
.form-panel {
  width: 440px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--fab-header-bg);
  transition: background 0.3s;
}

.form-content {
  width: 100%;
  max-width: 340px;
}

.form-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--fab-text);
  margin-bottom: 4px;
}

.form-desc {
  font-size: 14px;
  color: var(--fab-text-secondary);
  margin-bottom: 32px;
}

.login-form {
  margin-bottom: 0;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
}

.divider-text {
  font-size: 12px;
  color: var(--fab-text-secondary);
}

.qr-placeholder,
.qr-section {
  text-align: center;
  color: var(--fab-text-secondary);
  font-size: 13px;
}

.qr-img {
  width: 160px;
  height: 160px;
  border-radius: 8px;
  margin-bottom: 8px;
}

/* ─── Dark mode brand panel ─── */
html.dark .brand-panel {
  background: linear-gradient(135deg, #082f49 0%, #0369a1 50%, #0284c7 100%);
}

/* ─── Mobile ─── */
@media (max-width: 768px) {
  .brand-panel { display: none; }
  .form-panel { width: 100%; }
}
</style>
