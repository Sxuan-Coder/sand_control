<template>
  <div class="feeding-chart" ref="chartRef"></div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'FeedingChart',
  props: {
    data: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      chart: null,
      resizeTimeout: null
    }
  },
  methods: {
    initChart() {
      if (!this.$refs.chartRef) return

      this.chart = echarts.init(this.$refs.chartRef)
      this.updateChart()

      window.addEventListener('resize', this.handleResize)
    },
    updateChart() {
      if (!this.chart) return

      const option = {
        grid: {
          top: 30,
          right: 20,
          bottom: 30,
          left: 50,
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: this.data.map((item) => item.time),
          axisLine: {
            lineStyle: {
              color: 'rgba(139, 158, 176, 0.3)'
            }
          },
          axisLabel: {
            color: '#8b9eb0',
            fontSize: 12,
            interval: Math.floor(this.data.length / 5)
          },
          splitLine: {
            show: true,
            lineStyle: {
              color: 'rgba(139, 158, 176, 0.1)'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '给料量(g)',
          nameTextStyle: {
            color: '#8b9eb0',
            fontSize: 12,
            padding: [0, 30, 0, 0]
          },
          axisLine: {
            lineStyle: {
              color: 'rgba(139, 158, 176, 0.3)'
            }
          },
          axisLabel: {
            color: '#8b9eb0',
            fontSize: 12
          },
          splitLine: {
            show: true,
            lineStyle: {
              color: 'rgba(139, 158, 176, 0.1)'
            }
          }
        },
        series: [
          {
            data: this.data.map((item) => item.value),
            type: 'line',
            smooth: true,
            symbol: 'none',
            lineStyle: {
              width: 3,
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  {
                    offset: 0,
                    color: '#00a8ff'
                  },
                  {
                    offset: 1,
                    color: 'rgba(0, 168, 255, 0.1)'
                  }
                ]
              },
              shadowColor: 'rgba(0, 168, 255, 0.2)',
              shadowBlur: 10
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  {
                    offset: 0,
                    color: 'rgba(0, 168, 255, 0.2)'
                  },
                  {
                    offset: 1,
                    color: 'rgba(0, 168, 255, 0.05)'
                  }
                ]
              }
            },
            emphasis: {
              focus: 'series'
            },
            animation: true
          }
        ]
      }

      this.chart.setOption(option)
    },
    handleResize() {
      if (this.resizeTimeout) {
        clearTimeout(this.resizeTimeout)
      }
      this.resizeTimeout = setTimeout(() => {
        if (this.chart && document.body.contains(this.$refs.chartRef)) {
          this.chart.resize()
        }
      }, 100)
    }
  },
  watch: {
    data: {
      handler() {
        this.updateChart()
      },
      deep: true
    }
  },
  mounted() {
    this.initChart()
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
    if (this.resizeTimeout) {
      clearTimeout(this.resizeTimeout)
    }
    window.removeEventListener('resize', this.handleResize)
  }
}
</script>

<style scoped>
.feeding-chart {
  width: 100%;
  height: 100%;
  min-height: 200px;
}

:deep(.echarts) {
  width: 100% !important;
  height: 100% !important;
}
</style>
