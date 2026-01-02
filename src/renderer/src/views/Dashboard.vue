<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div class="header-left">
        <h1>砂石级配实验监控平台</h1>
        <div class="system-status" :class="{ 'status-running': isRunning }">
          系统{{ isRunning ? '运行中' : '已停止' }}
        </div>
        <!-- 系统监控指标 -->
        <div class="system-monitors">
          <div class="monitor-item">
            <el-icon class="monitor-icon cpu-icon"><Monitor /></el-icon>
            <div class="monitor-content">
              <span class="monitor-label">CPU</span>
              <span class="monitor-value">{{ cpuUsage }}%</span>
            </div>
          </div>
          <div class="monitor-item">
            <el-icon class="monitor-icon memory-icon"><Connection /></el-icon>
            <div class="monitor-content">
              <span class="monitor-label">内存</span>
              <span class="monitor-value">{{ memoryUsage }}</span>
            </div>
          </div>
          <div class="monitor-item">
            <el-icon class="monitor-icon delay-icon"><VideoCamera /></el-icon>
            <div class="monitor-content">
              <span class="monitor-label">延迟</span>
              <span class="monitor-value">{{ networkDelay }}ms</span>
            </div>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-button type="info" @click="showImageProcessing" class="report-button">
          <el-icon><Picture /></el-icon>
          图像处理展示
        </el-button>
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
                    :max="1000"
                    :disabled="isRunning"
                    controls-position="right"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-form-item label="每组照片" class="form-item-half">
                  <el-input-number
                    v-model="photosPerGroup"
                    :min="1"
                    :max="1000"
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

          <div class="console-section">
            <h2>控制台监控</h2>
            <div class="console-container">
              <div class="console-header">
                <div class="console-tabs">
                  <div class="tab active" style="color: #ccc;">系统日志</div>
                  <div class="tab" style="color: #ccc;">运行状态</div>
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

        <div class="bottom-row">
          <div class="photos-section" style="margin-top: 50px;">
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
                  <div class="photo-type-tag" :class="{ 'global': index % 2 === 0, 'local': index % 2 === 1 }">
                    {{ index % 2 === 0 ? '全局图像' :  '局部图像'}}
                  </div>
                </div>
                <div class="photo-info">
                  <span>组{{ photo.group }} - 照片{{ photo.photo }} {{ photo.time }}</span>
                
                </div>
              </div>
            </div>
          </div>

          <!-- 暂时注释给料状态
          <div class="feeding-section">
            <h2>给料状态</h2>
            <div class="chart-container">
              <feeding-chart :data="feedingData" />
            </div>
          </div>
          -->
          <div class="section-container">
              <div class="section-header" style="margin-top: 50px;">
                  <h3>设备模型</h3>
              </div>
              <div style="height: 450px">
                  <EquipmentModel />
              </div>
              <div class="progress-bar">
                  <div class="progress" :style="{ width: modelProgress + '%' }"></div>
                  
              </div>
              <h2 style="justify-content: center;text-align: center;color: orange;">实验进度</h2>
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
  testServerConnection,
  getSystemMonitor
} from '../api'
import EquipmentModel from '../components/EquipmentModel.vue'

// 获取API基础URL
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : window.location.origin;

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
    EquipmentModel,
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

    // 系统监控指标
    const cpuUsage = ref(43)
    const memoryUsage = ref('2.56')
    const networkDelay = ref(38)

    // 实验参数
    const dataPath = ref('F:/sand_data/test')
    const totalGroups = ref(5)
    const photosPerGroup = ref(5)
    const feedingAmount = ref(2)

    // 进度数据
    const completedGroups = ref(0)
    const currentPhoto = ref(0)
    const elapsedTime = ref(0)
    const feedingData = ref([])

    // 计算模型进度
    const modelProgress = computed(() => {
      if (!totalGroups.value) return 0
      return Math.round((completedGroups.value / totalGroups.value) * 100)
    })

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
    const imageRefreshInterval = ref(2000)

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

    // 实验进度计算
    const experimentProgress = computed(() => {
      const totalPhotos = totalGroups.value * photosPerGroup.value;
      const completedPhotos = completedGroups.value * photosPerGroup.value + currentPhoto.value;
      // 确保进度不会超过100%
      return Math.min(Math.floor((completedPhotos / totalPhotos) * 100), 100);
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
          start_group: 1, 
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
      // 使用时间因子生成相似波形
      const time = Date.now() / 1000
      // 使用正弦波作为基础，加入小幅度随机波动
      const amplitude = 0.2 // 波动幅度
      const frequency = 0.5 // 频率
      const baseWave = Math.sin(time * frequency) * amplitude
      // 添加小幅度随机波动，保持波形相似性
      const noise = (Math.random() - 0.5) * 0.05
      const value = baseValue + baseWave + noise

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
        // console.log('开始加载本地图片...');
        
        // 更新图片路径
        globalImagesPath.value = `${dataPath.value}/global`;
        localImagesPath.value = `${dataPath.value}/local`;
        
        // 创建Promise数组，同时请求global和local图片
        const [globalResponse, localResponse] = await Promise.all([
          getDirectoryImages(globalImagesPath.value),
          getDirectoryImages(localImagesPath.value)
        ]);
        
        const globalFiles = globalResponse.data || [];
        const localFiles = localResponse.data || [];
        
        // console.log(`找到全局图片: ${globalFiles.length}张, 本地图片: ${localFiles.length}张`);
        
        // 处理全局图片
        const globalImages = globalFiles.map(file => {
          const fileNameMatch = file.name.match(/(\d+)_(\d+)\.jpg$/i) || [];
          return {
            path: file.path,
            actualPath: file.path,
            group: parseInt(fileNameMatch[1]) || 0,
            photo: parseInt(fileNameMatch[2]) || 0,
            source: 'global',
            time: file.modifiedTime
          };
        }).filter(img => img.group > 0 && img.photo > 0);
        
        // 处理本地图片
        const localImages = localFiles.map(file => {
          const fileNameMatch = file.name.match(/(\d+)_(\d+)\.jpg$/i) || [];
          return {
            path: file.path,
            actualPath: file.path,
            group: parseInt(fileNameMatch[1]) || 0,
            photo: parseInt(fileNameMatch[2]) || 0,
            source: 'local',
            time: file.modifiedTime
          };
        }).filter(img => img.group > 0 && img.photo > 0);
        
        // 合并并优先按照时间排序
        const allImages = [...globalImages, ...localImages].sort((a, b) => {
          // 首先按照修改时间排序（降序）
          const timeA = new Date(a.time).getTime();
          const timeB = new Date(b.time).getTime();
          if (timeA !== timeB) return timeB - timeA;
          
          // 时间相同时，按组号排序（降序）
          if (a.group !== b.group) return b.group - a.group;
          
          // 组号相同时，按照照片号排序（降序）
          if (a.photo !== b.photo) return b.photo - a.photo;
          
          // 最后按来源排序，让local排在global后面
          return a.source === 'global' ? -1 : 1;
        });
        
        // 更新缓存
        cachedImages.value = allImages;
        
        if (allImages.length === 0) {
          console.log('未找到有效图片');
          addLog(`未找到图片。查找路径: ${globalImagesPath.value} 和 ${localImagesPath.value}`, 'warning');
        } else {
          // 按组分类日志输出
          const groupedImages = allImages.reduce((acc, img) => {
            const key = `组${img.group}`;
            if (!acc[key]) acc[key] = [];
            acc[key].push(`${img.source}_${img.photo}`);
            return acc;
          }, {});
          
          Object.entries(groupedImages).forEach(([group, photos]) => {
            console.log(`${group}: ${photos.join(', ')}`);
          });
          
          addLog(`成功加载 ${allImages.length} 张图片（全局：${globalImages.length}，本地：${localImages.length}）`, 'success');

          // 根据加载的图片更新进度
          const totalExpectedPhotos = totalGroups.value * photosPerGroup.value;
          const currentTotalPhotos = Math.max(globalImages.length, localImages.length);
          
          // 更新进度
          completedGroups.value = Math.floor(currentTotalPhotos / photosPerGroup.value);
          currentPhoto.value = currentTotalPhotos % photosPerGroup.value;
          
          // 确保不超过总数
          if (completedGroups.value >= totalGroups.value) {
            completedGroups.value = totalGroups.value;
            currentPhoto.value = photosPerGroup.value;
            isRunning.value = false;
            addLog('实验已完成', 'success');
          }
        }
        
        return allImages;
      } catch (error) {
        console.error('加载图片失败:', error);
        addLog('加载图片失败: ' + error.message, 'error');
        return [];
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
    const updateLatestPhotos = async () => {
      try {
        // console.log('开始刷新图片显示...');
        
        // 重新加载最新的图片
        const images = await loadLocalImages();
        
        if (images.length === 0) {
          latestPhotos.value = Array(4).fill({
            path: '',
            group: 0,
            photo: 0,
            time: new Date().toLocaleTimeString()
          });
          console.log('没有找到图片，使用空占位符');
          return;
        }

        // 按组和照片编号对图片进行分组
        const imageGroups = {};
        images.forEach(img => {
          const key = `${img.group}_${img.photo}`;
          if (!imageGroups[key]) {
            imageGroups[key] = {};
          }
          imageGroups[key][img.source] = img;
        });

        // 获取所有完整的图片对
        const completePairs = Object.entries(imageGroups)
          .filter(([_, group]) => group.global && group.local)
          .map(([key, group]) => ({
            key: key,
            global: group.global,
            local: group.local,
            // 使用最新的时间（global和local中较新的时间）
            latestTime: new Date(Math.max(
              new Date(group.global.time).getTime(),
              new Date(group.local.time).getTime()
            ))
          }))
          .sort((a, b) => {
            // 首先按最新时间排序
            const timeComparison = b.latestTime.getTime() - a.latestTime.getTime();
            if (timeComparison !== 0) return timeComparison;
            
            // 时间相同时才考虑组号和照片号
            const [aGroup, aPhoto] = a.key.split('_').map(Number);
            const [bGroup, bPhoto] = b.key.split('_').map(Number);
            if (aGroup !== bGroup) return bGroup - aGroup;
            return bPhoto - aPhoto;
          });

        // console.log('找到的完整图片对:', 
        //   completePairs.map(p => {
        //     const [group, photo] = p.key.split('_');
        //     return `组${group}照片${photo}(${p.latestTime.toLocaleTimeString()})`;
        //   }).join(', '));

        // 选择最新的两组图片对并构建显示数组
        const orderedPhotos = [];
        completePairs.slice(0, 2).forEach(pair => {
          // 确保每对中global在前，local在后
          if (pair.global) {
            orderedPhotos.push({
              ...pair.global,
              path: getImageUrl(pair.global.path)
            });
          }
          if (pair.local) {
            orderedPhotos.push({
              ...pair.local,
              path: getImageUrl(pair.local.path)
            });
          }
        });

        // 填充空位
        while (orderedPhotos.length < 4) {
          orderedPhotos.unshift({
            path: '',
            group: 0,
            photo: 0,
            time: new Date().toLocaleTimeString()
          });
        }

        // 更新显示
        latestPhotos.value = orderedPhotos.map(img => ({
          path: img.path || '',
          actualPath: img.actualPath || '',
          group: img.group || 0,
          photo: img.photo || 0,
          source: img.source || '',
          time: new Date(img.time).toLocaleTimeString()
        }));

        // 记录图片更新日志
        const logMessage = orderedPhotos
          .filter(img => img.source)
          .map(img => `${img.source}/${img.group}_${img.photo}`)
          .join(', ');

        if (logMessage) {
          // console.log('当前显示的图片:', logMessage);
          addLog(`图片更新成功: ${logMessage}`, 'success');
        }
      } catch (error) {
        console.error('获取图片失败:', error);
        addLog('获取图片失败: ' + error.message, 'error');
        
        latestPhotos.value = Array(4).fill({
          path: '',
          group: 0,
          photo: 0,
          time: new Date().toLocaleTimeString()
        });
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

    const showImageProcessing = async () => {
      try {
        // 调用主进程打开新窗口
        await window.api.ipcRenderer.invoke('open-image-processing-window')
        addLog('打开图像处理窗口', 'info')
      } catch (error) {
        ElMessage.error('打开图像处理窗口失败')
        addLog('打开图像处理窗口失败: ' + error.message, 'error')
      }
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
          const store = useStore()
          const router = useRouter()

          // 计算实验进度
          const modelProgress = computed(() => {
            const status = store.state.systemStatus
            if (!status || !status.current_config || !status.current_config.total_groups) return 0
            return Math.round((status.current_group / status.current_config.total_groups) * 100)
          })

          router.push('/login')
        })
        .catch(() => {
          // 取消登出
        })
    }

    // 启动一个单独的定时器以自动更新照片
    let timer
    let imageRefreshTimer

    // 更新系统监控指标
    const updateSystemMonitors = async () => {
      try {
        // 调用后端API获取真实系统监控数据
        const data = await getSystemMonitor()
        
        // 更新CPU使用率
        cpuUsage.value = data.cpu_usage
        
        // 更新内存使用量
        memoryUsage.value = data.memory_usage.toFixed(2)
        
        // 更新网络延迟
        networkDelay.value = data.network_delay
      } catch (error) {
        console.error('获取系统监控数据失败:', error)
        // 失败时使用模拟数据
        cpuUsage.value = Math.floor(40 + Math.random() * 15)
        memoryUsage.value = (2.3 + Math.random() * 0.9).toFixed(2)
        networkDelay.value = Math.floor(25 + Math.random() * 35)
      }
    }

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
        // 更新系统监控指标（每秒都更新）
        updateSystemMonitors()
        
        if (isRunning.value) {
          updateFeedingData()
          elapsedTime.value++

          // 更新实验进度 - 现在只在相机拍摄完成后更新
          // 检查系统日志中是否有相机拍摄完成的记录
          const latestLog = systemLogs.value[0];
          if (latestLog && latestLog.content === '相机拍摄完成' && latestLog.type === 'success') {
            // 更新当前照片计数
            if (currentPhoto.value < photosPerGroup.value - 1) {
              currentPhoto.value++
            } else {
              currentPhoto.value = 0;
              if (completedGroups.value < totalGroups.value - 1) {
                completedGroups.value++
              } else if (completedGroups.value === totalGroups.value - 1) {
                // 最后一组完成时的处理
                completedGroups.value = totalGroups.value;
                currentPhoto.value = photosPerGroup.value;
                isRunning.value = false;
                addLog('实验已完成', 'success');
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
      modelProgress,
      isRunning,
      isInitialized,
      cameraConnected,
      controllerConnected,
      sensorConnected,
      light_status,

      // 系统监控指标
      cpuUsage,
      memoryUsage,
      networkDelay,

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
      showImageProcessing,
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
  padding: 10px;
  gap: 10px;
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
  padding: 0 20px;
  height: 50px;
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

/* 系统监控指标样式 */
.system-monitors {
  display: flex;
  gap: 20px;
  align-items: center;
}

.monitor-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(0, 24, 48, 0.4);
  border: 1px solid rgba(0, 145, 255, 0.2);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.monitor-item:hover {
  background: rgba(0, 24, 48, 0.6);
  border-color: rgba(0, 145, 255, 0.4);
  box-shadow: 0 0 10px rgba(0, 145, 255, 0.2);
}

.monitor-icon {
  font-size: 20px;
}

.cpu-icon {
  color: #00a8ff;
}

.memory-icon {
  color: #52c41a;
}

.delay-icon {
  color: #faad14;
}

.monitor-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1;
}

.monitor-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 400;
}

.monitor-value {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 600;
  font-family: 'Consolas', 'Monaco', monospace;
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
  padding: 16px;
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
  grid-template-rows: repeat(2, minmax(150px, 1fr));
  gap: 16px;
  flex: 1;
  min-height: 0;
  height: calc(100% - 30px);
  margin-top: 2px;
  overflow-y: auto;
}

.photo-item {
  background: rgba(0, 24, 48, 0.2);
  border: 1px solid rgba(0, 145, 255, 0.1);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 150px;
  overflow: hidden;
}

.photo-wrapper {
  width: 100%;
  height: 200px;
  overflow: hidden;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
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
  height: calc(100% - 50px);
  position: relative;
}

.photo-type-tag {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
  z-index: 2;
}

.photo-type-tag.global {
  background-color: rgba(0, 145, 255, 0.8);
}

.photo-type-tag.local {
  background-color: rgba(0, 200, 83, 0.8);
  z-index: 3;
}

.photo-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  position: relative;
  z-index: 1;
}

.photo-info {
  padding: 6px 8px;
  background: rgba(0, 24, 48, 0.4);
  border-top: 1px solid rgba(0, 145, 255, 0.1);
  height: 50px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
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
  gap: 8px;
}

.control-form .el-form-item {
  margin-bottom: 8px;
}

.control-form .el-form-item__content {
  margin-left: 8px !important;
}

.control-form .el-button {
  margin-left: 8px;
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

.section-container {
  margin-top: 16px;
}

.section-header {
  margin-bottom: 12px;
}

.section-header h3 {
  font-size: 16px;
  color: #e6e6e6;
  margin: 0;
}

.section-header .photo-info span {
  font-size: 12px;
  color: #ffffff80;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 8px;
}

.progress {
  height: 100%;
  background: #67c23a;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(103, 194, 58, 0.5);
}
</style>
