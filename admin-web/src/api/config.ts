import client from './client'

export const configApi = {
  list() {
    return client.get('/config')
  },
  update(data: { scope: string; scope_id: string | null; key: string; value: unknown }) {
    return client.put('/config', data)
  },
}
