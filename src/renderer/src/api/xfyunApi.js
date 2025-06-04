import axios from 'axios'

// 讯飞星火大模型API调用配置
const XFYUN_API_URL = 'https://spark-api-open.xf-yun.com/v1/chat/completions';
const AUTH_TOKEN = 'pFKHvqJefKoFYrsZVvqJ:QneWSeXeqoeefFUBsAcV';

/**
 * 调用讯飞星火大模型API
 * @param {Object} data - 要发送给AI的数据
 * @returns {Promise<Object>} AI的响应
 */
export const chatWithXfyun = async (data) => {
  try {
    const { fineModulus, sandType, midSizeContent, fineContent, volumeDistribution } = data;
    
    // 构建提示词
    const prompt = `
      我是一个专业的机制砂分析专家。请根据以下数据分析机制砂的特性和提出建议：
      
      1. 细度模数：${fineModulus}
      2. 砂的类型：${sandType}
      3. 中间粒级(0.3~2.36mm)含量：${midSizeContent}%
      4. 细粉含量(<0.075mm)：${fineContent}%
      5. 各粒径体积占比：${JSON.stringify(volumeDistribution)}
      
      请提供以下分析：
      1. 分析结论（包括级配特征评价）
      2. 优化建议（至少3条）
      3. 应用适宜性分析
      
      请以JSON格式返回，包含conclusion（结论）、optimizationSuggestions（优化建议数组）和applicationSuitability（应用适宜性）字段。
    `;

    console.log('发送到讯飞API的提示词:', prompt);

    // 调用API
    const response = await axios.post(XFYUN_API_URL, {
      messages: [{ role: 'user', content: prompt }]
    }, {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      }
    });

    console.log('讯飞API原始响应:', response.data);

    if (response.data && response.data.choices && response.data.choices[0]) {
      // 解析API返回的JSON响应
      const aiResponse = JSON.parse(response.data.choices[0].message.content);
      return aiResponse;
    } else {
      throw new Error('无效的API响应格式');
    }
  } catch (error) {
    console.error('调用讯飞星火API失败:', error);
    throw error;
  }
};

// 导出默认对象
export default chatWithXfyun;