<template>
  <div>
    <h2>用户管理</h2>
    <div style="display: flex; gap: 12px; margin-bottom: 16px">
      <el-input v-model="search" placeholder="搜索用户名" clearable style="width: 240px" @clear="fetchUsers" @keyup.enter="fetchUsers" />
      <el-button type="primary" @click="fetchUsers">搜索</el-button>
    </div>
    <el-table :data="filteredUsers" v-loading="loading">
      <el-table-column prop="id" label="ID" />
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="status" label="状态" />
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button
            size="small"
            :type="row.status === 'active' ? 'danger' : 'success'"
            @click="toggleStatus(row)"
          >
            {{ row.status === 'active' ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" @click="openRoleDialog(row)">分配角色</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="page"
      :page-size="20"
      :total="total"
      @current-change="fetchUsers"
      style="margin-top: 16px"
    />

    <el-dialog v-model="showRoleDialog" title="分配角色" width="400px">
      <el-form>
        <el-form-item label="用户">
          <span>{{ currentUser?.name }}</span>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="selectedRole" placeholder="选择角色">
            <el-option label="超级管理员" value="super_admin" />
            <el-option label="机构管理员" value="org_admin" />
            <el-option label="校区管理员" value="campus_admin" />
            <el-option label="教师" value="teacher" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRoleDialog = false">取消</el-button>
        <el-button type="primary" @click="assignRole">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { usersApi } from '@/api/users'

interface UserRow {
  id: string
  name: string
  status: string
  campus_id?: string
}

const users = ref<UserRow[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const search = ref('')
const showRoleDialog = ref(false)
const currentUser = ref<UserRow | null>(null)
const selectedRole = ref('')

const filteredUsers = computed(() => {
  if (!search.value) return users.value
  return users.value.filter(u => u.name.includes(search.value))
})

async function fetchUsers() {
  loading.value = true
  try {
    const { data } = await usersApi.list(page.value)
    users.value = data.data
    total.value = data.total ?? data.data.length
  } catch {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function toggleStatus(user: UserRow) {
  const newStatus = user.status === 'active' ? 'disabled' : 'active'
  try {
    await usersApi.updateStatus(user.id, newStatus)
    user.status = newStatus
    ElMessage.success('状态已更新')
  } catch {
    ElMessage.error('更新失败')
  }
}

function openRoleDialog(user: UserRow) {
  currentUser.value = user
  selectedRole.value = ''
  showRoleDialog.value = true
}

async function assignRole() {
  if (!currentUser.value || !selectedRole.value) return
  try {
    await usersApi.assignRole(currentUser.value.id, selectedRole.value)
    ElMessage.success('角色已分配')
    showRoleDialog.value = false
  } catch {
    ElMessage.error('分配角色失败')
  }
}

onMounted(fetchUsers)
</script>
