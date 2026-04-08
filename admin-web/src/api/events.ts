import client from './client'

export const eventsApi = {
  batchReport(events: Record<string, unknown>[]) {
    return client.post('/events/batch', events)
  },
}
