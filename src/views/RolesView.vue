<template>
  <div>
    <h2>角色管理</h2>
    <el-button type="primary" style="margin-bottom: 16px" @click="showDialog()">新建角色</el-button>
    <el-table :data="roles" v-loading="loading">
      <el-table-column prop="id" label="ID" />
      <el-table-column prop="name" label="角色名" />
      <el-table-column prop="permissions" label="权限">
        <template #default="{ row }">
          <el-tag v-for="p in (row.permissions || [])" :key="p" size="small" style="margin-right: 4px">{{ p }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑角色' : '新建角色'" width="500px">
      <el-form label-width="80px">
        <el-form-item label="角色名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="权限">
          <el-select v-model="form.permissions" multiple style="width: 100%">
            <el-option v-for="p in availablePermissions" :key="p" :label="p" :value="p" />
          </el-select>
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
import rolesApi from '@/api/roles'

const loading = ref(false)
const roles = ref<any[]>([])
const dialogVisible = ref(false)
const editing = ref<any>(null)
const form = ref({ name: '', permissions: [] as string[] })
const availablePermissions = [
  'read:users', 'write:users',
  'read:campuses', 'write:campuses',
  'read:analytics', 'read:audit',
  'write:roles', 'write:apps', 'write:config',
]

async function fetchRoles() {
  loading.value = true
  try {
    const { data } = await rolesApi.list()
    roles.value = data.data?.items || data.data || []
  } catch {
    roles.value = []
  } finally {
    loading.value = false
  }
}

function showDialog(role?: any) {
  editing.value = role || null
  form.value = role
    ? { name: role.name, permissions: [...(role.permissions || [])] }
    : { name: '', permissions: [] }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    if (editing.value) {
      await rolesApi.update(editing.value.id, form.value)
    } else {
      await rolesApi.create(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchRoles()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function handleDelete(id: string) {
  try {
    await rolesApi.delete(id)
    ElMessage.success('删除成功')
    await fetchRoles()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(fetchRoles)
</script>
