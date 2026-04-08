<template>
  <el-dialog v-model="visible" title="扫码登录" width="360px" :close-on-click-modal="false">
    <div class="qrcode-wrapper">
      <img v-if="qrUrl" :src="qrUrl" alt="二维码" class="qrcode-img" />
      <el-skeleton v-else :rows="5" animated />
      <p class="hint">请使用微信扫描二维码登录</p>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { authApi } from '../api/auth'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: boolean): void }>()

const visible = ref(props.modelValue)
const qrUrl = ref('')

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) fetchQrCode()
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

async function fetchQrCode() {
  try {
    const resp = await authApi.getQrCode()
    qrUrl.value = resp.data?.data?.url ?? ''
  } catch {
    qrUrl.value = ''
  }
}
</script>

<style scoped>
.qrcode-wrapper {
  text-align: center;
}
.qrcode-img {
  width: 200px;
  height: 200px;
}
.hint {
  margin-top: 12px;
  color: #909399;
}
</style>
