<template>
  <div class="campuses-view">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon class="btn-icon"><Plus /></el-icon>
        新增校区
      </el-button>
    </div>

    <!-- Table -->
    <el-card shadow="never" class="table-card">
      <el-table :data="campuses" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="160" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small" effect="plain">
              {{ row.status === 'active' ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" plain @click="openEditDialog(row)">
              <el-icon class="btn-icon"><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(row)">
              <el-icon class="btn-icon"><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Dialog -->
    <el-dialog v-model="showDialog" :title="isEditing ? '编辑校区' : '新增校区'" width="420px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item v-if="!isEditing" label="校区 ID">
          <el-input v-model="form.id" placeholder="输入唯一标识" />
        </el-form-item>
        <el-form-item label="校区名称">
          <el-input v-model="form.name" placeholder="输入校区名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { campusesApi } from '@/api/campuses'

interface CampusRow {
  id: string
  name: string
  status: string
  [key: string]: unknown
}

const campuses = ref<CampusRow[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const form = reactive({ id: '', name: '' })

async function fetchCampuses() {
  loading.value = true
  try {
    const { data } = await campusesApi.list()
    campuses.value = data.data as CampusRow[]
  } catch {
    ElMessage.error('获取校区列表失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  form.id = ''
  form.name = ''
  showDialog.value = true
}

function openEditDialog(row: CampusRow) {
  isEditing.value = true
  editingId.value = row.id
  form.id = row.id
  form.name = row.name
  showDialog.value = true
}

async function handleSubmit() {
  try {
    if (isEditing.value) {
      await campusesApi.update(editingId.value, form.name)
      ElMessage.success('更新成功')
    } else {
      await campusesApi.create(form.id, form.name)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    await fetchCampuses()
  } catch {
    ElMessage.error(isEditing.value ? '更新失败' : '创建失败')
  }
}

async function handleDelete(campus: CampusRow) {
  try {
    await ElMessageBox.confirm('确认删除该校区？', '提示', { type: 'warning' })
    await campusesApi.remove(campus.id)
    ElMessage.success('删除成功')
    await fetchCampuses()
  } catch {
    // cancelled or error
  }
}

onMounted(fetchCampuses)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.table-card {
  border-radius: 8px;
}

.btn-icon {
  margin-right: 4px;
}
</style>
