import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('../components/Layout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue'),
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('../views/UsersView.vue'),
        },
        {
          path: 'campuses',
          name: 'campuses',
          component: () => import('../views/CampusesView.vue'),
        },
        {
          path: 'analytics',
          name: 'analytics',
          component: () => import('../views/AnalyticsView.vue'),
        },
        {
          path: 'audit',
          name: 'audit',
          component: () => import('../views/AuditView.vue'),
        },
        {
          path: 'roles',
          name: 'roles',
          component: () => import('../views/RolesView.vue'),
        },
        {
          path: 'apps',
          name: 'apps',
          component: () => import('../views/AppsView.vue'),
        },
        {
          path: 'config',
          name: 'config',
          component: () => import('../views/ConfigView.vue'),
        },
        {
          path: 'password',
          name: 'password',
          component: () => import('../views/PasswordView.vue'),
        },
      ],
    },
  ],
})

// Route guard — check auth via heartbeat (cookie-based) + role-based access
const roleRequired: Record<string, string[]> = {
  '/roles': ['super_admin'],
  '/users': ['super_admin', 'admin'],
  '/campuses': ['super_admin', 'admin'],
  '/config': ['super_admin'],
  '/apps': ['super_admin'],
}

router.beforeEach(async (to) => {
  if (to.path === '/login') return true

  const authStore = useAuthStore()

  // Already have user info — check role and allow
  if (authStore.user) {
    const required = roleRequired[to.path]
    if (required && !required.some(r => authStore.roles.includes(r))) {
      return '/'
    }
    return true
  }

  // Try to restore user info via heartbeat (uses HttpOnly cookie)
  try {
    const { data } = await authApi.heartbeat()
    if (data.data?.alive && data.data?.user_id) {
      // Restore user from heartbeat response
      const hbData = data.data
      authStore.setUser({
        id: hbData.user_id,
        name: hbData.user_name || hbData.user_id,
        tenant_id: hbData.tenant_id || 'default',
        roles: hbData.roles || [],
      })
      // Role-based route guard (UX only — backend enforces permissions)
      const required = roleRequired[to.path]
      if (required && !required.some(r => authStore.roles.includes(r))) {
        return '/'
      }
      return true
    }
  } catch {
    // heartbeat failed — not authenticated
  }

  return '/login'
})

export default router
