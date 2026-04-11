<template>
  <div class="roles-view">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button type="primary" @click="showDialog()">
        <el-icon class="btn-icon"><Plus /></el-icon>
        新建角色
      </el-button>
    </div>

    <!-- Table -->
    <el-card shadow="never" class="table-card">
      <el-table :data="roles" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="160" />
        <el-table-column prop="name" label="角色名" width="160" />
        <el-table-column label="权限">
          <template #default="{ row }">
            <el-tag
              v-for="p in (row.permissions || [])"
              :key="p"
              size="small"
              effect="plain"
              class="perm-tag"
            >
              {{ p }}
            </el-tag>
            <span v-if="!row.permissions?.length" class="text-muted">无权限</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" plain @click="showDialog(row)">
              <el-icon class="btn-icon"><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(row.id)">
              <el-icon class="btn-icon"><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Dialog -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑角色' : '新建角色'" width="520px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="角色名">
          <el-input v-model="form.name" placeholder="输入角色名" />
        </el-form-item>
        <el-form-item label="权限">
          <el-select v-model="form.permissions" multiple style="width: 100%" placeholder="选择权限">
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
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import rolesApi from '@/api/roles'

interface RoleRow {
  id: string
  name: string
  permissions: string[]
  [key: string]: unknown
}

const loading = ref(false)
const roles = ref<RoleRow[]>([])
const dialogVisible = ref(false)
const editing = ref<RoleRow | null>(null)
const form = ref({ name: '', permissions: [] as string[] })
const availablePermissions = [
  'user:read', 'user:create', 'user:update', 'user:delete',
  'role:read', 'role:update',
  'campus:read', 'campus:create', 'campus:update',
  'app:read', 'app:update',
  'config:read', 'config:update',
  'audit:read', 'analytics:read',
  'event:read', 'event:create',
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

function showDialog(role?: RoleRow) {
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
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '保存失败')
  }
}

async function handleDelete(id: string) {
  try {
    await rolesApi.delete(id)
    ElMessage.success('删除成功')
    await fetchRoles()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

onMounted(fetchRoles)
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

.perm-tag {
  margin: 2px 4px 2px 0;
}

.text-muted {
  color: var(--fab-text-secondary);
  font-size: 13px;
}
</style>
