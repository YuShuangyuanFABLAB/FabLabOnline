import client from './client'

export const analyticsApi = {
  getDashboard(days = 7) {
    return client.get('/analytics/dashboard', { params: { days } })
  },
  getUsage(start: string, end: string) {
    return client.get('/analytics/usage', { params: { start, end } })
  },
}
