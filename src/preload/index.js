import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'
// preload.js

// 暴露 electronAPI 对象
contextBridge.exposeInMainWorld('electronAPI', {
  fetchData: (url) => ipcRenderer.invoke('fetch-data', url)
})

// 定义系统 API
const api = {
  // 检查API服务器状态
  checkApiStatus: () => ipcRenderer.invoke('check-api-status'),

  // 向主进程发送消息
  send: (channel, data) => {
    // 白名单频道
    const validChannels = ['toMain', 'api-request']
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data)
    }
  },

  // 从主进程接收消息
  receive: (channel, func) => {
    // 白名单频道
    const validChannels = ['fromMain', 'api-response']
    if (validChannels.includes(channel)) {
      // 删除旧的监听器以避免重复
      ipcRenderer.removeAllListeners(channel)
      // 添加新的监听器
      ipcRenderer.on(channel, (_, ...args) => func(...args))
    }
  },

  // 系统状态相关 API
  getSystemStatus: () => ipcRenderer.invoke('api-call', { endpoint: '/status', method: 'get' }),
  initializeSystem: (config) =>
    ipcRenderer.invoke('api-call', { endpoint: '/initialize', method: 'post', data: config }),

  // 灯光控制 API
  openLight: () => ipcRenderer.invoke('api-call', { endpoint: '/light/open', method: 'post' }),
  closeLight: () => ipcRenderer.invoke('api-call', { endpoint: '/light/close', method: 'post' }),

  // 流程控制 API
  startProcess: (config) =>
    ipcRenderer.invoke('api-call', { endpoint: '/start', method: 'post', data: config }),
  stopProcess: () => ipcRenderer.invoke('api-call', { endpoint: '/stop', method: 'post' }),

  // 清砂相关 API
  cleanSand: (options) =>
    ipcRenderer.invoke('api-call', { endpoint: '/clean', method: 'post', data: options }),
  getCleanStatus: () =>
    ipcRenderer.invoke('api-call', { endpoint: '/clean/status', method: 'get' }),
  stopCleanProcess: () =>
    ipcRenderer.invoke('api-call', { endpoint: '/clean/stop', method: 'post' }),

  // 电子秤相关 API
  getScalePorts: () => ipcRenderer.invoke('api-call', { endpoint: '/scale/ports', method: 'get' }),
  getScaleStatus: () =>
    ipcRenderer.invoke('api-call', { endpoint: '/scale/status', method: 'get' }),
  connectScale: (port) =>
    ipcRenderer.invoke('api-call', { endpoint: `/scale/connect/${port}`, method: 'post' }),
  disconnectScale: () =>
    ipcRenderer.invoke('api-call', { endpoint: '/scale/disconnect', method: 'post' }),
  calibrateZero: () =>
    ipcRenderer.invoke('api-call', { endpoint: '/scale/calibrate/zero', method: 'post' }),
  calibrateGain: (calibrationWeight, slaveAddress = 1) =>
    ipcRenderer.invoke('api-call', {
      endpoint: '/scale/calibrate/gain',
      method: 'post',
      data: { calibration_weight: calibrationWeight, slave_address: slaveAddress }
    }),
  getWeight: () => ipcRenderer.invoke('api-call', { endpoint: '/scale/weight', method: 'get' }),

  // 图片相关 API
  getDirectoryImages: (directory) =>
    ipcRenderer.invoke('api-call', {
      endpoint: '/images/list',
      method: 'get',
      params: { directory }
    }),
  getImageUrl: (imagePath) => ipcRenderer.invoke('get-image-url', { imagePath }),

  // 讯飞星火大模型 API
  chatWithXfyun: (userMessage) => ipcRenderer.invoke('chat-with-xfyun', { userMessage }),

  // 测试服务器连接
  testServerConnection: () => ipcRenderer.invoke('test-server-connection')
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  window.electron = electronAPI
  window.api = api
}
