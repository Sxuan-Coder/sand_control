import axios from 'axios'

// 设置基础URL
const baseURL = 'http://localhost:8000'

/**
 * 获取沙粒图像处理结果
 * @returns {Promise<Object>} 处理结果数据
 */
export const getProcessingResults = async () => {
  try {
    console.log('正在获取沙粒分析结果...');
    const response = await axios.get(`${baseURL}/results`);
    
    if (response.data) {
      console.log('成功获取沙粒分析结果:', response.data);
      return response.data;
    } else {
      throw new Error('无效的处理结果数据');
    }
  } catch (error) {
    console.error('获取沙粒分析结果失败:', error);
    throw error;
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