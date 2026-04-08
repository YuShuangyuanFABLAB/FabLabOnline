<template>
  <div>
    <h2>校区管理</h2>
    <el-button type="primary" style="margin-bottom: 16px" @click="openCreateDialog">新增校区</el-button>
    <el-table :data="campuses" v-loading="loading">
      <el-table-column prop="id" label="ID" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="isEditing ? '编辑校区' : '新增校区'" width="400px">
      <el-form>
        <el-form-item v-if="!isEditing" label="校区ID">
          <el-input v-model="form.id" />
        </el-form-item>
        <el-form-item label="校区名称">
          <el-input v-model="form.name" />
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
import { campusesApi } from '@/api/campuses'

const campuses = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const form = reactive({ id: '', name: '' })

async function fetchCampuses() {
  loading.value = true
  try {
    const { data } = await campusesApi.list()
    campuses.value = data.data
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

function openEditDialog(row: Record<string, unknown>) {
  isEditing.value = true
  editingId.value = row.id as string
  form.id = row.id as string
  form.name = row.name as string
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

async function handleDelete(campus: Record<string, unknown>) {
  try {
    await ElMessageBox.confirm('确认删除该校区？', '提示')
    await campusesApi.remove(campus.id as string)
    ElMessage.success('删除成功')
    await fetchCampuses()
  } catch {
    // cancelled or error
  }
}

onMounted(fetchCampuses)
</script>
