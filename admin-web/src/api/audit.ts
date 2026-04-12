import client from './client'

export const auditApi = {
  list(page = 1, size = 20) {
    return client.get('/audit/logs', { params: { page, size } })
  },
}
