<template>
  <el-card class="experiment-status">
    <template #header>
      <div class="card-header">
        <span>实验状态监控</span>
        <el-tag :type="status.is_running ? 'success' : 'info'" effect="dark">
          {{ status.is_running ? '运行中' : '已停止' }}
        </el-tag>
      </div>
    </template>

    <!-- 总体进度 -->
    <div class="progress-section">
      <div class="progress-info">
        <span class="label">总体进度</span>
        <span class="value">{{ currentGroup }}/{{ totalGroups }}组</span>
      </div>
      <el-progress
        :percentage="totalProgress"
        :status="status.is_running ? '' : 'success'"
        :stroke-width="20"
        :format="(format) => `${totalProgress}%`"
      />
    </div>

    <!-- 当前组进度 -->
    <div class="progress-section">
      <div class="progress-info">
        <span class="label">当前组进度</span>
        <span class="value">{{ currentPhoto }}/{{ totalPhotos }}张</span>
      </div>
      <el-progress
        :percentage="groupProgress"
        :status="status.is_running ? '' : 'success'"
        :stroke-width="15"
      />
    </div>

    <!-- 状态数据 -->
    <div class="status-grid">
      <div class="status-item">
        <i class="el-icon-time"></i>
        <div class="item-content">
          <div class="item-label">已运行时间</div>
          <div class="item-value">{{ formatTime(elapsedTime) }}</div>
        </div>
      </div>

      <div class="status-item">
        <i class="el-icon-timer"></i>
        <div class="item-content">
          <div class="item-label">预计剩余时间</div>
          <div class="item-value">{{ formatTime(remainingTime) }}</div>
        </div>
      </div>

      <div class="status-item">
        <i class="el-icon-box"></i>
        <div class="item-content">
          <div class="item-label">剩余沙量</div>
          <div class="item-value">{{ remainingSand }}克</div>
        </div>
      </div>

      <div class="status-item">
        <i class="el-icon-camera"></i>
        <div class="item-content">
          <div class="item-label">已拍摄照片</div>
          <div class="item-value">{{ totalPhotosCount }}张</div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: Object,
    required: true
  },
  config: {
    type: Object,
    required: true
  }
})

// 计算属性
const currentGroup = computed(() => props.status.current_group || 0)
const totalGroups = computed(() => props.config.total_groups || 0)
const currentPhoto = computed(() => props.status.current_photo || 0)
const totalPhotos = computed(() => props.config.photos_per_group * 2 || 0)
const remainingSand = computed(() => props.status.remaining_sand || 0)
const elapsedTime = computed(() => props.status.elapsed_time || 0)

const totalProgress = computed(() => {
  if (!totalGroups.value) return 0
  return Math.round((currentGroup.value / totalGroups.value) * 100)
})

const groupProgress = computed(() => {
  if (!totalPhotos.value) return 0
  return Math.round((currentPhoto.value / totalPhotos.value) * 100)
})

const totalPhotosCount = computed(() => {
  return currentGroup.value * totalPhotos.value + currentPhoto.value
})

const remainingTime = computed(() => {
  if (!props.status.is_running || !elapsedTime.value || !currentGroup.value) return 0
  const timePerGroup = elapsedTime.value / currentGroup.value
  return timePerGroup * (totalGroups.value - currentGroup.value)
})

// 格式化时间
const formatTime = (seconds) => {
  if (!seconds) return '0秒'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)

  let result = ''
  if (hours > 0) result += `${hours}小时`
  if (minutes > 0) result += `${minutes}分`
  if (remainingSeconds > 0 || result === '') result += `${remainingSeconds}秒`
  return result
}
</script>

<style scoped>
.experiment-status {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-section {
  margin: 20px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-info .label {
  color: #606266;
  font-size: 14px;
}

.progress-info .value {
  color: #409eff;
  font-weight: 500;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.status-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.status-item i {
  font-size: 24px;
  color: #409eff;
  margin-right: 12px;
}

.item-content {
  flex: 1;
}

.item-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.item-value {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}
</style>
