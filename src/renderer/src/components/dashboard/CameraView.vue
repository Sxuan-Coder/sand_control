<template>
  <div class="camera-view">
    <div class="camera-header">
      <span class="camera-title">{{ title }}</span>
      <div class="camera-status" :class="{ connected: isConnected }">
        {{ isConnected ? '已连接' : '未连接' }}
      </div>
    </div>
    <div class="camera-content" :class="{ offline: !isConnected }">
      <img v-if="streamUrl && isConnected" :src="streamUrl" :alt="title" />
      <div v-else class="no-signal">
        <el-icon><VideoCamera /></el-icon>
        <span>{{ isConnected ? '等待视频流' : '相机离线' }}</span>
      </div>
    </div>
    <div class="camera-footer">
      <div class="camera-info">
        <span>分辨率: {{ resolution }}</span>
        <span>帧率: {{ fps }}fps</span>
      </div>
      <div class="camera-controls">
        <el-button
          size="small"
          type="primary"
          :icon="isRecording ? 'VideoCamera' : 'VideoPlay'"
          @click="toggleRecording"
        >
          {{ isRecording ? '停止录制' : '开始录制' }}
        </el-button>
        <el-button size="small" type="success" icon="Camera" @click="takeSnapshot">
          拍照
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera, VideoPlay, Camera } from '@element-plus/icons-vue'

export default {
  name: 'CameraView',
  components: {
    VideoCamera,
    VideoPlay,
    Camera
  },
  props: {
    title: {
      type: String,
      required: true
    },
    streamUrl: {
      type: String,
      default: ''
    },
    isConnected: {
      type: Boolean,
      default: false
    },
    resolution: {
      type: String,
      default: '1920x1080'
    },
    fps: {
      type: Number,
      default: 30
    }
  },
  setup(props, { emit }) {
    const isRecording = ref(false)

    const takeSnapshot = () => {
      if (!props.isConnected) {
        ElMessage.warning('相机未连接')
        return
      }
      emit('snapshot')
      ElMessage.success('已拍照')
    }

    const toggleRecording = () => {
      if (!props.isConnected) {
        ElMessage.warning('相机未连接')
        return
      }
      isRecording.value = !isRecording.value
      emit('record', isRecording.value)
      ElMessage.success(isRecording.value ? '开始录制' : '停止录制')
    }

    return {
      isRecording,
      takeSnapshot,
      toggleRecording
    }
  }
}
</script>

<style scoped>
.camera-view {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.4);
  height: 32px;
}

.camera-title {
  font-size: 13px;
  font-weight: bold;
}

.camera-status {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  background: rgba(255, 0, 0, 0.2);
  border: 1px solid rgba(255, 0, 0, 0.3);
  color: #ff4d4f;
}

.camera-status.connected {
  background: rgba(0, 255, 0, 0.2);
  border: 1px solid rgba(0, 255, 0, 0.3);
  color: #52c41a;
}

.camera-content {
  position: relative;
  flex: 1;
  min-height: 0;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-content img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-content.offline {
  background: #1a1a1a;
}

.no-signal {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
}

.no-signal .el-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.no-signal span {
  display: block;
  font-size: 13px;
}

.camera-footer {
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 32px;
}

.camera-info {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.camera-info span {
  margin-right: 8px;
}

.camera-controls {
  display: flex;
  gap: 6px;
}

:deep(.el-button--small) {
  padding: 3px 8px;
  font-size: 12px;
  height: 24px;
}

:deep(.el-button--primary) {
  background: #1890ff;
  border-color: #1890ff;
}

:deep(.el-button--success) {
  background: #52c41a;
  border-color: #52c41a;
}
</style>
