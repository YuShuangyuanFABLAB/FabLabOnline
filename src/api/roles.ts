import client from './client'

export default {
  list() {
    return client.get('/roles')
  },
  create(data: { name: string; permissions: string[] }) {
    return client.post('/roles', data)
  },
  update(id: string, data: { name?: string; permissions?: string[] }) {
    return client.put(`/roles/${id}`, data)
  },
  delete(id: string) {
    return client.delete(`/roles/${id}`)
  },
}
