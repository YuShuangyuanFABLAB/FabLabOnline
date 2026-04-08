import { defineStore } from 'pinia'
import { ref } from 'vue'

interface AppInfo {
  id: string
  name: string
  app_key: string
  status: string
}

export const useAppStore = defineStore('app', () => {
  const apps = ref<AppInfo[]>([])

  function setApps(list: AppInfo[]) {
    apps.value = list
  }

  function clearApps() {
    apps.value = []
  }

  return { apps, setApps, clearApps }
})
