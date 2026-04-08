import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts unauthenticated', async () => {
    const { useAuthStore } = await import('@/stores/auth')
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
  })

  it('sets user on login', async () => {
    const { useAuthStore } = await import('@/stores/auth')
    const store = useAuthStore()
    store.setUser({ id: 'u1', name: 'Admin', tenant_id: 't1' })
    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.name).toBe('Admin')
  })

  it('clears user on logout', async () => {
    const { useAuthStore } = await import('@/stores/auth')
    const store = useAuthStore()
    store.setUser({ id: 'u1', name: 'Admin', tenant_id: 't1' })
    store.logout()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
  })
})
