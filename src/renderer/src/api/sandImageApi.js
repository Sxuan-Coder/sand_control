import axios from 'axios'

// 设置基础URL
const baseURL = 'http://localhost:8000'

/**
 * 获取沙粒分析结果
 * @returns {Promise} 返回分析结果数据
 */
export const getProcessingResults = async () => {
  try {
    const response = await axios.get(`${baseURL}/results`)
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      throw new Error('未找到沙粒分析结果数据')
    }
    throw new Error('获取沙粒分析结果失败: ' + (error.response?.data?.error || error.message))
  }
}

/**
 * 获取沙粒图片URL
 * @param {string} filename - 图片文件名
 * @returns {string} 图片的完整URL
 */
export const getSandImageUrl = (filename) => {
  // 统一路径分隔符为正斜杠，适合URL格式
  const normalizedFilename = filename.replace(/\\/g, '/');
  // 使用正确的API端点 /images/file?path= 而不是 /images/
  return `${baseURL}/images/file?path=${encodeURIComponent(normalizedFilename)}`
}

export default {
  getProcessingResults,
  getSandImageUrl
}