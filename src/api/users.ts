import client from './client'

export const usersApi = {
  list(page = 1, size = 20) {
    return client.get('/users', { params: { page, size } })
  },
  get(id: string) {
    return client.get(`/users/${id}`)
  },
  updateStatus(id: string, status: string) {
    return client.put(`/users/${id}/status`, null, { params: { status } })
  },
  assignRole(id: string, roleId: string, scopeId = '*') {
    return client.post(`/users/${id}/roles`, null, { params: { role_id: roleId, scope_id: scopeId } })
  },
}
