import client from './client'

export const campusesApi = {
  list(page = 1, size = 20) {
    return client.get('/campuses', { params: { page, size } })
  },
  create(campusId: string, name: string) {
    return client.post('/campuses', null, { params: { campus_id: campusId, name } })
  },
  update(id: string, name?: string) {
    return client.put(`/campuses/${id}`, null, { params: { name } })
  },
  remove(id: string) {
    return client.delete(`/campuses/${id}`)
  },
}
