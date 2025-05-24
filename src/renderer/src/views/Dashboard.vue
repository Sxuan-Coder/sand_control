<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div class="header-left">
        <h1>砂石级配实验监控平台</h1>
        <div class="system-status" :class="{ 'status-running': isRunning }">
          系统{{ isRunning ? '运行中' : '已停止' }}
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showReport" class="report-button">
          <el-icon><DataAnalysis /></el-icon>
          数据报表
        </el-button>
        <el-button type="success" @click="showSandGradingReport" class="report-button">
          <el-icon><Document /></el-icon>
          砂级配报告
        </el-button>
        <el-button type="danger" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出登录
        </el-button>
      </div>
    </div>

    <div class="dashboard-content">
      <div class="left-panel">
        <div class="control-section">
          <div class="control-header">
            <h2>实验控制</h2>
          </div>
          <div class="control-body">
            <el-form class="control-form" label-width="100px" size="default">
              <el-form-item label="数据路径">
                <el-input
                  v-model="dataPath"
                  placeholder="请输入数据保存路径"
                  :disabled="isRunning"
                />
              </el-form-item>

              <div class="form-row">
                <el-form-item label="总组数" class="form-item-half">
                  <el-input-number
                    v-model="totalGroups"
                    :min="1"
                    :max="100"
                    :disabled="isRunning"
                    controls-position="right"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-form-item label="每组照片" class="form-item-half">
                  <el-input-number
                    v-model="photosPerGroup"
                    :min="1"
                    :max="100"
                    :disabled="isRunning"
                    controls-position="right"
                    style="width: 100%"
                  />
                </el-form-item>
              </div>

              <el-form-item label="给料量(克)">
                <el-input-number
                  v-model="feedingAmount"
                  :min="0.1"
                  :max="10"
                  :step="0.1"
                  :precision="1"
                  :disabled="isRunning"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>

              <div class="control-buttons">
                <el-button
                  type="primary"
                  @click="initSystem"
                  :loading="initLoading"
                  :disabled="isInitialized || isRunning"
                >
                  初始化系统
                </el-button>
                <el-button
                  type="primary"
                  @click="start_openOrClose_Light"
                  :loading="LightLoading"
                  :disabled="isRunning"
                >
                  {{ light_status }}
                </el-button>
              </div>

              <div class="control-buttons">
                <el-button
                  type="success"
                  @click="startExperiment"
                  :loading="startLoading"
                  :disabled="!isInitialized || isRunning"
                >
                  开始实验
                </el-button>
                <el-button
                  type="danger"
                  @click="stopExperiment"
                  :loading="stopLoading"
                  :disabled="!isRunning"
                >
                  停止实验
                </el-button>
              </div>
            </el-form>
          </div>
        </div>

        <ScaleControl class="scale-section" />
        <CleanSandControl class="scale-section" />
      </div>

      <div class="right-panel">
        <div class="top-row">
          <div class="progress-section">
            <div class="progress-header">
              <h2>实验进度</h2>
              <div class="progress-stats">
                <div class="stat-item">
                  <div class="stat-label">已完成组数</div>
                  <div class="stat-value">{{ completedGroups }}/{{ totalGroups }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">当前照片</div>
                  <div class="stat-value">{{ currentPhoto }}/{{ photosPerGroup }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">运行时间</div>
                  <div class="stat-value">{{ elapsedTime }}s</div>
                </div>
              </div>
            </div>
            <div class="progress-container">
              <progress-chart :progress="experimentProgress" />
            </div>
          </div>

          <div class="feeding-section">
            <h2>给料状态</h2>
            <div class="chart-container">
              <feeding-chart :data="feedingData" />
            </div>
          </div>
        </div>

        <div class="bottom-row">
          <div class="photos-section">
            <h2>最新照片</h2>
            <div class="photo-grid">
              <div v-for="(photo, index) in latestPhotos" :key="index" class="photo-item">
                <div class="photo-placeholder" v-if="!photo.path">
                  <el-icon><Picture /></el-icon>
                </div>
                <div class="photo-image" v-else>
                  <img
                    :src="photo.path"
                    alt="实验照片"
                    @error="handleImageError"
                    @load="handleImageLoad"
                  />
                </div>
                <div class="photo-info">
                  <span>组{{ photo.group }} - 照片{{ photo.photo }}</span>
                  <span>{{ photo.time }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="console-section">
            <h2>控制台监控</h2>
            <div class="console-container">
              <div class="console-header">
                <div class="console-tabs">
                  <div class="tab active">系统日志</div>
                  <div class="tab">运行状态</div>
                </div>
                <div class="console-controls">
                  <el-icon class="control-icon"><Delete /></el-icon>
                  <el-icon class="control-icon"><Download /></el-icon>
                </div>
              </div>
              <div class="console-body">
                <div class="log-list">
                  <div
                    v-for="(log, index) in systemLogs"
                    :key="index"
                    :class="['log-item', log.type]"
                  >
                    <span class="log-time">{{ log.time }}</span>
                    <span class="log-content">{{ log.content }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="reportDialogVisible"
      title="数据分析报表"
      width="90%"
      :destroy-on-close="true"
      class="report-dialog"
    >
      <data-report />
    </el-dialog>
    <el-dialog
      v-model="sandGradingReportDialogVisible"
      title="砂级配报告"
      width="90%"
      :destroy-on-close="true"
      class="report-dialog"
    >
      <sand-grading-report />
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import {
  VideoCamera,
  Connection,
  Monitor,
  Picture,
  Camera,
  VideoPlay,
  Delete,
  Download,
  DataAnalysis,
  Document,
  SwitchButton
} from '@element-plus/icons-vue'
import ProgressChart from '../components/dashboard/ProgressChart.vue'
import FeedingChart from '../components/dashboard/FeedingChart.vue'
import DataReport from '../components/DataReport.vue'
import SandGradingReport from '../components/SandGradingReport.vue'
import ScaleControl from '../components/dashboard/ScaleControl.vue'
import CleanSandControl from '../components/CleanSandControl.vue'
import api, {
  initializeSystem,
  openLight,
  closeLight,
  startProcess,
  stopProcess,
  cleanSand as cleanSandApi,
  getDirectoryImages,
  getImageUrl,
  testServerConnection
} from '../api'
import { number } from 'echarts'

export default {
  name: 'Dashboard',
  components: {
    ProgressChart,
    FeedingChart,
    DataReport,
    SandGradingReport,
    ScaleControl,
    CleanSandControl,
    VideoCamera,
    Connection,
    Monitor,
    Picture,
    Camera,
    VideoPlay,
    Delete,
    Download,
    DataAnalysis,
    Document,
    SwitchButton
  },
  setup() {
    // 系统状态
    const isRunning = ref(false)
    const isInitialized = ref(false)
    const cameraConnected = ref(false)
    const controllerConnected = ref(false)
    const sensorConnected = ref(false)
    const light_status = ref('打开灯光')

    // 实验参数
    const dataPath = ref('F:/sand_data/test')
    const totalGroups = ref(5)
    const photosPerGroup = ref(5)
    const feedingAmount = ref(0.1)

    // 进度数据
    const completedGroups = ref(0)
    const currentPhoto = ref(0)
    const elapsedTime = ref(0)
    const feedingData = ref([])

    // 图片数据
    const latestPhotos = ref([
      { path: '', group: 0, photo: 0, time: '' },
      { path: '', group: 0, photo: 0, time: '' },
      { path: '', group: 0, photo: 0, time: '' },
      { path: '', group: 0, photo: 0, time: '' }
    ])

    // 图片路径配置
    const globalImagesPath = ref('')
    const localImagesPath = ref('')

    // 图片刷新间隔（毫秒）
    const imageRefreshInterval = ref(5000)

    // 当前显示的图片索引
    const currentImageIndex = ref(0)

    // 缓存的图片列表
    const cachedImages = ref([])

    // 加载状态
    const initLoading = ref(false)
    const cleanLoading = ref(false)
    const LightLoading = ref(false)
    const startLoading = ref(false)
    const stopLoading = ref(false)

    const reportDialogVisible = ref(false)
    const sandGradingReportDialogVisible = ref(false)

    const experimentProgress = computed(() => {
      const totalPhotos = totalGroups.value * photosPerGroup.value
      const completedPhotos = completedGroups.value * photosPerGroup.value + currentPhoto.value

      if (totalPhotos > 0) {
        return Math.round((completedPhotos / totalPhotos) * 100)
      }
      return 0
    })

    // 系统日志数据
    const systemLogs = ref([])

    // 测试网络连接
    const testBaiduConnection = async () => {
      try {
        addLog('正在测试网络连接...', 'info')
        
        // 使用 IPC 通信测试网络连接
        // 这种方法可以避免 CSP 限制
        const result = await window.api.checkApiStatus()
        
        if (result.success) {
          ElMessage.success('网络连接正常')
          addLog('网络连接正常', 'success')
          return true
        } else {
          ElMessage.error(`网络连接异常: ${result.error || '未知错误'}`)
          addLog(`网络连接异常: ${result.error || '未知错误'}`, 'error')
          return false
        }
      } catch (error) {
        ElMessage.error(`网络连接测试失败：${error.message}`)
        addLog(`网络连接测试失败：${error.message}`, 'error')
        return false
      }
    }

    // 测试服务器连接
    const checkServerConnection = async () => {
      try {
        const result = await testServerConnection()
        if (result.success) {
          ElMessage.success(result.message)
          addLog('服务器连接成功', 'success')
          return true
        } else {
          ElMessage.error(result.message)
          addLog('服务器连接失败', 'error')
          return false
        }
      } catch (error) {
        ElMessage.error('服务器连接测试失败')
        addLog('服务器连接测试失败', 'error')
        console.error('服务器连接测试错误:', error)
        return false
      }
    }

    // 方法
    const initSystem = async () => {
      try {
        initLoading.value = true
        await initializeSystem()
        isInitialized.value = true
        ElMessage.success('系统初始化成功')
      } catch (error) {
        ElMessage.error('系统初始化失败')
        console.log(error)
      } finally {
        initLoading.value = false
      }
    }

    const start_openOrClose_Light = async () => {
      if (light_status.value === '打开灯光') {
        try {
          LightLoading.value = true
          await openLight()
          light_status.value = '关闭灯光'
          addLog('灯光已打开', 'success')
        } catch (error) {
          addLog('打开灯光失败', 'error')
        } finally {
          LightLoading.value = false
        }
      } else {
        try {
          LightLoading.value = true
          await closeLight()
          light_status.value = '打开灯光'
          addLog('灯光已关闭', 'success')
        } catch (error) {
          addLog('关闭灯光失败', 'error')
        } finally {
          LightLoading.value = false
        }
      }
    }

    const startExperiment = async () => {
      try {
        startLoading.value = true
        await startProcess({
          base_path: dataPath.value,
          start_group: totalGroups.value,
          photos_per_group: photosPerGroup.value,
          once_count: feedingAmount.value
        })
        isRunning.value = true
        ElMessage.success('实验开始')
      } catch (error) {
        ElMessage.error('实验启动失败')
      } finally {
        startLoading.value = false
      }
    }

    const stopExperiment = async () => {
      try {
        stopLoading.value = true
        await stopProcess()
        isRunning.value = false
        ElMessage.success('实验已停止')
      } catch (error) {
        ElMessage.error('实验停止失败')
      } finally {
        stopLoading.value = false
      }
    }

    // 模拟系统日志更新
    const addLog = (content, type = 'info') => {
      const levels = {
        info: 'INFO',
        warning: 'WARN',
        error: 'ERROR',
        success: 'SUCCESS'
      }
      systemLogs.value.unshift({
        time: new Date().toLocaleTimeString(),
        level: levels[type],
        content,
        type
      })
      if (systemLogs.value.length > 100) {
        systemLogs.value.pop()
      }
    }

    // 模拟给料数据更新
    const updateFeedingData = () => {
      const now = new Date()
      // 模拟更真实的给料波动
      const baseValue = feedingAmount.value
      const time = Date.now() / 1000
      // 使用多个正弦波叠加制造更自然的波动
      const wave1 = Math.sin(time) * 0.2
      const wave2 = Math.sin(time * 2) * 0.1
      const wave3 = Math.sin(time * 0.5) * 0.15
      const noise = (Math.random() - 0.5) * 0.1
      const value = baseValue + wave1 + wave2 + wave3 + noise

      feedingData.value.push({
        time: now.toLocaleTimeString(),
        value: Math.max(0, value).toFixed(2)
      })
      if (feedingData.value.length > 30) {
        feedingData.value.shift()
      }
    }

    // 加载本地图片
    const loadLocalImages = async () => {
      try {
        // 更新图片路径 - 使用正确的路径格式
        globalImagesPath.value = `${dataPath.value}/global`
        localImagesPath.value = `${dataPath.value}/local`
        
        // 从全局路径加载图片
        const globalResponse = await getDirectoryImages(globalImagesPath.value)
        const globalFiles = globalResponse.data || []
        
        // 从本地路径加载图片
        const localResponse = await getDirectoryImages(localImagesPath.value)
        const localFiles = localResponse.data || []
        
        // 处理全局图片
        const globalImages = globalFiles.map(file => {
          // 从文件名中提取组号和照片号
          // 文件名格式为 {组号}_{照片号}.jpg
          const fileNameMatch = file.name.match(/(\d+)_(\d+)\.jpg$/i) || []
          const group = fileNameMatch[1] ? parseInt(fileNameMatch[1]) : 1
          const photo = fileNameMatch[2] ? parseInt(fileNameMatch[2]) : 1
          
          return {
            path: getImageUrl(file.path),
            actualPath: file.path,
            group: group,
            photo: photo,
            source: 'global',
            time: new Date(file.modifiedTime).toLocaleTimeString()
          }
        })
        
        // 处理本地图片
        const localImages = localFiles.map(file => {
          // 从文件名中提取组号和照片号
          const fileNameMatch = file.name.match(/(\d+)_(\d+)\.jpg$/i) || []
          const group = fileNameMatch[1] ? parseInt(fileNameMatch[1]) : 1
          const photo = fileNameMatch[2] ? parseInt(fileNameMatch[2]) : 1
          
          return {
            path: getImageUrl(file.path),
            actualPath: file.path,
            group: group,
            photo: photo,
            source: 'local',
            time: new Date(file.modifiedTime).toLocaleTimeString()
          }
        })
        
        // 合并和排序图片
        // 我们需要按照特定顺序排列:
        // 1. 先按组号排序
        // 2. 对于相同组号，按照照片号排序
        // 3. 对于相同组号和照片号，按照global/local顺序排列
        
        // 创建一个映射来存储每个组和照片的global和local图片
        const imageMap = new Map()
        
        // 处理全局图片
        globalImages.forEach(img => {
          const key = `${img.group}_${img.photo}`
          if (!imageMap.has(key)) {
            imageMap.set(key, { global: null, local: null })
          }
          imageMap.get(key).global = img
        })
        
        // 处理本地图片
        localImages.forEach(img => {
          const key = `${img.group}_${img.photo}`
          if (!imageMap.has(key)) {
            imageMap.set(key, { global: null, local: null })
          }
          imageMap.get(key).local = img
        })
        
        // 按照组号和照片号排序
        const sortedKeys = Array.from(imageMap.keys()).sort((a, b) => {
          const [aGroup, aPhoto] = a.split('_').map(Number)
          const [bGroup, bPhoto] = b.split('_').map(Number)
          
          if (aGroup !== bGroup) return aGroup - bGroup
          return aPhoto - bPhoto
        })
        
        // 创建排序后的图片数组
        cachedImages.value = []
        sortedKeys.forEach(key => {
          const pair = imageMap.get(key)
          if (pair.global) cachedImages.value.push(pair.global)
          if (pair.local) cachedImages.value.push(pair.local)
        })
        
        // 如果没有找到图片，使用测试图片
        if (cachedImages.value.length === 0) {
          addLog(`未找到图片，使用测试图片代替。查找路径: ${globalImagesPath.value} 和 ${localImagesPath.value}`, 'warning')
          createTestImages()
        } else {
          addLog(`成功加载 ${cachedImages.value.length} 张图片`, 'success')
        }
        
        // 更新显示
        updateLatestPhotos()
      } catch (error) {
        console.error('加载图片失败:', error)
        addLog('加载图片失败: ' + error.message, 'error')
        
        // 出错时使用测试图片
        createTestImages()
        updateLatestPhotos()
      }
    }

    // 创建测试图片数据
    const createTestImages = () => {
      const imgPath = '/test-image.jpg'
      
      // 创建模拟图片数据，按照特定顺序排列
      cachedImages.value = [
        {
          path: imgPath,
          actualPath: `${globalImagesPath.value}/5_1.jpg (测试图片)`,
          group: 5,
          photo: 1,
          source: 'global',
          time: new Date().toLocaleTimeString()
        },
        {
          path: imgPath,
          actualPath: `${localImagesPath.value}/5_1.jpg (测试图片)`,
          group: 5,
          photo: 1,
          source: 'local',
          time: new Date().toLocaleTimeString()
        },
        {
          path: imgPath,
          actualPath: `${globalImagesPath.value}/5_2.jpg (测试图片)`,
          group: 5,
          photo: 2,
          source: 'global',
          time: new Date().toLocaleTimeString()
        },
        {
          path: imgPath,
          actualPath: `${localImagesPath.value}/5_2.jpg (测试图片)`,
          group: 5,
          photo: 2,
          source: 'local',
          time: new Date().toLocaleTimeString()
        }
      ]
    }

    // 更新最新的图片路径
    const updateLatestPhotos = () => {
      try {
        // 如果没有缓存的图片，则使用测试图片
        if (cachedImages.value.length === 0) {
          // 使用测试图片
          const imgPath = '/test-image.jpg'
          latestPhotos.value = [
            { path: imgPath, group: 5, photo: 1, source: 'global', time: new Date().toLocaleTimeString() },
            { path: imgPath, group: 5, photo: 1, source: 'local', time: new Date().toLocaleTimeString() },
            { path: imgPath, group: 5, photo: 2, source: 'global', time: new Date().toLocaleTimeString() },
            { path: imgPath, group: 5, photo: 2, source: 'local', time: new Date().toLocaleTimeString() }
          ]
          
          // 尝试加载本地图片
          loadLocalImages()
          return
        }
        
        // 按顺序选择4张图片显示
        const startIndex = currentImageIndex.value % cachedImages.value.length
        const selectedFiles = []
        
        // 确保我们选择的是4张图片，并且按照global/local交替的顺序
        // 如果缓存中的图片不足4张，则循环使用
        for (let i = 0; i < 4; i++) {
          const index = (startIndex + i) % cachedImages.value.length
          selectedFiles.push(cachedImages.value[index])
        }
        
        // 更新当前索引，下次显示下一组图片
        currentImageIndex.value = (startIndex + 4) % cachedImages.value.length
        
        // 更新图片显示
        latestPhotos.value = selectedFiles.map((img, index) => {
          return {
            path: img.path,  // 这里使用后端提供的图片路径
            actualPath: img.actualPath, // 保存实际路径用于调试
            group: img.group,
            photo: img.photo,
            source: img.source,
            time: img.time
          }
        })
        
        // 更新日志，显示当前图片的组号、照片号和来源
        const logMessage = selectedFiles.map(img => 
          `${img.source}/${img.group}_${img.photo}`
        ).join(', ')
        
        addLog(`图片更新成功 (当前显示: ${logMessage})`, 'success')
      } catch (error) {
        console.error('获取图片失败:', error)
        addLog('获取图片失败', 'error')
        
        // 出错时使用测试图片
        const imgPath = '/test-image.jpg'
        
        // 创建模拟图片数据，按照特定顺序排列
        latestPhotos.value = [
          { path: imgPath, group: 5, photo: 1, source: 'global', time: new Date().toLocaleTimeString() },
          { path: imgPath, group: 5, photo: 1, source: 'local', time: new Date().toLocaleTimeString() },
          { path: imgPath, group: 5, photo: 2, source: 'global', time: new Date().toLocaleTimeString() },
          { path: imgPath, group: 5, photo: 2, source: 'local', time: new Date().toLocaleTimeString() }
        ]
      }
    }

    // 处理图片加载错误
    const handleImageError = (e) => {
      // 当图片加载失败时，清空路径以显示占位符
      const index = latestPhotos.value.findIndex((photo) => photo.path === e.target.src)
      if (index !== -1) {
        latestPhotos.value[index].path = ''
      }
    }

    // 处理图片加载成功
    const handleImageLoad = (e) => {
      // 图片加载成功，无需特殊处理
    }

    const testProgress = () => {
      // 更新进度
      if (currentPhoto.value < photosPerGroup.value - 1) {
        currentPhoto.value++
      } else {
        currentPhoto.value = 0
        if (completedGroups.value < totalGroups.value - 1) {
          completedGroups.value++
        } else {
          // 重置进度
          completedGroups.value = 0
          currentPhoto.value = 0
        }
      }

      // 添加日志
      addLog(
        `当前进度：第 ${completedGroups.value + 1} 组，第 ${currentPhoto.value + 1} 张照片`,
        'info'
      )
    }

    const addGroup = () => {
      if (totalGroups.value < 100) {
        totalGroups.value++
        addLog(`修改总组数为: ${totalGroups.value}`, 'info')
      }
    }

    const addPhotos = () => {
      if (photosPerGroup.value < 100) {
        photosPerGroup.value++
        addLog(`修改每组照片数为: ${photosPerGroup.value}`, 'info')
      }
    }

    const testUpdatePhotos = () => {
      addLog('刷新图片显示', 'info')
      loadLocalImages()
      addLog('图片刷新完成', 'success')
    }

    const showReport = () => {
      reportDialogVisible.value = true
    }

    const showSandGradingReport = () => {
      sandGradingReportDialogVisible.value = true
    }

    // 处理登出
    const handleLogout = () => {
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
        .then(() => {
          // 清除登录状态
          localStorage.removeItem('isLoggedIn')
          localStorage.removeItem('username')

          ElMessage({
            type: 'success',
            message: '已成功退出登录'
          })

          // 跳转到登录页
          const router = useRouter()
          router.push('/login')
        })
        .catch(() => {
          // 取消登出
        })
    }

    // 启动一个单独的定时器以自动更新照片
    let timer
    let imageRefreshTimer

    onMounted(async () => {
      // 检查服务器连接状态
      await checkServerConnection()
      
      // 初始化给料数据
      for (let i = 0; i < 10; i++) {
        updateFeedingData()
      }

      // 添加初始日志
      addLog('系统启动完成，等待初始化...', 'info')
      addLog('正在检查设备连接状态...', 'info')

      // 检测百度链接
      testBaiduConnection()

      // 加载本地图片
      loadLocalImages()

      // 在组件挂载时初始化图片
      updateLatestPhotos()

      // 创建测试图片数据
      createTestImages()

      // 启动定时器，更频繁更新
      timer = setInterval(() => {
        if (isRunning.value) {
          updateFeedingData()
          elapsedTime.value++

          // 更新实验进度
          if (elapsedTime.value % 5 === 0) {
            // 每5秒更新一次进度
            if (currentPhoto.value < photosPerGroup.value - 1) {
              currentPhoto.value++
            } else {
              currentPhoto.value = 0
              if (completedGroups.value < totalGroups.value - 1) {
                completedGroups.value++
              } else {
                // 实验完成
                completedGroups.value = totalGroups.value
                currentPhoto.value = photosPerGroup.value
                isRunning.value = false
                addLog('实验已完成', 'success')
              }
            }
          }

          // 随机添加一些系统日志
          if (Math.random() < 0.1) {
            const events = [
              { content: '相机拍摄完成', type: 'success' },
              { content: '给料电机运行正常', type: 'info' },
              { content: '传感器数据采集中...', type: 'info' },
              { content: '网络连接延迟较高', type: 'warning' }
            ]
            const event = events[Math.floor(Math.random() * events.length)]
            addLog(event.content, event.type)
          }
        }
      }, 1000) // 改为每秒更新一次

      // 启动图片刷新定时器，无论系统是否运行都会刷新图片
      imageRefreshTimer = setInterval(() => {
        updateLatestPhotos()
      }, imageRefreshInterval.value)
    })

    onUnmounted(() => {
      if (timer) {
        clearInterval(timer)
      }
      if (imageRefreshTimer) {
        clearInterval(imageRefreshTimer)
      }
    })

    return {
      // 状态
      isRunning,
      isInitialized,
      cameraConnected,
      controllerConnected,
      sensorConnected,
      light_status,

      // 参数
      dataPath,
      totalGroups,
      photosPerGroup,
      feedingAmount,

      // 进度
      completedGroups,
      currentPhoto,
      elapsedTime,
      feedingData,
      experimentProgress,
      latestPhotos,

      // 图片路径
      globalImagesPath,
      localImagesPath,

      // 加载状态
      initLoading,
      LightLoading,
      startLoading,
      stopLoading,

      // 系统日志数据
      systemLogs,
      addLog,

      // 方法
      initSystem,
      start_openOrClose_Light,
      startExperiment,
      stopExperiment,
      testProgress,
      addGroup,
      addPhotos,
      testUpdatePhotos,
      handleImageError,
      handleImageLoad,
      reportDialogVisible,
      showReport,
      sandGradingReportDialogVisible,
      showSandGradingReport,
      handleLogout,
      checkServerConnection
    }
  }
}
</script>

<style scoped>
.dashboard {
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #001529;
  padding: 16px;
  gap: 16px;
  overflow: hidden;
  position: relative;
  box-sizing: border-box;
}

/* 添加动态背景效果 */
.dashboard::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 0% 0%, rgba(0, 168, 255, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 100% 0%, rgba(0, 168, 255, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 100% 100%, rgba(0, 168, 255, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 0% 100%, rgba(0, 168, 255, 0.03) 0%, transparent 50%);
  animation: gradientMove 15s ease-in-out infinite;
  z-index: 0;
}

.dashboard::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    linear-gradient(45deg, transparent 45%, rgba(0, 168, 255, 0.03) 50%, transparent 55%),
    linear-gradient(-45deg, transparent 45%, rgba(0, 168, 255, 0.03) 50%, transparent 55%);
  background-size: 300% 300%;
  animation: lightMove 8s linear infinite;
  z-index: 0;
}

@keyframes gradientMove {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
}

@keyframes lightMove {
  0% {
    background-position: 0% 0%;
  }
  100% {
    background-position: 300% 300%;
  }
}

.photos-section,
.console-section,
.progress-section,
.feeding-section {
  position: relative;
  overflow: hidden;
}

.photos-section::before,
.console-section::before,
.progress-section::before,
.feeding-section::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(0, 145, 255, 0.03) 0%, transparent 70%);
  animation: rotate 30s linear infinite;
  z-index: 0;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.photo-item {
  position: relative;
  transition: all 0.3s ease;
}

.photo-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent, rgba(0, 168, 255, 0.03), transparent);
  background-size: 200% 200%;
  animation: shimmer 3s infinite;
  z-index: 1;
  pointer-events: none;
}

@keyframes shimmer {
  0% {
    background-position: -200% -200%;
  }
  100% {
    background-position: 200% 200%;
  }
}

.photo-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 145, 255, 0.1);
}

.photo-item:hover::before {
  animation: shimmer 1.5s infinite;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  border-radius: 8px;
  background: rgba(0, 33, 64, 0.4);
  border: 1px solid rgba(0, 145, 255, 0.15);
  animation: fadeInDown 0.5s ease-out;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.dashboard-header h1 {
  margin: 0;
  color: #00a8ff;
  font-size: 24px;
  font-weight: 500;
  margin: 0;
  text-shadow: 0 0 15px rgba(0, 168, 255, 0.5);
  letter-spacing: 1px;
}

.system-status {
  padding: 4px 12px;
  border-radius: 4px;
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  font-size: 14px;
  border: 1px solid rgba(245, 108, 108, 0.2);
}

.system-status.status-running {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
  border-color: rgba(103, 194, 58, 0.2);
}

.status-list {
  display: flex;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 4px;
  background: rgba(0, 33, 64, 0.2);
  color: #f56c6c;
  font-size: 14px;
  border: 1px solid rgba(245, 108, 108, 0.2);
}

.status-item.connected {
  color: #67c23a;
  border-color: rgba(103, 194, 58, 0.2);
}

.dashboard-content {
  flex: 1;
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
  min-height: 0;
  height: calc(100vh - 92px);
  position: relative;
  z-index: 1;
  overflow: hidden;
}

/* 添加动态背景效果 */
.dashboard-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 0% 0%, rgba(0, 168, 255, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 100% 0%, rgba(0, 168, 255, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 100% 100%, rgba(0, 168, 255, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 0% 100%, rgba(0, 168, 255, 0.03) 0%, transparent 50%);
  animation: gradientMove 15s ease-in-out infinite;
  z-index: 0;
}

.dashboard-content::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    linear-gradient(45deg, transparent 45%, rgba(0, 168, 255, 0.03) 50%, transparent 55%),
    linear-gradient(-45deg, transparent 45%, rgba(0, 168, 255, 0.03) 50%, transparent 55%);
  background-size: 300% 300%;
  animation: lightMove 8s linear infinite;
  z-index: 0;
}

.left-panel,
.right-panel {
  position: relative;
  z-index: 1;
}

.right-panel {
  display: grid;
  grid-template-rows: 300px 1fr;
  gap: 16px;
  height: 100%;
  overflow: hidden;
}

.top-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.progress-section {
  background: rgba(0, 33, 64, 0.2);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border: 1px solid rgba(0, 145, 255, 0.15);
  position: relative;
  min-height: 280px;
  height: 100%;
}

.progress-header {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.progress-header h2 {
  color: #00a8ff;
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

.progress-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 0;
  width: 100%;
}

.stat-item {
  background: rgba(0, 24, 48, 0.3);
  border: 1px solid rgba(0, 145, 255, 0.15);
  border-radius: 4px;
  padding: 12px;
  text-align: center;
}

.stat-label {
  color: #8b9eb0;
  font-size: 13px;
  margin-bottom: 8px;
}

.stat-value {
  color: #00a8ff;
  font-size: 20px;
  font-weight: 500;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

.progress-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  position: relative;
  margin-top: 20px;
}

.feeding-section {
  background: rgba(0, 33, 64, 0.2);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border: 1px solid rgba(0, 145, 255, 0.15);
}

.feeding-section h2 {
  color: #00a8ff;
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

.chart-container {
  flex: 1;
  background: rgba(0, 24, 48, 0.2);
  border: 1px solid rgba(0, 145, 255, 0.1);
  border-radius: 8px;
  padding: 16px;
  min-height: 0;
  position: relative;
  z-index: 1;
}

.photos-section {
  background: rgba(0, 33, 64, 0.2);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border: 1px solid rgba(0, 145, 255, 0.15);
  height: 100%;
  overflow: hidden;
}

.photos-section h2 {
  color: #00a8ff;
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 12px;
  flex: 1;
  min-height: 0;
  height: calc(100% - 40px);
}

.photo-item {
  background: rgba(0, 24, 48, 0.2);
  border: 1px solid rgba(0, 145, 255, 0.1);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 180px;
  overflow: hidden;
}

.photo-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 24, 48, 0.3);
  color: rgba(0, 145, 255, 0.2);
  font-size: 48px;
  padding: 10px;
}

.photo-placeholder :deep(.el-icon) {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.photo-image {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(0, 24, 48, 0.3);
  padding: 4px;
  min-height: 0;
}

.photo-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.photo-info {
  background: rgba(0, 24, 48, 0.3);
  border-top: 1px solid rgba(0, 145, 255, 0.1);
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 36px;
  flex-shrink: 0;
}

.photo-info span {
  color: #e6f7ff;
  font-size: 12px;
}

.console-section {
  background: rgba(0, 33, 64, 0.2);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border: 1px solid rgba(0, 145, 255, 0.15);
  height: 100%;
  overflow: hidden;
}

.console-section h2 {
  color: #00a8ff;
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
  position: relative;
  z-index: 2;
}

.console-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(0, 24, 48, 0.2);
  border: 1px solid rgba(0, 145, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
  min-height: 0;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(0, 24, 48, 0.3);
  border-bottom: 1px solid rgba(0, 145, 255, 0.1);
  position: relative;
  z-index: 2;
}

.console-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  min-height: 0;
  height: calc(100% - 50px);
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  display: flex;
  gap: 12px;
  font-size: 13px;
  line-height: 1.5;
  padding: 8px 12px;
  background: rgba(0, 24, 48, 0.2);
  border-radius: 4px;
}

.log-time {
  color: #00a8ff;
  flex-shrink: 0;
  font-family: monospace;
}

.log-content {
  color: #e6f7ff;
}

body {
  margin: 0;
  padding: 0;
  overflow: hidden;
}

#app {
  height: 100vh;
  overflow: hidden;
}

.report-button {
  margin-right: 16px;
}

:deep(.report-dialog) {
  .el-dialog__body {
    padding: 0;
  }
}

.scale-section {
  margin-top: 20px;
}

.control-section {
  background: rgba(0, 33, 64, 0.2);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border: 1px solid rgba(0, 145, 255, 0.15);
  margin-bottom: 16px;
}

.control-header {
  margin-bottom: 16px;
}

.control-header h2 {
  color: #00a8ff;
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

.control-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  width: 100%;
}

.form-item-half {
  width: 100%;
  margin-bottom: 0;
}

.form-item-half :deep(.el-form-item__content) {
  width: 100%;
  display: flex;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: center;
  color: #00a8ff;
  height: 32px;
  font-size: 16px;
}

:deep(.el-input-number .el-input-number__decrease),
:deep(.el-input-number .el-input-number__increase) {
  background-color: rgba(0, 24, 48, 0.5);
  border-color: rgba(0, 145, 255, 0.15);
  color: #00a8ff;
}

:deep(.el-input-number.is-disabled .el-input__wrapper) {
  background-color: rgba(0, 24, 48, 0.5);
}

:deep(.el-input-number.is-disabled .el-input__inner) {
  color: rgba(0, 168, 255, 0.5);
}

.control-buttons {
  display: flex;
  gap: 12px;
  margin: 8px 0;
  justify-content: space-between;
}

.control-buttons .el-button {
  flex: 1;
  height: 40px;
  border-radius: 4px;
  font-weight: 500;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

/* 元件测试部分的特殊样式 */
.test-form {
  width: 100%;
}

.test-button-container {
  display: flex;
  justify-content: center;
  width: 100%;
  margin: 10px 0;
}

.test-button {
  width: 100%;
  height: 44px !important;
  font-size: 16px !important;
  border-radius: 4px;
  background-color: #409eff;
  border-color: #409eff;
}

.test-button:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

.control-buttons .el-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: all 0.5s;
}

.control-buttons .el-button:hover::before {
  left: 100%;
}

.control-buttons .el-button + .el-button {
  margin-left: 0;
}
</style>
