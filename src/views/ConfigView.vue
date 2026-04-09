<template>
  <div>
    <h2>系统配置</h2>
    <el-table :data="configs" v-loading="loading">
      <el-table-column prop="key" label="配置项" />
      <el-table-column prop="value" label="值" />
      <el-table-column prop="description" label="说明" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" @click="editConfig(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="编辑配置" width="500px">
      <el-form label-width="80px">
        <el-form-item label="配置项">
          <el-input :model-value="form.key" disabled />
        </el-form-item>
        <el-form-item label="值">
          <el-input v-model="form.value" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import client from '@/api/client'

const loading = ref(false)
const configs = ref<any[]>([])
const dialogVisible = ref(false)
const form = ref({ key: '', value: '' })

async function fetchConfigs() {
  loading.value = true
  try {
    const { data } = await client.get('/config')
    configs.value = data.data?.items || data.data || []
  } catch {
    configs.value = []
  } finally {
    loading.value = false
  }
}

function editConfig(row: any) {
  form.value = { key: row.key, value: typeof row.value === 'string' ? row.value : JSON.stringify(row.value) }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    await client.put(`/config/${form.value.key}`, { value: form.value.value })
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchConfigs()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

onMounted(fetchConfigs)
</script>
