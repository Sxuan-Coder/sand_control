// 讯飞星火大模型 API
export const chatWithXfyun = async (messages) => {
  try {
    return await window.api.chatWithXfyun(messages)
  } catch (error) {
    console.error('讯飞星火API调用失败:', error)
    throw error
  }
}
