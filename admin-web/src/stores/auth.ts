import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: string
  name: string
  tenant_id: string
  roles?: string[]
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => user.value !== null)

  const roles = computed(() => user.value?.roles ?? [])

  const highestRole = computed(() => {
    const priority = ['super_admin', 'admin', 'teacher']
    for (const r of priority) {
      if (roles.value.includes(r)) return r
    }
    return roles.value[0] ?? ''
  })

  function setUser(u: User) {
    user.value = u
  }

  function logout() {
    user.value = null
  }

  return { user, isAuthenticated, roles, highestRole, setUser, logout }
})
