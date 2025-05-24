<template>
  <div class="clean-sand-control">
    <div class="control-header">
      <h3>清砂控制</h3>
      <el-tag :type="statusType" effect="dark">{{ statusText }}</el-tag>
    </div>

    <div class="control-body">
      <div class="control-options">
        <el-form :model="cleanOptions" label-width="100px" size="small">
          <el-form-item label="测试循环次数">
            <el-input-number
              v-model="cleanOptions.testCycles"
              :min="1"
              :max="10"
              :disabled="cleaning"
            />
          </el-form-item>
        </el-form>
      </div>

      <div class="control-actions">
        <el-button
          type="primary"
          :icon="Brush"
          :loading="cleaning"
          @click="startCleanSand"
          :disabled="cleaning"
        >
          开始清砂
        </el-button>

        <el-button type="danger" :icon="CircleClose" @click="stopCleanSand" :disabled="!cleaning">
          停止清砂
        </el-button>
      </div>
    </div>

    <div class="control-logs" v-if="logs.length > 0">
      <h4>操作日志</h4>
      <div class="logs-container">
        <p v-for="(log, index) in logs" :key="index" :class="{ 'error-log': log.type === 'error' }">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-message">{{ log.message }}</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Brush, CircleClose } from '@element-plus/icons-vue'
import { cleanSand, getCleanStatus, stopCleanProcess } from '../api'

// 清砂状态
const status = ref('idle') // idle, cleaning, error
const cleaning = ref(false)
const logs = ref([])
const statusCheckInterval = ref(null)

// 清砂选项
const cleanOptions = ref({
  testCycles: 1,
  testMode: false
})

// 计算属性
const statusText = computed(() => {
  switch (status.value) {
    case 'idle':
      return '空闲'
    case 'cleaning':
      return '清砂中'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
})

const statusType = computed(() => {
  switch (status.value) {
    case 'idle':
      return 'info'
    case 'cleaning':
      return 'success'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
})

// 添加日志
const addLog = (message, type = 'info') => {
  const now = new Date()
  const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`

  logs.value.unshift({
    time: timeStr,
    message,
    type
  })

  // 最多保留20条日志
  if (logs.value.length > 20) {
    logs.value.pop()
  }
}

// 开始清砂
const startCleanSand = async () => {
  try {
    // 确认操作
    await ElMessageBox.confirm('确定要开始清砂操作吗？', '操作确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    cleaning.value = true
    status.value = 'cleaning'
    addLog(`开始清砂操作，循环次数: ${cleanOptions.value.testCycles}`)

    // 调用清砂API
    const response = await cleanSand({
      testCycles: cleanOptions.value.testCycles,
      testMode: cleanOptions.value.testMode
    })

    // 开始定时检查状态
    startStatusCheck()

    ElMessage.success('清砂操作已开始')
  } catch (error) {
    if (error !== 'cancel') {
      status.value = 'error'
      addLog(`清砂操作失败: ${error.message || '未知错误'}`, 'error')
      ElMessage.error(`清砂操作失败: ${error.message || '未知错误'}`)
      cleaning.value = false
    }
  }
}

// 停止清砂
const stopCleanSand = async () => {
  try {
    // 确认操作
    await ElMessageBox.confirm('确定要停止清砂操作吗？', '操作确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    addLog('正在停止清砂操作...')

    // 调用停止清砂API
    await stopCleanProcess()

    cleaning.value = false
    status.value = 'idle'
    addLog('清砂操作已停止')
    ElMessage.info('清砂操作已停止')

    // 停止状态检查
    stopStatusCheck()
  } catch (error) {
    if (error !== 'cancel') {
      addLog(`停止清砂操作失败: ${error.message || '未知错误'}`, 'error')
      ElMessage.error(`停止清砂操作失败: ${error.message || '未知错误'}`)
    }
  }
}

// 开始状态检查
const startStatusCheck = () => {
  // 每3秒检查一次状态
  statusCheckInterval.value = setInterval(async () => {
    try {
      const statusData = await getCleanStatus()

      // 更新状态
      if (statusData.status === 'completed') {
        cleaning.value = false
        status.value = 'idle'
        addLog('清砂操作已完成')
        ElMessage.success('清砂操作已完成')
        stopStatusCheck()
      } else if (statusData.status === 'error') {
        cleaning.value = false
        status.value = 'error'
        addLog(`清砂操作出错: ${statusData.message || '未知错误'}`, 'error')
        ElMessage.error(`清砂操作出错: ${statusData.message || '未知错误'}`)
        stopStatusCheck()
      } else if (statusData.status === 'cleaning') {
        // 如果有进度信息，添加到日志
        if (statusData.progress) {
          addLog(`清砂进度: ${statusData.progress}`)
        }
      }
    } catch (error) {
      console.error('获取清砂状态失败:', error)
    }
  }, 3000)
}

// 停止状态检查
const stopStatusCheck = () => {
  if (statusCheckInterval.value) {
    clearInterval(statusCheckInterval.value)
    statusCheckInterval.value = null
  }
}

// 组件挂载时检查状态
onMounted(async () => {
  try {
    const statusData = await getCleanStatus()

    // 如果正在清砂，更新状态
    if (statusData.status === 'cleaning') {
      cleaning.value = true
      status.value = 'cleaning'
      addLog('检测到正在进行的清砂操作')
      startStatusCheck()
    }
  } catch (error) {
    console.error('获取清砂状态失败:', error)
  }
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopStatusCheck()
})
</script>

<style scoped>
.clean-sand-control {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.control-header h3 {
  margin: 0;
  color: #303133;
}

.control-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-actions {
  display: flex;
  gap: 12px;
}

.control-logs {
  margin-top: 16px;
  border-top: 1px solid #e4e7ed;
  padding-top: 12px;
}

.control-logs h4 {
  margin: 0 0 8px 0;
  color: #606266;
}

.logs-container {
  max-height: 200px;
  overflow-y: auto;
  background-color: #fafafa;
  border-radius: 4px;
  padding: 8px;
}

.logs-container p {
  margin: 4px 0;
  font-size: 12px;
  line-height: 1.5;
  color: #606266;
}

.log-time {
  color: #909399;
  margin-right: 8px;
}

.error-log {
  color: #f56c6c !important;
}

.error-log .log-time {
  color: #f56c6c;
  opacity: 0.8;
}
</style>
