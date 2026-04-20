<template>
  <div class="password-page">
    <el-card class="password-card">
      <template #header>
        <span class="card-title">修改密码</span>
      </template>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="form.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="form.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">确认修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { authApi } from '@/api/auth'

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  old_password: '',
  new_password: '',
  confirm: '',
})

const rules: FormRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度 8-128 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.new_password) callback(new Error('两次密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await authApi.changePassword(form.old_password, form.new_password)
    if (res.data?.success) {
      ElMessage.success('密码修改成功')
      form.old_password = ''
      form.new_password = ''
      form.confirm = ''
      formRef.value?.resetFields()
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '修改失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.password-page {
  max-width: 480px;
  margin: 0 auto;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
}
</style>
