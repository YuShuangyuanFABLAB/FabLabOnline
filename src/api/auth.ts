import client from './client'

export const authApi = {
  getQrCode() {
    return client.post('/auth/qrcode')
  },
  getStatus(state: string) {
    return client.get(`/auth/qrcode/${state}/status`)
  },
  heartbeat() {
    return client.post('/auth/heartbeat')
  },
  logout() {
    return client.post('/auth/logout')
  },
}
