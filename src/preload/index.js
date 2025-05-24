import { contextBridge } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// 简化的系统 API 定义
const api = {
  // 定义版本信息
  version: '1.0.0',
  
  // 定义应用运行环境
  env: process.env.NODE_ENV,
  
  // 定义基础 API URL
  baseUrl: process.env.NODE_ENV === 'development' 
    ? 'http://localhost:8000'
    : 'http://127.0.0.1:8000'
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
