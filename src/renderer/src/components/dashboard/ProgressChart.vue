<template>
  <div class="progress-chart">
    <div class="progress-circle">
      <svg viewBox="0 0 100 100">
        <!-- 背景圆环 -->
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="rgba(0, 145, 255, 0.1)"
          stroke-width="6"
        />
        <!-- 进度圆环 -->
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="url(#progressGradient)"
          stroke-width="6"
          stroke-linecap="round"
          :stroke-dasharray="progressArray"
          :stroke-dashoffset="progressOffset"
          transform="rotate(-90 50 50)"
        />
        <!-- 渐变定义 -->
        <defs>
          <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#00a8ff" />
            <stop offset="100%" stop-color="#0091ff" />
          </linearGradient>
        </defs>
      </svg>
      <!-- 进度文字 -->
      <div class="progress-text">
        <span class="value">{{ typeof progress === 'number' ? Math.round(progress) : 0 }}%</span>
        <span class="label">实验进度</span>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'ProgressChart',
  props: {
    progress: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const chartRef = ref(null)
    let resizeObserver = null

    const circumference = 2 * Math.PI * 45
    const progressArray = computed(() => `${circumference} ${circumference}`)
    const progressOffset = computed(() => {
      // 确保 progress 是数字，如果不是则使用 0
      const progressValue = typeof props.progress === 'number' ? props.progress : 0
      return circumference - (progressValue / 100) * circumference
    })

    onMounted(() => {
      if (chartRef.value) {
        resizeObserver = new ResizeObserver((entries) => {
          requestAnimationFrame(() => {
            for (const entry of entries) {
              if (entry.target === chartRef.value) {
                // Handle resize if needed
                // Add your resize logic here
              }
            }
          })
        })
        resizeObserver.observe(chartRef.value)
      }
    })

    onUnmounted(() => {
      if (resizeObserver) {
        resizeObserver.disconnect()
        resizeObserver = null
      }
    })

    return {
      progressArray,
      progressOffset,
      chartRef
    }
  }
}
</script>

<style scoped>
.progress-chart {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 24, 48, 0.3);
  border-radius: 8px;
  position: relative;
}

.progress-circle {
  position: relative;
  width: 140px;
  height: 140px;
}

.progress-circle svg {
  width: 100%;
  height: 100%;
  transform: rotate(0deg);
  filter: drop-shadow(0 0 8px rgba(0, 168, 255, 0.3));
}

circle {
  transition: stroke-dashoffset 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #00a8ff;
  width: 100%;
  z-index: 2;
}

.progress-text .value {
  font-size: 28px;
  font-weight: 600;
  text-shadow: 0 0 15px rgba(0, 168, 255, 0.5);
  display: block;
  line-height: 1.2;
  margin-bottom: 4px;
  color: #fff;
  background: linear-gradient(180deg, #fff 0%, #00a8ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.progress-text .label {
  font-size: 13px;
  color: #8b9eb0;
  display: block;
  font-weight: 500;
  text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
}

@keyframes glow {
  0% {
    text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
  }
  50% {
    text-shadow: 0 0 20px rgba(0, 168, 255, 0.8);
  }
  100% {
    text-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
  }
}

.progress-text .value {
  animation: glow 2s infinite;
}
</style>
