import client from './client'

export const authApi = {
  getQrCode() {
    return client.post('/auth/qrcode')
  },
  getStatus(state: string) {
    return client.get(`/auth/qrcode/${state}/status`)
  },
  login(userId: string, password: string) {
    return client.post('/auth/login', { user_id: userId, password })
  },
  heartbeat() {
    return client.post('/auth/heartbeat')
  },
  logout() {
    return client.post('/auth/logout')
  },
  changePassword(oldPassword: string, newPassword: string) {
    return client.put('/auth/password', { old_password: oldPassword, new_password: newPassword })
  },
}
