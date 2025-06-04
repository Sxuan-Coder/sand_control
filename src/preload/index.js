import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'
import { join } from 'path'

// 简化的系统 API 定义
const api = {
  // 定义版本信息
  version: '1.0.0',
  
  // 定义应用运行环境
  env: process.env.NODE_ENV,
  
  // 定义基础 API URL
  baseUrl: process.env.NODE_ENV === 'development' 
    ? 'http://localhost:8000'
    : 'http://127.0.0.1:8000',

  // 添加ipcRenderer API
  ipcRenderer: {
    invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args)
  },
  // 添加path.join功能
  path: {
    join: (...args) => join(...args)
  }
}

// 使用contextBridge暴露API
try {
  contextBridge.exposeInMainWorld('electron', electronAPI)
  contextBridge.exposeInMainWorld('api', {
    ipcRenderer: {
      invoke: (...args) => ipcRenderer.invoke(...args)
    },
    path: {
      join: (...args) => join(...args)
    }
  })
  console.log('成功暴露API到渲染进程')
} catch (error) {
  console.error('暴露API失败:', error)
}
