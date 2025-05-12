// 使用 IPC 通信代替直接的 axios 请求
// 所有的 API 调用都通过主进程处理

// 系统状态相关 API
export const getSystemStatus = async () => {
  return window.api.getSystemStatus()
}

export const initializeSystem = async (config) => {
  return window.api.initializeSystem(config)
}

// 灯光控制 API
export const openLight = async () => {
  return window.api.openLight()
}

export const closeLight = async () => {
  return window.api.closeLight()
}

// 流程控制 API
export const startProcess = async (config) => {
  return window.api.startProcess(config)
}

export const stopProcess = async () => {
  return window.api.stopProcess()
}

// 清砂相关 API
export const cleanSand = async (options = {}) => {
  return window.api.cleanSand(options)
}

export const getCleanStatus = async () => {
  return window.api.getCleanStatus()
}

export const stopCleanProcess = async () => {
  return window.api.stopCleanProcess()
}

// 电子秤相关 API
export const getScalePorts = async () => {
  return window.api.getScalePorts()
}

export const getScaleStatus = async () => {
  return window.api.getScaleStatus()
}

export const connectScale = async (port) => {
  return window.api.connectScale(port)
}

export const disconnectScale = async () => {
  return window.api.disconnectScale()
}

export const calibrateZero = async () => {
  return window.api.calibrateZero()
}

export const calibrateGain = async (calibrationWeight, slaveAddress = 1) => {
  return window.api.calibrateGain(calibrationWeight, slaveAddress)
}

export const getWeight = async () => {
  return window.api.getWeight()
}

// 图片相关 API
export const getDirectoryImages = async (directory) => {
  return window.api.getDirectoryImages(directory)
}

// 获取图片URL
export const getImageUrl = async (imagePath) => {
  return window.api.getImageUrl(imagePath)
}

// 讯飞星火大模型 API
export const chatWithXfyun = async (userMessage) => {
  try {
    const result = await window.api.chatWithXfyun(userMessage)
    if (result.success) {
      return result.content
    } else {
      throw new Error(result.error || '调用星火大模型失败')
    }
  } catch (error) {
    console.error('调用讯飞星火大模型API失败:', error)
    throw error
  }
}

// 测试服务器连接状态
export const testServerConnection = async () => {
  return window.api.testServerConnection()
}

// 为了兼容现有代码，创建一个虚拟的 api 对象
const api = {
  defaults: {
    baseURL: 'http://127.0.0.1:8000'
  }
}

export default api
