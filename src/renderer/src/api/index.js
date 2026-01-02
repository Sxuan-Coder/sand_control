// 使用HTTP API通信代替IPC通信
// 所有API调用直接通过axios访问HTTP后端

// 导入axios
import axios from 'axios'

// 导入沙粒图像处理API
import sandImageApi from './sandImageApi'

// 导入讯飞星火API
import { chatWithXfyun } from './xfyunApi'

// 获取API基础URL，默认为本地开发环境
const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:8000'
  : window.location.origin // 生产环境使用当前域名

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 测试服务器连接
export const testServerConnection = async () => {
  try {
    const response = await api.get('/hello')
    return {
      success: true,
      message: '服务器连接成功',
      data: response.data
    }
  } catch (error) {
    return {
      success: false,
      message: '服务器连接失败: ' + (error.message || '未知错误'),
      error
    }
  }
}

// 系统状态相关 API
export const getSystemStatus = async () => {
  try {
    const response = await api.get('/status')
    return response.data
  } catch (error) {
    console.error('获取系统状态失败:', error)
    throw error
  }
}

// 获取系统监控数据(CPU、内存、网络延迟)
export const getSystemMonitor = async () => {
  try {
    const response = await api.get('/system/monitor')
    return response.data
  } catch (error) {
    console.error('获取系统监控数据失败:', error)
    throw error
  }
}

export const initializeSystem = async (config) => {
  try {
    const response = await api.post('/initialize', config || {})
    return response.data
  } catch (error) {
    console.error('初始化系统失败:', error)
    throw error
  }
}

// 灯光控制 API
export const openLight = async () => {
  try {
    const response = await api.post('/light/open')
    return response.data
  } catch (error) {
    console.error('打开灯光失败:', error)
    throw error
  }
}

export const closeLight = async () => {
  try {
    const response = await api.post('/light/close')
    return response.data
  } catch (error) {
    console.error('关闭灯光失败:', error)
    throw error
  }
}

// 流程控制 API
export const startProcess = async (config) => {
  try {
    const response = await api.post('/start', config)
    return response.data
  } catch (error) {
    console.error('启动流程失败:', error)
    throw error
  }
}

export const stopProcess = async () => {
  try {
    const response = await api.post('/stop')
    return response.data
  } catch (error) {
    console.error('停止流程失败:', error)
    throw error
  }
}

// 清砂控制 API
export const cleanSand = async (config) => {
  try {
    const response = await api.post('/clean', config)
    return response.data
  } catch (error) {
    console.error('清砂操作失败:', error)
    throw error
  }
}

export const getCleanStatus = async () => {
  try {
    const response = await api.get('/clean/status')
    return response.data
  } catch (error) {
    console.error('获取清砂状态失败:', error)
    throw error
  }
}

export const stopCleanProcess = async () => {
  try {
    const response = await api.post('/clean/stop')
    return response.data
  } catch (error) {
    console.error('停止清砂操作失败:', error)
    throw error
  }
}

// 电子秤 API
export const getScalePorts = async () => {
  try {
    const response = await api.get('/scale/ports')
    return response.data
  } catch (error) {
    console.error('获取串口列表失败:', error)
    throw error
  }
}

export const getScaleStatus = async () => {
  try {
    const response = await api.get('/scale/status')
    return response.data
  } catch (error) {
    console.error('获取电子秤状态失败:', error)
    throw error
  }
}

export const connectScale = async (port) => {
  try {
    const response = await api.post(`/scale/connect/${port}`)
    return response.data
  } catch (error) {
    console.error('连接电子秤失败:', error)
    throw error
  }
}

export const disconnectScale = async () => {
  try {
    const response = await api.post('/scale/disconnect')
    return response.data
  } catch (error) {
    console.error('断开电子秤连接失败:', error)
    throw error
  }
}

export const calibrateZero = async () => {
  try {
    const response = await api.post('/scale/calibrate/zero')
    return response.data
  } catch (error) {
    console.error('零点校准失败:', error)
    throw error
  }
}

export const calibrateGain = async (calibrationWeight, slaveAddress = 1) => {
  try {
    const response = await api.post('/scale/calibrate/gain', {
      calibration_weight: calibrationWeight,
      slave_address: slaveAddress
    })
    return response.data
  } catch (error) {
    console.error('增益校准失败:', error)
    throw error
  }
}

export const getWeight = async () => {
  try {
    const response = await api.get('/scale/weight')
    return response.data
  } catch (error) {
    console.error('获取重量失败:', error)
    throw error
  }
}

// 图片相关 API
export const getDirectoryImages = async (directory) => {
  try {
    const response = await api.get('/images/list', {
      params: { directory }
    })
    return response.data
  } catch (error) {
    console.error('获取目录图片失败:', error)
    throw error
  }
}

export const getImageUrl = (imagePath) => {
  if (!imagePath) {
    console.warn('getImageUrl: imagePath is empty');
    return '';
  }

  try {
    // 统一路径分隔符为正斜杠，适合URL格式
    const normalizedPath = imagePath.replace(/\\/g, '/');

    // 去除路径中的多余斜杠和点
    const cleanPath = normalizedPath
      .replace(/\/+/g, '/') // 多个斜杠替换为单个
      .replace(/\/\.\//g, '/') // 移除 /./
      .replace(/^\.\/?/, ''); // 移除开头的 ./ 或 .

    const url = `${API_BASE_URL}/images/file?path=${encodeURIComponent(cleanPath)}`;

    // 只在开发模式下输出调试信息
    if (process.env.NODE_ENV === 'development') {
      // console.log('构建图片URL:', {
      //   originalPath: imagePath,
      //   normalizedPath: cleanPath,
      //   url
      // });
    }

    return url;
  } catch (error) {
    console.error('生成图片URL时出错:', error);
    return '';
  }
}

export const uploadAndProcessImages = async (files, imageType, sampleIndex, saveResults = true, outputPath = null) => {
  return sandImageApi.uploadAndProcessImages(files, imageType, sampleIndex, saveResults, outputPath)
}

export const getTaskStatus = async (taskId) => {
  return sandImageApi.getTaskStatus(taskId)
}

export const processCustomImages = async () => {
  return sandImageApi.processCustomImages()
}

export const getProcessingResults = async () => {
  return sandImageApi.getProcessingResults()
}

export const getSandImageUrl = (imageName) => {
  return sandImageApi.getSandImageUrl(imageName)
}

export const analyzeSandData = async (params) => {
  return sandImageApi.analyzeSandData(params)
}

// 只导出sandImageApi，避免重复导出
export {
  sandImageApi
}

// 兼容性导出一个API对象
const API = {
  getSystemStatus,
  getSystemMonitor,
  chatWithXfyun,
  testServerConnection,
  initializeSystem,
  openLight,
  closeLight,
  startProcess,
  stopProcess,
  cleanSand,
  getCleanStatus,
  stopCleanProcess,
  getScalePorts,
  connectScale,
  disconnectScale,
  calibrateZero,
  calibrateGain,
  getWeight,
  getDirectoryImages,
  getImageUrl,
  uploadAndProcessImages,
  getTaskStatus,
  processCustomImages,
  getProcessingResults,
  getSandImageUrl,
  analyzeSandData,
  sandImageApi
}

export default API
