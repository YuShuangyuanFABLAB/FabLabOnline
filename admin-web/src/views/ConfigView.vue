<template>
  <div class="config-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <span class="card-title">系统配置</span>
      </template>
      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column prop="key" label="配置项" width="200" />
        <el-table-column prop="value" label="值" show-overflow-tooltip />
        <el-table-column prop="description" label="说明" width="200" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" plain @click="editConfig(row)">
              <el-icon class="btn-icon"><Edit /></el-icon>
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Edit Dialog -->
    <el-dialog v-model="dialogVisible" title="编辑配置" width="520px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="配置项">
          <el-input :model-value="form.key" disabled />
        </el-form-item>
        <el-form-item label="值">
          <el-input v-model="form.value" type="textarea" :rows="4" />
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
import { Edit } from '@element-plus/icons-vue'
import client from '@/api/client'

interface ConfigRow {
  key: string
  value: string
  description?: string
  [k: string]: unknown
}

const loading = ref(false)
const configs = ref<ConfigRow[]>([])
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

function editConfig(row: ConfigRow) {
  form.value = {
    key: row.key,
    value: typeof row.value === 'string' ? row.value : JSON.stringify(row.value),
  }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    await client.put(`/config/${form.value.key}`, { value: form.value.value })
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchConfigs()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '保存失败')
  }
}

onMounted(fetchConfigs)
</script>

<style scoped>
.table-card {
  border-radius: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}

.btn-icon {
  margin-right: 4px;
}
</style>
