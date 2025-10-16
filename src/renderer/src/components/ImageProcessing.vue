<template>
  <div class="image-processing">
  
    <!-- 主内容区 -->
    <div class="processing-content">
      <!-- 左侧：图像对比展示 -->
      <div class="image-comparison-section">
        <div class="section-title">
          <h3>图像处理对比</h3>
          <el-select v-model="selectedGroup" placeholder="选择组别" class="group-selector">
            <el-option 
              v-for="group in availableGroups" 
              :key="group" 
              :label="`第${group}组`" 
              :value="group" 
            />
          </el-select>
        </div>

        <!-- 全局图像对比区域 -->
        <div class="view-type-label">全局视图</div>
        <div class="comparison-container">
          <div class="image-box">
            <div class="image-label">原始图像</div>
            <div class="image-placeholder" v-if="globalImages.original">
              <img :src="globalImages.original" alt="原始图像" class="result-image" />
            </div>
            <div class="image-placeholder" v-else>
              <el-icon class="placeholder-icon"><Camera /></el-icon>
              <p>暂无图像</p>
            </div>
            <div class="image-info">
              <span>类型: 全局视图</span>
              <span>组别: 第{{ selectedGroup }}组</span>
            </div>
          </div>

          <div class="arrow-divider">
            <el-icon class="arrow-icon"><Right /></el-icon>
          </div>

          <div class="image-box processing">
            <div class="image-label processing-label">
              <span>图像分割</span>
            </div>
            <div class="image-placeholder" v-if="globalImages.segmented">
              <img :src="globalImages.segmented" alt="分割图像" class="result-image" />
            </div>
            <div class="image-placeholder processing-bg" v-else>
              <el-icon class="placeholder-icon"><Loading /></el-icon>
              <p>分割处理中...</p>
            </div>
            <div class="image-info">
              <span>算法: Watershed</span>
              <span v-if="getGroupStats.global">颗粒: {{ getGroupStats.global.contours_count }}</span>
            </div>
          </div>

          <div class="arrow-divider">
            <el-icon class="arrow-icon"><Right /></el-icon>
          </div>

          <div class="image-box result">
            <div class="image-label result-label">图像分类</div>
            <div class="image-placeholder" v-if="globalImages.classified">
              <img :src="globalImages.classified" alt="分类图像" class="result-image" />
            </div>
            <div class="image-placeholder" v-else>
              <el-icon class="placeholder-icon"><Finished /></el-icon>
              <p>等待分类</p>
            </div>
            <div class="image-info">
              <span v-if="getGroupStats.global">颗粒数: {{ getGroupStats.global.contours_count }}</span>
              <span>状态: 已完成</span>
            </div>
          </div>
        </div>

        <!-- 局部图像对比区域 -->
        <div class="view-type-label">局部视图</div>
        <div class="comparison-container">
          <div class="image-box">
            <div class="image-label">原始图像</div>
            <div class="image-placeholder" v-if="localImages.original">
              <img :src="localImages.original" alt="原始图像" class="result-image" />
            </div>
            <div class="image-placeholder" v-else>
              <el-icon class="placeholder-icon"><Camera /></el-icon>
              <p>暂无图像</p>
            </div>
            <div class="image-info">
              <span>类型: 局部视图</span>
              <span>组别: 第{{ selectedGroup }}组</span>
            </div>
          </div>

          <div class="arrow-divider">
            <el-icon class="arrow-icon"><Right /></el-icon>
          </div>

          <div class="image-box processing">
            <div class="image-label processing-label">
              <span>图像分割</span>
            </div>
            <div class="image-placeholder" v-if="localImages.segmented">
              <img :src="localImages.segmented" alt="分割图像" class="result-image" />
            </div>
            <div class="image-placeholder processing-bg" v-else>
              <el-icon class="placeholder-icon"><Loading /></el-icon>
              <p>分割处理中...</p>
            </div>
            <div class="image-info">
              <span>算法: Watershed</span>
              <span v-if="getGroupStats.local">颗粒: {{ getGroupStats.local.contours_count }}</span>
            </div>
          </div>

          <div class="arrow-divider">
            <el-icon class="arrow-icon"><Right /></el-icon>
          </div>

          <div class="image-box result">
            <div class="image-label result-label">图像分类</div>
            <div class="image-placeholder" v-if="localImages.classified">
              <img :src="localImages.classified" alt="分类图像" class="result-image" />
            </div>
            <div class="image-placeholder" v-else>
              <el-icon class="placeholder-icon"><Finished /></el-icon>
              <p>等待分类</p>
            </div>
            <div class="image-info">
              <span v-if="getGroupStats.local">颗粒数: {{ getGroupStats.local.contours_count }}</span>
              <span>状态: 已完成</span>
            </div>
          </div>
        </div>

        <!-- 处理步骤流程 -->
        <div class="processing-steps">
          <div class="step-title">处理流程</div>
          <div class="steps-container">
            <div class="step-item active">
              <div class="step-icon">
                <el-icon><Upload /></el-icon>
              </div>
              <div class="step-name">图像采集</div>
              <div class="step-status">已完成</div>
            </div>
            
            <div class="step-connector active"></div>
            
            <div class="step-item active">
              <div class="step-icon">
                <el-icon><Setting /></el-icon>
              </div>
              <div class="step-name">预处理</div>
              <div class="step-status">已完成</div>
            </div>
            
            <div class="step-connector active"></div>
            
            <div class="step-item current">
              <div class="step-icon">
                <el-icon><View /></el-icon>
              </div>
              <div class="step-name">特征提取</div>
              <div class="step-status">进行中</div>
            </div>
            
            <div class="step-connector"></div>
            
            <div class="step-item">
              <div class="step-icon">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="step-name">结果分析</div>
              <div class="step-status">等待中</div>
            </div>
            
            <div class="step-connector"></div>
            
            <div class="step-item">
              <div class="step-icon">
                <el-icon><Download /></el-icon>
              </div>
              <div class="step-name">导出报告</div>
              <div class="step-status">等待中</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  Picture,
  Camera,
  Right,
  Loading,
  Finished,
  Upload,
  Setting,
  View,
  DataAnalysis,
  Download
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const selectedGroup = ref('1')
const processingData = ref(null)
const availableGroups = ref([])

// 存储已加载的图片 base64 数据
const imageCache = ref({})

// 加载单张图片
const loadImage = async (imagePath) => {
  if (!imagePath) return null
  
  // 检查缓存
  if (imageCache.value[imagePath]) {
    return imageCache.value[imagePath]
  }
  
  try {
    const result = await window.api.ipcRenderer.invoke('read-local-image', imagePath)
    if (result.success) {
      imageCache.value[imagePath] = result.data
      return result.data
    }
  } catch (error) {
    console.error('加载图片失败:', error)
  }
  
  return null
}

// 计算图片路径
const getImagePath = (viewType, imageType, group) => {
  if (!processingData.value) return null
  
  const viewData = processingData.value[viewType]
  if (!viewData || viewData.length === 0) return null
  
  // 查找对应组的数据
  const groupData = viewData.find(item => {
    const fileName = item[`${imageType}_path`]?.split('\\').pop() || ''
    return fileName.startsWith(`${group}_`)
  })
  
  if (!groupData) return null
  
  return groupData[`${imageType}_path`]
}

// 全局视图图片数据
const globalImages = ref({
  original: null,
  segmented: null,
  classified: null
})

// 局部视图图片数据
const localImages = ref({
  original: null,
  segmented: null,
  classified: null
})

// 加载当前组的所有图片
const loadGroupImages = async () => {
  const globalOriginalPath = getImagePath('global', 'original', selectedGroup.value)
  const globalSegmentedPath = getImagePath('global', 'segmented', selectedGroup.value)
  const globalClassifiedPath = getImagePath('global', 'classified', selectedGroup.value)
  
  const localOriginalPath = getImagePath('local', 'original', selectedGroup.value)
  const localSegmentedPath = getImagePath('local', 'segmented', selectedGroup.value)
  const localClassifiedPath = getImagePath('local', 'classified', selectedGroup.value)
  
  // 并行加载所有图片
  const [
    globalOriginal,
    globalSegmented,
    globalClassified,
    localOriginal,
    localSegmented,
    localClassified
  ] = await Promise.all([
    loadImage(globalOriginalPath),
    loadImage(globalSegmentedPath),
    loadImage(globalClassifiedPath),
    loadImage(localOriginalPath),
    loadImage(localSegmentedPath),
    loadImage(localClassifiedPath)
  ])
  
  globalImages.value = {
    original: globalOriginal,
    segmented: globalSegmented,
    classified: globalClassified
  }
  
  localImages.value = {
    original: localOriginal,
    segmented: localSegmented,
    classified: localClassified
  }
  
  console.log('图片加载完成，组别:', selectedGroup.value)
}

// 获取当前组的统计信息
const getGroupStats = computed(() => {
  if (!processingData.value) return { global: null, local: null }
  
  const findGroupData = (viewType) => {
    const viewData = processingData.value[viewType]
    if (!viewData || viewData.length === 0) return null
    
    return viewData.find(item => {
      const fileName = item.original_path?.split('\\').pop() || ''
      return fileName.startsWith(`${selectedGroup.value}_`)
    })
  }
  
  return {
    global: findGroupData('global'),
    local: findGroupData('local')
  }
})

// 加载处理结果数据
const loadProcessingData = async () => {
  try {
    // 使用 IPC 读取本地 JSON 文件
    const result = await window.api.ipcRenderer.invoke('read-processing-results')
    
    if (!result.success) {
      throw new Error(result.error)
    }
    
    processingData.value = result.data
    
    // 提取所有可用的组号
    const groups = new Set()
    
    if (result.data.global) {
      result.data.global.forEach(item => {
        const fileName = item.original_path?.split('\\').pop() || ''
        const match = fileName.match(/^(\d+)_/)
        if (match) groups.add(match[1])
      })
    }
    
    if (result.data.local) {
      result.data.local.forEach(item => {
        const fileName = item.original_path?.split('\\').pop() || ''
        const match = fileName.match(/^(\d+)_/)
        if (match) groups.add(match[1])
      })
    }
    
    availableGroups.value = Array.from(groups).sort((a, b) => parseInt(a) - parseInt(b))
    
    // 默认选择第一组
    if (availableGroups.value.length > 0) {
      selectedGroup.value = availableGroups.value[0]
    }
    
    console.log('处理数据加载成功:', result.data)
    console.log('可用组别:', availableGroups.value)
    
    // 加载第一组的图片
    await loadGroupImages()
  } catch (error) {
    console.error('加载处理数据失败:', error)
    ElMessage.error('加载图像数据失败')
  }
}

// 监听组别变化
watch(selectedGroup, () => {
  loadGroupImages()
})

onMounted(() => {
  loadProcessingData()
})
</script>

<style scoped>
.image-processing {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1e3a 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.processing-header {
  background: rgba(0, 33, 64, 0.4);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 145, 255, 0.2);
  padding: 12px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: slideDown 0.5s ease-out;
  min-height: 60px;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 24px;
  color: #00a8ff;
  filter: drop-shadow(0 0 10px rgba(0, 168, 255, 0.5));
}

.header-title h2 {
  margin: 0;
  color: #fff;
  font-size: 20px;
  font-weight: 500;
  text-shadow: 0 0 20px rgba(0, 168, 255, 0.3);
}

.header-stats {
  display: flex;
  gap: 20px;
}

.stat-card {
  background: rgba(0, 168, 255, 0.1);
  border: 1px solid rgba(0, 168, 255, 0.3);
  border-radius: 6px;
  padding: 8px 16px;
  text-align: center;
  backdrop-filter: blur(10px);
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 168, 255, 0.3);
  border-color: rgba(0, 168, 255, 0.5);
}

.stat-label {
  font-size: 11px;
  color: #8b9eb0;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 18px;
  color: #00a8ff;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.5);
}

.processing-content {
  flex: 1;
  display: flex;
  padding: 15px 30px 20px;
  overflow-y: auto;
}

.image-comparison-section {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-title h3 {
  margin: 0;
  color: #00a8ff;
  font-size: 18px;
  font-weight: 500;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

.group-selector {
  width: 150px;
}

.view-type-label {
  color: #00a8ff;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
  padding-left: 10px;
  border-left: 3px solid #00a8ff;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
  animation: fadeInLeft 0.5s ease-out;
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.comparison-container {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  gap: 25px;
  align-items: center;
  background: rgba(0, 33, 64, 0.3);
  border: 1px solid rgba(0, 145, 255, 0.2);
  border-radius: 12px;
  padding: 30px 25px;
  position: relative;
  overflow: hidden;
}

.comparison-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 50% 50%, rgba(0, 168, 255, 0.05) 0%, transparent 70%);
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.image-box {
  background: rgba(0, 24, 48, 0.4);
  border: 2px solid rgba(0, 145, 255, 0.3);
  border-radius: 8px;
  padding: 10px;
  transition: all 0.3s;
  position: relative;
  z-index: 1;
  max-width: 280px;
}

.image-box:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 168, 255, 0.2);
  border-color: rgba(0, 168, 255, 0.5);
}

.image-box.processing {
  border-color: rgba(255, 193, 7, 0.3);
}

.image-box.result {
  border-color: rgba(103, 194, 58, 0.3);
}

.image-label {
  font-size: 13px;
  color: #00a8ff;
  margin-bottom: 8px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.processing-label {
  color: #ffc107;
}

.result-label {
  color: #67c23a;
}

.processing-dots {
  display: flex;
  gap: 4px;
}

.processing-dots span {
  width: 6px;
  height: 6px;
  background: #ffc107;
  border-radius: 50%;
  animation: dotPulse 1.4s infinite;
}

.processing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.processing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.image-placeholder {
  aspect-ratio: 4/3;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(0, 168, 255, 0.4);
  margin-bottom: 8px;
  position: relative;
  overflow: hidden;
  min-height: 150px;
  max-height: 200px;
}

.result-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.image-placeholder::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(0, 168, 255, 0.1), transparent);
  animation: scan 3s linear infinite;
}

@keyframes scan {
  0% { transform: translateX(-100%) translateY(-100%); }
  100% { transform: translateX(100%) translateY(100%); }
}

.processing-bg {
  background: rgba(255, 193, 7, 0.05);
}

.processing-bg::before {
  background: linear-gradient(45deg, transparent, rgba(255, 193, 7, 0.1), transparent);
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 8px;
  z-index: 1;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.image-placeholder p {
  font-size: 13px;
  margin: 0;
  z-index: 1;
}

.image-info {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #8b9eb0;
  gap: 8px;
}

.image-info span {
  flex: 1;
  text-align: center;
}

.arrow-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00a8ff;
  font-size: 24px;
  z-index: 1;
  position: relative;
  top: -25px;
}

.arrow-icon {
  animation: arrowPulse 2s ease-in-out infinite;
}

@keyframes arrowPulse {
  0%, 100% { transform: translateX(0); opacity: 0.5; }
  50% { transform: translateX(5px); opacity: 1; }
}

.processing-steps {
  background: rgba(0, 33, 64, 0.3);
  border: 1px solid rgba(0, 145, 255, 0.2);
  border-radius: 12px;
  padding: 18px 25px;
}

.step-title {
  color: #00a8ff;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 15px;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

.steps-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  transition: all 0.3s;
}

.step-icon {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(0, 24, 48, 0.5);
  border: 2px solid rgba(0, 145, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: rgba(0, 168, 255, 0.5);
  transition: all 0.3s;
}

.step-item.active .step-icon {
  background: rgba(0, 168, 255, 0.2);
  border-color: #00a8ff;
  color: #00a8ff;
  box-shadow: 0 0 20px rgba(0, 168, 255, 0.3);
}

.step-item.current .step-icon {
  background: rgba(255, 193, 7, 0.2);
  border-color: #ffc107;
  color: #ffc107;
  animation: currentPulse 2s ease-in-out infinite;
  box-shadow: 0 0 20px rgba(255, 193, 7, 0.4);
}

@keyframes currentPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.step-name {
  font-size: 12px;
  color: #8b9eb0;
  font-weight: 500;
}

.step-item.active .step-name {
  color: #00a8ff;
}

.step-item.current .step-name {
  color: #ffc107;
}

.step-status {
  font-size: 10px;
  color: rgba(139, 158, 176, 0.6);
}

.step-item.active .step-status {
  color: rgba(0, 168, 255, 0.8);
}

.step-item.current .step-status {
  color: rgba(255, 193, 7, 0.8);
}

.step-connector {
  flex: 1;
  height: 2px;
  background: rgba(0, 145, 255, 0.2);
  margin: 0 10px;
  position: relative;
  overflow: hidden;
}

.step-connector.active {
  background: rgba(0, 168, 255, 0.4);
}

.step-connector.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 30px;
  background: linear-gradient(90deg, transparent, #00a8ff, transparent);
  animation: flowRight 2s linear infinite;
}

@keyframes flowRight {
  0% { left: -30px; }
  100% { left: 100%; }
}

/* 滚动条样式 */
.processing-content::-webkit-scrollbar {
  width: 6px;
}

.processing-content::-webkit-scrollbar-track {
  background: rgba(0, 24, 48, 0.3);
  border-radius: 3px;
}

.processing-content::-webkit-scrollbar-thumb {
  background: rgba(0, 168, 255, 0.3);
  border-radius: 3px;
}

.processing-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 168, 255, 0.5);
}
</style>

