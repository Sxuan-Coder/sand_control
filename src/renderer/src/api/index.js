import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('响应错误:', error)
    return Promise.reject(error)
  }
)

export const getSystemStatus = () => {
  return api.get('/status')
}

export const initializeSystem = (config) => {
  return api.post('/initialize', config)
}

export const openLight = () => {
  return api.post('/light/open')
}

export const closeLight = () => {
  return api.post('/light/close')
}

export const startProcess = (config) => {
  return api.post('/start', config)
}

export const stopProcess = () => {
  return api.post('/stop')
}

export const cleanSand = (options = {}) => {
  // 可以传入选项如：循环次数、是否测试模式等
  return api.post('/clean', options)
}

export const getCleanStatus = () => {
  return api.get('/clean/status')
}

export const stopCleanProcess = () => {
  return api.post('/clean/stop')
}

// 电子秤相关API
export const getScalePorts = () => {
  return api.get('/scale/ports')
}

export const getScaleStatus = () => {
  return api.get('/scale/status')
}

export const connectScale = (port) => {
  return api.post(`/scale/connect/${port}`)
}

export const disconnectScale = () => {
  return api.post('/scale/disconnect')
}

export const calibrateZero = () => {
  return api.post('/scale/calibrate/zero')
}

export const calibrateGain = (calibrationWeight, slaveAddress = 1) => {
  return api.post('/scale/calibrate/gain', {
    calibration_weight: calibrationWeight,
    slave_address: slaveAddress
  })
}

export const getWeight = () => {
  return api.get('/scale/weight')
}

// 获取指定目录下的图片列表
export const getDirectoryImages = (directory) => {
  return api.get('/images/list', { params: { directory } })
}

// 获取图片URL
export const getImageUrl = (imagePath) => {
  return `${api.defaults.baseURL}/images/file?path=${encodeURIComponent(imagePath)}`
}

// 讯飞星火大模型API配置
const XFYUN_API_URL = '/xfyun-api/v1/chat/completions' // 使用代理路径
const AUTH_TOKEN = 'pFKHvqJefKoFYrsZVvqJ:QneWSeXeqoeefFUBsAcV'

// 调用讯飞星火大模型API
export const chatWithXfyun = async (userMessage) => {
  try {
    // 构建请求体
    const requestBody = {
      model: '4.0Ultra',
      messages: [
        {
          role: 'user',
          content: userMessage
        }
      ],
      stream: false
    }

    // 请求头设置
    const headers = {
      Authorization: `Bearer ${AUTH_TOKEN}`,
      'Content-Type': 'application/json'
    }

    // 发送POST请求
    const response = await axios.post(XFYUN_API_URL, requestBody, { headers })

    // 返回响应内容
    if (response.data && response.data.choices && response.data.choices.length > 0) {
      return response.data.choices[0].message.content
    } else {
      throw new Error('无效的API响应格式')
    }
  } catch (error) {
    console.error('调用讯飞星火大模型API失败:', error)
    throw error
  }
}

export default api
