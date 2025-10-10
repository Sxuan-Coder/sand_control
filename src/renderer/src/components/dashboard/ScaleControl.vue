<template>
  <div class="scale-control">
    <div class="scale-header">
      <h2>高精度压力传感器</h2>
      <div class="scale-status" :class="{ connected: scaleStatus.is_connected }">
        {{ scaleStatus.is_connected ? '已连接' : '未连接' }}
      </div>
    </div>

    <!-- 连接控制 -->
    <div class="control-section">
      <div class="port-select" v-if="!scaleStatus.is_connected">
        <el-select v-model="selectedPort" placeholder="选择串口">
          <el-option v-for="port in availablePorts" :key="port" :label="port" :value="port" />
        </el-select>
        <el-button type="primary" @click="handleConnect" :loading="connecting"> 连接 </el-button>
      </div>
      <el-button v-else type="danger" @click="handleDisconnect" :loading="disconnecting">
        断开连接
      </el-button>
    </div>

    <!-- 重量显示 -->
    <div class="weight-display" v-if="scaleStatus.is_connected">
      <div class="weight-value">
        {{ currentWeight === null ? '--' : (currentWeight / 1000).toFixed(3) }}
        <span class="weight-unit">g</span>
      </div>
      <div class="weight-label">当前重量</div>
    </div>

    <!-- 校准控制 -->
    <div class="calibration-section" v-if="scaleStatus.is_connected">
      <div class="calibration-controls">
        <el-button @click="handleZeroCalibration" :loading="calibrating"> 零点校准 </el-button>
        <el-button @click="showGainCalibration" :loading="calibrating"> 增益校准 </el-button>
      </div>
      <div class="last-calibration" v-if="scaleStatus.last_calibration">
        上次校准: {{ scaleStatus.last_calibration }}
      </div>
    </div>

    <!-- 增益校准对话框 -->
    <el-dialog
      v-model="gainDialogVisible"
      title="增益校准"
      width="400px"
      append-to-body
      :modal="true"
      :close-on-click-modal="false"
      :z-index="2000"
      destroy-on-close
    >
      <el-form :model="calibrationForm" label-width="100px">
        <el-form-item label="校准重量(g)">
          <el-input-number v-model="calibrationForm.weight" :precision="3" :step="0.1" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="gainDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleGainCalibration" :loading="calibrating">
            确认校准
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getScalePorts,
  getScaleStatus,
  connectScale,
  disconnectScale,
  calibrateZero,
  calibrateGain,
  getWeight
} from '../../api'

export default {
  name: 'ScaleControl',
  setup() {
    const availablePorts = ref([])
    const selectedPort = ref('')
    const scaleStatus = ref({
      is_connected: false,
      port: null,
      current_weight: null,
      last_calibration: null
    })
    const currentWeight = ref(null)
    const connecting = ref(false)
    const disconnecting = ref(false)
    const calibrating = ref(false)
    const gainDialogVisible = ref(false)
    const calibrationForm = ref({
      weight: 1.24
    })
    let weightInterval = null

    // 获取可用串口
    const fetchPorts = async () => {
      try {
        const response = await getScalePorts()
        availablePorts.value = response.available_ports
      } catch (error) {
        ElMessage.error('获取串口列表失败')
        console.error('获取串口列表失败:', error)
      }
    }

    // 获取电子秤状态
    const fetchStatus = async () => {
      try {
        const response = await getScaleStatus()
        scaleStatus.value = response
        if (response.is_connected) {
          startWeightPolling()
        }
      } catch (error) {
        ElMessage.error('获取电子秤状态失败')
        console.error('获取电子秤状态失败:', error)
      }
    }

    // 连接电子秤
    const handleConnect = async () => {
      if (!selectedPort.value) {
        ElMessage.warning('请选择串口')
        return
      }

      connecting.value = true
      try {
        await connectScale(selectedPort.value)
        await fetchStatus()
        ElMessage.success('连接成功')
        startWeightPolling()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '连接失败')
        console.error('连接失败:', error)
      } finally {
        connecting.value = false
      }
    }

    // 断开连接
    const handleDisconnect = async () => {
      disconnecting.value = true
      try {
        await disconnectScale()
        stopWeightPolling()
        await fetchStatus()
        ElMessage.success('已断开连接')
      } catch (error) {
        ElMessage.error('断开连接失败')
      } finally {
        disconnecting.value = false
      }
    }

    // 零点校准
    const handleZeroCalibration = async () => {
      calibrating.value = true
      try {
        await calibrateZero()
        await fetchStatus()
        ElMessage.success('零点校准完成')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '校准失败')
      } finally {
        calibrating.value = false
      }
    }

    // 显示增益校准对话框
    const showGainCalibration = () => {
      gainDialogVisible.value = true
    }

    // 增益校准
    const handleGainCalibration = async () => {
      calibrating.value = true
      try {
        await calibrateGain(calibrationForm.value.weight)
        await fetchStatus()
        gainDialogVisible.value = false
        ElMessage.success('增益校准完成')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '校准失败')
      } finally {
        calibrating.value = false
      }
    }

    // 开始重量轮询
    const startWeightPolling = () => {
      stopWeightPolling()
      weightInterval = setInterval(async () => {
        try {
          const response = await getWeight()
          currentWeight.value = response.weight
        } catch (error) {
          console.error('获取重量失败:', error)
        }
      }, 500)
    }

    // 停止重量轮询
    const stopWeightPolling = () => {
      if (weightInterval) {
        clearInterval(weightInterval)
        weightInterval = null
      }
    }

    onMounted(() => {
      fetchPorts()
      fetchStatus()
    })

    onUnmounted(() => {
      stopWeightPolling()
    })

    return {
      availablePorts,
      selectedPort,
      scaleStatus,
      currentWeight,
      connecting,
      disconnecting,
      calibrating,
      gainDialogVisible,
      calibrationForm,
      handleConnect,
      handleDisconnect,
      handleZeroCalibration,
      showGainCalibration,
      handleGainCalibration
    }
  }
}
</script>

<style scoped>
.scale-control {
  background: rgba(0, 33, 64, 0.2);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid rgba(0, 145, 255, 0.15);
}

.control-section {
  margin: 8px 0;
}

.calibration-section {
  margin: 8px 0;
}

.weight-display {
  margin: 12px 0;
}

.el-form-item {
  margin-bottom: 12px;
}

.scale-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.scale-header h2 {
  color: #00a8ff;
  font-size: 18px;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

.scale-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  background: rgba(245, 108, 108, 0.1);
  border: 1px solid rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

.scale-status.connected {
  background: rgba(103, 194, 58, 0.1);
  border-color: rgba(103, 194, 58, 0.2);
  color: #67c23a;
}

.control-section {
  margin-bottom: 20px;
}

.port-select {
  display: flex;
  gap: 12px;
}

.port-select :deep(.el-select) {
  flex: 1;
}

.weight-display {
  background: rgba(0, 24, 48, 0.3);
  border: 1px solid rgba(0, 145, 255, 0.15);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  margin-bottom: 20px;
}

.weight-value {
  font-size: 36px;
  color: #00a8ff;
  text-shadow: 0 0 15px rgba(0, 168, 255, 0.5);
  margin-bottom: 8px;
}

.weight-unit {
  font-size: 20px;
  margin-left: 4px;
  color: #8b9eb0;
}

.weight-label {
  color: #8b9eb0;
  font-size: 14px;
}

.calibration-section {
  background: rgba(0, 24, 48, 0.3);
  border: 1px solid rgba(0, 145, 255, 0.15);
  border-radius: 8px;
  padding: 20px;
}

.calibration-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.last-calibration {
  color: #8b9eb0;
  font-size: 13px;
  text-align: center;
}

:deep(.el-input__wrapper),
:deep(.el-select .el-input__wrapper) {
  background: rgba(0, 24, 48, 0.4) !important;
  border: 1px solid rgba(0, 145, 255, 0.15) !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  color: #e6f7ff !important;
}

:deep(.el-select-dropdown__item) {
  color: #e6f7ff;
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item:hover) {
  background: rgba(0, 145, 255, 0.1);
}

:deep(.el-select-dropdown__item.selected) {
  background: rgba(0, 145, 255, 0.2);
  color: #00a8ff;
}
</style>
