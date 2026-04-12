import client from './client'

export const appsApi = {
  list() {
    return client.get('/apps')
  },
  register(data: { app_id: string; name: string; app_key: string }) {
    return client.post('/apps', data)
  },
  toggleStatus(id: string, status: string) {
    return client.put(`/apps/${id}/status`, { status })
  },
}
