<template>
  <div class="data-report bg-white text-gray-900">
    <div class="report-header bg-blue-50 p-4 rounded-lg mb-5 shadow-sm border border-blue-100">
      <h2 class="text-blue-700 text-xl font-bold mb-3">数据分析报表</h2>
      <div class="report-actions flex items-center justify-between">
        <el-button-group class="shadow-sm">
          <el-button
            type="primary"
            size="default"
            @click="exportData"
            class="bg-blue-600 hover:bg-blue-700 border-blue-700"
          >
            <el-icon class="mr-1"><Download /></el-icon>
            导出Excel
          </el-button>
          <el-button
            type="success"
            size="default"
            @click="exportImage"
            class="bg-green-600 hover:bg-green-700 border-green-700"
          >
            <el-icon class="mr-1"><PictureFilled /></el-icon>
            导出图表
          </el-button>
          <el-button
            type="warning"
            size="default"
            @click="printReport"
            class="bg-amber-500 hover:bg-amber-600 border-amber-600"
          >
            <el-icon class="mr-1"><Printer /></el-icon>
            打印报表
          </el-button>
        </el-button-group>
      </div>
    </div>

    <div class="report-content bg-white border border-gray-200 rounded-lg shadow-sm p-5">
      <div class="data-filter mb-5 bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h3 class="text-blue-700 text-base font-semibold mb-3">数据筛选</h3>
        <el-form :inline="true" size="default">
          <el-form-item label="数据日期" class="mb-0">
            <el-date-picker
              v-model="filterDate"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 280px"
              class="rounded-md"
            />
          </el-form-item>
          <el-form-item label="对比组数" class="mb-0">
            <el-select v-model="filterGroups" placeholder="选择组数" class="rounded-md">
              <el-option label="全部" value="all" />
              <el-option label="最近5组" value="5" />
              <el-option label="最近10组" value="10" />
            </el-select>
          </el-form-item>
          <el-form-item class="mb-0">
            <el-button
              type="primary"
              @click="applyFilter"
              class="bg-blue-600 hover:bg-blue-700 border-blue-700 rounded-md"
            >
              <el-icon class="mr-1"><Search /></el-icon>
              应用筛选
            </el-button>
            <el-button @click="resetFilter" class="ml-2 rounded-md">
              <el-icon class="mr-1"><RefreshRight /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-tabs v-model="activeTab" class="border-b border-gray-200 custom-tabs">
        <el-tab-pane label="粒径分布曲线" name="curves">
          <div
            class="chart-container mb-5 border border-blue-100 rounded-lg shadow-sm bg-white p-4"
          >
            <h3 class="text-blue-700 text-base font-semibold mb-3">粒径分布曲线图</h3>
            <div ref="curvesChart" class="chart" style="height: 380px"></div>
          </div>
          <div class="control-panel mb-5 bg-blue-50 p-4 rounded-lg border border-blue-100">
            <div class="legend-control mb-4">
              <h4 class="text-blue-700 text-sm font-semibold mb-3">数据组选择</h4>
              <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                <el-checkbox
                  v-for="item in groupData"
                  :key="item.group"
                  :label="item.group"
                  class="custom-checkbox"
                >
                  第 {{ item.group }} 组 [{{ item.range }}]
                </el-checkbox>
              </div>
            </div>
            <div class="view-control">
              <h4 class="text-blue-700 text-sm font-semibold mb-3">显示模式</h4>
              <el-radio-group
                v-model="curveDisplayMode"
                @change="updateCurvesChart"
                size="default"
                class="custom-radio"
              >
                <el-radio-button label="original">原始数据</el-radio-button>
                <el-radio-button label="mixed">拟合曲线</el-radio-button>
                <el-radio-button label="combined">全部组合</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="MX值对比" name="mx">
          <div
            class="chart-container mb-5 border border-blue-100 rounded-lg shadow-sm bg-white p-4"
          >
            <h3 class="text-blue-700 text-base font-semibold mb-3">MX值对比图</h3>
            <div ref="mxComparisonChart" class="chart" style="height: 380px"></div>
          </div>
          <div class="data-table mb-5">
            <h4 class="text-blue-700 text-base font-semibold mb-3">MX值对比数据</h4>
            <el-table
              :data="mxData"
              border
              style="width: 100%"
              class="custom-table rounded-lg overflow-hidden"
              :header-cell-style="{ background: '#EFF6FF', color: '#1D4ED8', fontWeight: 'bold' }"
              :cell-style="{ textAlign: 'center' }"
            >
              <el-table-column prop="group" label="组别" width="100" />
              <el-table-column prop="screeningMx" label="筛分法MX" />
              <el-table-column prop="cameraMx" label="双相机MX" />
              <el-table-column prop="loss" label="Loss (%)" />
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="粒径分布" name="distribution">
          <div
            class="chart-container mb-5 border border-blue-100 rounded-lg shadow-sm bg-white p-4"
          >
            <h3 class="text-blue-700 text-base font-semibold mb-3">粒径分布对比图</h3>
            <div ref="distributionChart" class="chart" style="height: 380px"></div>
          </div>
          <div class="data-table mb-5">
            <h4 class="text-blue-700 text-base font-semibold mb-3">粒径分布数据</h4>
            <el-table
              :data="distributionData"
              border
              style="width: 100%"
              class="custom-table rounded-lg overflow-hidden"
              :header-cell-style="{ background: '#EFF6FF', color: '#1D4ED8', fontWeight: 'bold' }"
              :cell-style="{ textAlign: 'center' }"
            >
              <el-table-column prop="range" label="粒径范围(mm)" />
              <el-table-column prop="screening" label="筛分法(%)" />
              <el-table-column prop="camera" label="双相机(%)" />
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="误差分析" name="error">
          <div
            class="chart-container mb-5 border border-blue-100 rounded-lg shadow-sm bg-white p-4"
          >
            <h3 class="text-blue-700 text-base font-semibold mb-3">误差分析图</h3>
            <div ref="errorChart" class="chart" style="height: 380px"></div>
          </div>
          <div class="data-table mb-5">
            <h4 class="text-blue-700 text-base font-semibold mb-3">误差分析数据</h4>
            <el-table
              :data="errorData"
              border
              style="width: 100%"
              class="custom-table rounded-lg overflow-hidden"
              :header-cell-style="{ background: '#EFF6FF', color: '#1D4ED8', fontWeight: 'bold' }"
              :cell-style="{ textAlign: 'center' }"
            >
              <el-table-column prop="range" label="粒径范围(mm)" />
              <el-table-column prop="totalError" label="总误差分类概率(%)" />
              <el-table-column prop="previousError" label="误差分类到前一个区间(%)" />
              <el-table-column prop="nextError" label="误差分类到后一个区间(%)" />
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Download, Printer, PictureFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { saveAs } from 'file-saver'
import * as XLSX from 'xlsx'
import { ElMessage } from 'element-plus'

export default {
  name: 'DataReport',
  components: {
    Download,
    Printer,
    PictureFilled
  },
  setup() {
    const activeTab = ref('curves')
    const mxComparisonChart = ref(null)
    const distributionChart = ref(null)
    const errorChart = ref(null)
    const curvesChart = ref(null)
    const imageRefs = ref([])
    let chartInstances = []

    // 筛选条件
    const filterDate = ref([])
    const filterGroups = ref('all')

    // 粒径分布曲线控制
    const selectedGroups = ref([1, 2, 3, 4, 5, 6])
    const curveDisplayMode = ref('mixed')

    // 图片分析数据
    const imageData = ref([])

    // 图片悬停效果
    const handleHover = (img, index) => {
      imageData.value[index].hovering = true
    }

    const handleHoverEnd = (index) => {
      imageData.value[index].hovering = false
    }

    // 粒径分布数据点 - 更接近图片中的数据
    const groupData = ref([
      {
        group: 1,
        range: '0.03-0.15',
        color: '#1890ff',
        points: [
          { x: 0.03, y: 0.01 },
          { x: 0.06, y: 0.05 },
          { x: 0.09, y: 0.1 },
          { x: 0.11, y: 0.09 },
          { x: 0.13, y: 0.05 },
          { x: 0.15, y: 0.01 },
          { x: 0.17, y: 0.0 }
        ]
      },
      {
        group: 2,
        range: '0.09-0.33',
        color: '#ff9c6e',
        points: [
          { x: 0.09, y: 0.0 },
          { x: 0.11, y: 0.05 },
          { x: 0.13, y: 0.12 },
          { x: 0.15, y: 0.175 },
          { x: 0.17, y: 0.12 },
          { x: 0.21, y: 0.05 },
          { x: 0.33, y: 0.0 }
        ]
      },
      {
        group: 3,
        range: '0.23-0.59',
        color: '#52c41a',
        points: [
          { x: 0.23, y: 0.0 },
          { x: 0.3, y: 0.04 },
          { x: 0.37, y: 0.09 },
          { x: 0.42, y: 0.115 },
          { x: 0.48, y: 0.075 },
          { x: 0.54, y: 0.02 },
          { x: 0.59, y: 0.0 }
        ]
      },
      {
        group: 4,
        range: '0.45-1.15',
        color: '#f5222d',
        points: [
          { x: 0.45, y: 0.0 },
          { x: 0.55, y: 0.04 },
          { x: 0.65, y: 0.09 },
          { x: 0.75, y: 0.125 },
          { x: 0.85, y: 0.075 },
          { x: 0.95, y: 0.025 },
          { x: 1.15, y: 0.0 }
        ]
      },
      {
        group: 5,
        range: '0.84-2.12',
        color: '#722ed1',
        points: [
          { x: 0.84, y: 0.0 },
          { x: 1.0, y: 0.03 },
          { x: 1.16, y: 0.075 },
          { x: 1.32, y: 0.125 },
          { x: 1.48, y: 0.07 },
          { x: 1.72, y: 0.02 },
          { x: 2.12, y: 0.0 }
        ]
      },
      {
        group: 6,
        range: '1.82-3.98',
        color: '#a0522d',
        points: [
          { x: 1.82, y: 0.0 },
          { x: 2.2, y: 0.03 },
          { x: 2.7, y: 0.08 },
          { x: 3.0, y: 0.13 },
          { x: 3.3, y: 0.085 },
          { x: 3.6, y: 0.03 },
          { x: 3.98, y: 0.0 }
        ]
      }
    ])

    // 更新示例数据为实际数据格式
    const mxData = ref([
      { group: 1, screeningMx: 2.0, cameraMx: 2.05, loss: 7.0 },
      { group: 2, screeningMx: 3.05, cameraMx: 3.25, loss: 13.5 },
      { group: 3, screeningMx: 2.5, cameraMx: 2.7, loss: 10.2 },
      { group: 4, screeningMx: 2.35, cameraMx: 2.3, loss: 10.5 },
      { group: 5, screeningMx: 2.2, cameraMx: 2.25, loss: 9.5 },
      { group: 6, screeningMx: 2.7, cameraMx: 2.85, loss: 8.5 },
      { group: 7, screeningMx: 2.9, cameraMx: 3.05, loss: 11.0 },
      { group: 8, screeningMx: 2.7, cameraMx: 2.85, loss: 10.2 },
      { group: 9, screeningMx: 3.3, cameraMx: 3.2, loss: 14.0 },
      { group: 10, screeningMx: 3.5, cameraMx: 3.6, loss: 15.8 }
    ])

    // 筛选后显示的数据
    const filteredMxData = ref([...mxData.value])

    const distributionData = ref([
      { range: '0.075-0.15', screening: 20.0, camera: 18.9, difference: -1.1 },
      { range: '0.15-0.3', screening: 10.0, camera: 10.2, difference: 0.2 },
      { range: '0.3-0.6', screening: 29.0, camera: 30.7, difference: 1.7 },
      { range: '0.6-1.18', screening: 31.0, camera: 29.2, difference: -1.8 },
      { range: '1.18-2.36', screening: 10.0, camera: 9.5, difference: -0.5 },
      { range: '2.36-4.75', screening: 0.0, camera: 1.5, difference: 1.5 }
    ])

    const errorData = ref([
      { range: '0.15-0.3', totalError: 13.0, previousError: 0.0, nextError: 0.0 },
      { range: '0.3-0.6', totalError: 11.5, previousError: 2.8, nextError: 0.75 },
      { range: '0.6-1.18', totalError: 8.6, previousError: 1.07, nextError: 0.75 },
      { range: '1.18-2.36', totalError: 5.6, previousError: 0.77, nextError: 0.69 },
      { range: '2.36-4.75', totalError: 16.45, previousError: 3.54, nextError: 0.99 }
    ])

    // 创建图表实例的函数
    const createChart = (container, options) => {
      if (!container.value || !document.body.contains(container.value)) {
        return null
      }

      // 确保容器是可见的且有尺寸
      if (
        container.value.offsetParent === null ||
        container.value.offsetWidth === 0 ||
        container.value.offsetHeight === 0
      ) {
        return null
      }

      try {
        // 如果已经存在图表实例，先销毁它
        const existingChart = chartInstances.find(
          (chart) => chart && chart.getDom && chart.getDom() === container.value
        )

        if (existingChart) {
          existingChart.dispose()
          chartInstances = chartInstances.filter((chart) => chart !== existingChart)
        }

        // 创建新的图表实例
        const chart = echarts.init(container.value, null, {
          renderer: 'canvas',
          useDirtyRect: false
        })

        // 设置图表选项
        chart.setOption(options)

        // 添加图表实例到数组
        chartInstances.push(chart)

        return chart
      } catch (error) {
        console.error('创建图表失败:', error)
        return null
      }
    }

    // 创建粒径分布曲线图
    const createCurvesChart = () => {
      if (!curvesChart.value) return null

      try {
        // 生成系列数据
        const series = []

        if (curveDisplayMode.value === 'combined') {
          // 显示所有组的数据在一张图上
          groupData.value.forEach((group, index) => {
            if (!selectedGroups.value.includes(group.group)) return

            series.push({
              name: `第 ${group.group} 组`,
              type: 'line',
              smooth: true,
              symbolSize: 5,
              lineStyle: {
                width: 3
              },
              itemStyle: {
                color: group.color
              },
              data: group.points.map((point) => [point.x, point.y])
            })
          })
        } else {
          // 原始数据和拟合曲线分开显示
          selectedGroups.value.forEach((groupId, index) => {
            const group = groupData.value.find((g) => g.group === groupId)
            if (!group) return

            // 原始数据曲线
            series.push({
              name: `第 ${group.group} 组`,
              type: 'line',
              smooth: true,
              symbolSize: 5,
              lineStyle: {
                width: 3,
                type: curveDisplayMode.value === 'original' ? 'solid' : 'dotted'
              },
              itemStyle: {
                color: group.color
              },
              data: group.points.map((point) => [point.x, point.y])
            })

            // 拟合曲线
            if (curveDisplayMode.value === 'mixed') {
              series.push({
                name: `第 ${group.group} 组拟合`,
                type: 'line',
                smooth: true,
                symbolSize: 0,
                lineStyle: {
                  width: 2,
                  type: 'dashed'
                },
                itemStyle: {
                  color: group.color
                },
                data: group.points.map((point) => [point.x, point.y * 0.95])
              })
            }
          })
        }

        const option = {
          title: {
            text: '粒径分布',
            textStyle: {
              color: '#00a8ff',
              fontSize: 16
            }
          },
          tooltip: {
            trigger: 'axis',
            formatter: function (params) {
              let result = `粒径: ${params[0].data[0]}mm<br>`
              params.forEach((param) => {
                // 忽略拟合曲线的显示
                if (!param.seriesName.includes('拟合')) {
                  result += `${param.seriesName}: ${(param.data[1] * 100).toFixed(2)}%<br>`
                }
              })
              return result
            }
          },
          legend: {
            data: selectedGroups.value
              .map((groupId) => {
                const group = groupData.value.find((g) => g.group === groupId)
                if (!group) return ''
                return `第 ${group.group} 组: [${group.range}]`
              })
              .filter(Boolean),
            textStyle: {
              color: '#e6f7ff'
            },
            right: 10,
            orient: 'vertical',
            top: 50,
            selected: selectedGroups.value.reduce((acc, groupId) => {
              const group = groupData.value.find((g) => g.group === groupId)
              if (group) {
                acc[`第 ${group.group} 组: [${group.range}]`] = true
              }
              return acc
            }, {})
          },
          grid: {
            left: '3%',
            right: '22%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'value',
            name: '粒径 (mm)',
            min: 0,
            max: 4.0,
            axisLine: {
              lineStyle: {
                color: '#8b9eb0'
              }
            },
            axisLabel: {
              color: '#e6f7ff',
              formatter: '{value}'
            },
            splitLine: {
              lineStyle: {
                color: 'rgba(139, 158, 176, 0.1)'
              }
            }
          },
          yAxis: {
            type: 'value',
            name: '比例',
            min: 0,
            max: 0.2,
            axisLine: {
              lineStyle: {
                color: '#8b9eb0'
              }
            },
            axisLabel: {
              color: '#e6f7ff',
              formatter: function (value) {
                return (value * 100).toFixed(2) + '%'
              }
            },
            splitLine: {
              lineStyle: {
                color: 'rgba(139, 158, 176, 0.1)'
              }
            }
          },
          series: series
        }

        const chart = createChart(curvesChart, option)
        if (chart) chartInstances.push(chart)
        return chart
      } catch (error) {
        console.error('创建曲线图表失败:', error)
        return null
      }
    }

    // 更新曲线图
    const updateCurvesChart = () => {
      if (activeTab.value !== 'curves') return

      // 清理旧图表并创建新的
      disposeAllCharts()

      // 延迟创建以确保DOM更新
      setTimeout(() => {
        createCurvesChart()
      }, 100)
    }

    // 初始化图表和创建初始图表的函数
    const initCharts = async () => {
      try {
        // 清理现有图表
        disposeAllCharts()

        // 确保DOM更新完成
        await nextTick()

        // 延迟创建图表以确保DOM已渲染
        setTimeout(() => {
          if (document.visibilityState === 'visible') {
            createChartByTab(activeTab.value)
          }
        }, 300)
      } catch (error) {
        console.error('初始化图表时出错:', error)
      }
    }

    // 根据当前标签页创建相应图表
    const createChartByTab = (tab) => {
      // 清理现有图表
      disposeAllCharts()

      // 确保DOM已经准备好
      nextTick(() => {
        try {
          // 检查容器是否可见
          const containerMap = {
            mx: mxComparisonChart.value,
            distribution: distributionChart.value,
            error: errorChart.value,
            curves: curvesChart.value
          }

          if (!containerMap[tab] || !document.body.contains(containerMap[tab])) {
            return
          }

          // 根据标签页创建相应图表
          switch (tab) {
            case 'mx':
              createMxChart()
              break
            case 'distribution':
              createDistributionChart()
              break
            case 'error':
              createErrorChart()
              break
            case 'curves':
              createCurvesChart()
              break
          }
        } catch (error) {
          console.error('创建图表失败:', error)
        }
      })
    }

    // 处理标签页切换
    const handleTabChange = (tab) => {
      // 先清理现有图表
      disposeAllCharts()

      // 延迟切换以确保DOM更新
      setTimeout(() => {
        createChartByTab(tab)
      }, 200)
    }

    // 优化图表清理逻辑
    const disposeAllCharts = () => {
      const disposedCharts = new Set()

      chartInstances.forEach((chart) => {
        if (chart && !disposedCharts.has(chart)) {
          try {
            chart.dispose()
            disposedCharts.add(chart)
          } catch (e) {
            console.warn('图表清理异常:', e)
          }
        }
      })

      // 清空图表实例数组
      chartInstances = []
    }

    // 在挂载时处理
    onMounted(() => {
      // 设置延迟确保DOM完全加载
      const initTimeout = setTimeout(() => {
        // 初始化图表
        initCharts()

        // 创建resize处理函数
        let resizeTimeout
        const handleResize = () => {
          if (document.visibilityState === 'visible') {
            chartInstances.forEach((chart) => {
              if (chart && chart.getDom && document.body.contains(chart.getDom())) {
                try {
                  requestAnimationFrame(() => {
                    chart.resize()
                  })
                } catch (e) {
                  console.warn('调整图表大小失败:', e)
                }
              }
            })
          }
        }

        // 使用防抖处理resize事件
        const debouncedResize = () => {
          if (resizeTimeout) {
            clearTimeout(resizeTimeout)
          }
          resizeTimeout = setTimeout(handleResize, 200)
        }

        // 添加resize事件监听
        window.addEventListener('resize', debouncedResize)

        // 监听标签页变化
        watch(activeTab, (newTab) => {
          handleTabChange(newTab)
        })

        // 监听visibility change事件
        const visibilityHandler = () => {
          if (document.visibilityState === 'visible') {
            setTimeout(initCharts, 200)
          }
        }
        document.addEventListener('visibilitychange', visibilityHandler)

        // 组件卸载时清理
        onUnmounted(() => {
          if (resizeTimeout) {
            clearTimeout(resizeTimeout)
          }
          if (initTimeout) {
            clearTimeout(initTimeout)
          }
          window.removeEventListener('resize', debouncedResize)
          document.removeEventListener('visibilitychange', visibilityHandler)
          disposeAllCharts()
        })
      }, 300)
    })

    // 创建MX对比图表
    const createMxChart = () => {
      if (!mxComparisonChart.value) return null

      try {
        const options = {
          title: {
            text: '筛分法MX值与双相机MX值对比',
            textStyle: {
              color: '#00a8ff',
              fontSize: 16
            }
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            }
          },
          legend: {
            data: ['筛分法MX', '双相机MX', 'Loss'],
            textStyle: {
              color: '#e6f7ff'
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: [
            {
              type: 'category',
              data: filteredMxData.value.map((item) => item.group),
              name: '土组样本对比',
              axisLine: {
                lineStyle: {
                  color: '#8b9eb0'
                }
              },
              axisLabel: {
                color: '#e6f7ff'
              }
            }
          ],
          yAxis: [
            {
              type: 'value',
              name: 'MX值',
              position: 'left',
              axisLine: {
                lineStyle: {
                  color: '#8b9eb0'
                }
              },
              axisLabel: {
                color: '#e6f7ff'
              },
              splitLine: {
                lineStyle: {
                  color: 'rgba(139, 158, 176, 0.1)'
                }
              }
            },
            {
              type: 'value',
              name: 'Loss (%)',
              position: 'right',
              axisLine: {
                lineStyle: {
                  color: '#8b9eb0'
                }
              },
              axisLabel: {
                color: '#e6f7ff'
              },
              splitLine: {
                show: false
              }
            }
          ],
          series: [
            {
              name: '筛分法MX',
              type: 'bar',
              data: filteredMxData.value.map((item) => item.screeningMx),
              itemStyle: {
                color: '#5470c6'
              }
            },
            {
              name: '双相机MX',
              type: 'bar',
              data: filteredMxData.value.map((item) => item.cameraMx),
              itemStyle: {
                color: '#fac858'
              }
            },
            {
              name: 'Loss',
              type: 'line',
              yAxisIndex: 1,
              data: filteredMxData.value.map((item) => item.loss),
              itemStyle: {
                color: '#91cc75'
              },
              lineStyle: {
                width: 2
              },
              symbol: 'circle',
              symbolSize: 8
            }
          ]
        }

        const chart = createChart(mxComparisonChart, options)
        if (chart) chartInstances.push(chart)
        return chart
      } catch (error) {
        console.error('创建MX图表失败:', error)
        return null
      }
    }

    // 创建粒径分布图表
    const createDistributionChart = () => {
      if (!distributionChart.value) return null

      try {
        const options = {
          title: {
            text: '筛分法与双相机结果对比分析',
            textStyle: {
              color: '#00a8ff',
              fontSize: 16
            }
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            }
          },
          legend: {
            data: ['筛分法', '双相机', '误差'],
            textStyle: {
              color: '#e6f7ff'
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: distributionData.value.map((item) => item.range),
            name: '粒径范围 (mm)',
            axisLine: {
              lineStyle: {
                color: '#8b9eb0'
              }
            },
            axisLabel: {
              color: '#e6f7ff'
            }
          },
          yAxis: [
            {
              type: 'value',
              name: '百分比 (%)',
              position: 'left',
              axisLine: {
                lineStyle: {
                  color: '#8b9eb0'
                }
              },
              axisLabel: {
                color: '#e6f7ff'
              },
              splitLine: {
                lineStyle: {
                  color: 'rgba(139, 158, 176, 0.1)'
                }
              }
            },
            {
              type: 'value',
              name: '误差 (%)',
              position: 'right',
              axisLine: {
                lineStyle: {
                  color: '#8b9eb0'
                }
              },
              axisLabel: {
                color: '#e6f7ff'
              },
              splitLine: {
                show: false
              }
            }
          ],
          series: [
            {
              name: '筛分法',
              type: 'bar',
              data: distributionData.value.map((item) => item.screening),
              itemStyle: {
                color: '#5470c6'
              }
            },
            {
              name: '双相机',
              type: 'bar',
              data: distributionData.value.map((item) => item.camera),
              itemStyle: {
                color: '#fac858'
              }
            },
            {
              name: '误差',
              type: 'line',
              yAxisIndex: 1,
              data: distributionData.value.map((item) => item.difference),
              itemStyle: {
                color: '#ee6666'
              },
              lineStyle: {
                width: 2
              },
              symbol: 'circle',
              symbolSize: 8
            }
          ]
        }

        const chart = createChart(distributionChart, options)
        if (chart) chartInstances.push(chart)
        return chart
      } catch (error) {
        console.error('创建分布图表失败:', error)
        return null
      }
    }

    // 创建误差分析图表
    const createErrorChart = () => {
      if (!errorChart.value) return null

      try {
        const options = {
          title: {
            text: '不同粒径区间的错误分类概率对比',
            textStyle: {
              color: '#00a8ff',
              fontSize: 16
            }
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            }
          },
          legend: {
            data: ['总错误分类概率', '错误分类到前一个区间', '错误分类到后一个区间'],
            textStyle: {
              color: '#e6f7ff'
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: errorData.value.map((item) => item.range),
            name: '粒径范围 (mm)',
            axisLine: {
              lineStyle: {
                color: '#8b9eb0'
              }
            },
            axisLabel: {
              color: '#e6f7ff'
            }
          },
          yAxis: {
            type: 'value',
            name: '错误分类概率 (%)',
            axisLine: {
              lineStyle: {
                color: '#8b9eb0'
              }
            },
            axisLabel: {
              color: '#e6f7ff'
            },
            splitLine: {
              lineStyle: {
                color: 'rgba(139, 158, 176, 0.1)'
              }
            }
          },
          series: [
            {
              name: '总错误分类概率',
              data: errorData.value.map((item) => item.totalError),
              type: 'line',
              smooth: true,
              lineStyle: {
                width: 3
              },
              symbol: 'circle',
              symbolSize: 10,
              itemStyle: {
                color: '#91cc75'
              }
            },
            {
              name: '错误分类到前一个区间',
              type: 'bar',
              stack: 'total',
              data: errorData.value.map((item) => item.previousError),
              itemStyle: {
                color: '#fac858'
              }
            },
            {
              name: '错误分类到后一个区间',
              type: 'bar',
              stack: 'total',
              data: errorData.value.map((item) => item.nextError),
              itemStyle: {
                color: '#ee6666'
              }
            }
          ]
        }

        const chart = createChart(errorChart, options)
        if (chart) chartInstances.push(chart)
        return chart
      } catch (error) {
        console.error('创建误差图表失败:', error)
        return null
      }
    }

    // 导出图表为图片
    const exportImage = () => {
      // 获取当前激活的图表
      let activeChart = null

      if (chartInstances.length > 0) {
        activeChart = chartInstances[0] // 当前标签页只有一个图表实例
      }

      if (activeChart) {
        // 获取图表的数据URL
        try {
          const url = activeChart.getDataURL({
            type: 'png',
            pixelRatio: 2,
            backgroundColor: '#001529'
          })

          // 创建临时链接并下载
          const link = document.createElement('a')
          link.download = `砂石级配分析_${activeTab.value}_${new Date().toISOString().split('T')[0]}.png`
          link.href = url
          link.click()
        } catch (error) {
          console.error('导出图片失败:', error)
          ElMessage.error('导出图片失败，请重试')
        }
      }
    }

    // 导出数据到Excel
    const exportData = () => {
      // 创建工作簿
      const wb = XLSX.utils.book_new()

      // 转换MX数据
      const mxWs = XLSX.utils.json_to_sheet(mxData.value)
      XLSX.utils.book_append_sheet(wb, mxWs, 'MX值对比')

      // 转换分布数据
      const distributionWs = XLSX.utils.json_to_sheet(distributionData.value)
      XLSX.utils.book_append_sheet(wb, distributionWs, '粒径分布')

      // 转换误差数据
      const errorWs = XLSX.utils.json_to_sheet(errorData.value)
      XLSX.utils.book_append_sheet(wb, errorWs, '误差分析')

      // 添加摘要数据
      const summaryData = [
        ['报告生成日期', new Date().toLocaleDateString()],
        ['总样本数', mxData.value.length],
        [
          '平均筛分法MX',
          (
            mxData.value.reduce((sum, item) => sum + item.screeningMx, 0) / mxData.value.length
          ).toFixed(2)
        ],
        [
          '平均双相机MX',
          (
            mxData.value.reduce((sum, item) => sum + item.cameraMx, 0) / mxData.value.length
          ).toFixed(2)
        ],
        [
          '平均误差率',
          (mxData.value.reduce((sum, item) => sum + item.loss, 0) / mxData.value.length).toFixed(
            2
          ) + '%'
        ]
      ]
      const summaryWs = XLSX.utils.aoa_to_sheet(summaryData)
      XLSX.utils.book_append_sheet(wb, summaryWs, '报告摘要')

      // 导出Excel文件
      const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
      const blob = new Blob([wbout], { type: 'application/octet-stream' })
      saveAs(blob, `砂石级配分析报告_${new Date().toISOString().split('T')[0]}.xlsx`)
    }

    const printReport = () => {
      ElMessage.info('正在准备打印...')
      nextTick(() => {
        window.print()
      })
    }

    // 应用筛选
    const applyFilter = () => {
      try {
        // 实现筛选逻辑
        if (filterGroups.value === 'all') {
          filteredMxData.value = [...mxData.value]
        } else {
          const count = parseInt(filterGroups.value)
          const startIdx = Math.max(0, mxData.value.length - count)
          filteredMxData.value = mxData.value.slice(startIdx)
        }

        // 如果当前是MX标签页，更新图表
        if (activeTab.value === 'mx') {
          disposeAllCharts()
          setTimeout(() => {
            createMxChart()
          }, 100)
        }

        ElMessage.success(
          `已应用筛选: ${filterGroups.value === 'all' ? '全部' : `最近${filterGroups.value}组`}数据`
        )
      } catch (error) {
        console.error('应用筛选失败:', error)
        ElMessage.error('应用筛选失败，请重试')
      }
    }

    // 重置筛选
    const resetFilter = () => {
      try {
        filterDate.value = []
        filterGroups.value = 'all'
        filteredMxData.value = [...mxData.value]

        // 如果当前是MX标签页，更新图表
        if (activeTab.value === 'mx') {
          disposeAllCharts()
          setTimeout(() => {
            createMxChart()
          }, 100)
        }

        ElMessage.info('已重置筛选条件')
      } catch (error) {
        console.error('重置筛选失败:', error)
        ElMessage.error('重置筛选失败，请重试')
      }
    }

    // 监听标签页变化
    watch(activeTab, (newTab, oldTab) => {
      if (newTab !== oldTab) {
        handleTabChange(newTab)
      }
    })

    // 监听筛选条件变化
    watch([filterDate, filterGroups], () => {
      // 可以在这里添加自动应用筛选的逻辑，或者让用户手动点击应用按钮
    })

    // 确保在组件卸载时清理所有图表实例和事件监听器
    onUnmounted(() => {
      disposeAllCharts()
    })

    return {
      activeTab,
      mxComparisonChart,
      distributionChart,
      errorChart,
      curvesChart,
      imageRefs,
      mxData,
      filteredMxData,
      distributionData,
      errorData,
      groupData,
      selectedGroups,
      curveDisplayMode,
      imageData,
      exportData,
      exportImage,
      printReport,
      filterDate,
      filterGroups,
      applyFilter,
      resetFilter,
      updateCurvesChart,
      generateTestImages,
      handleHover,
      handleHoverEnd
    }
  }
}
</script>

<style scoped>
.data-report {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.chart {
  width: 100%;
  height: 100%;
}

/* 自定义表格样式 */
.custom-table {
  --el-table-border-color: #e5e7eb;
  --el-table-border: 1px solid #e5e7eb;
  --el-table-text-color: #374151;
  --el-table-header-text-color: #1d4ed8;
  --el-table-row-hover-bg-color: #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 自定义标签页样式 */
:deep(.custom-tabs .el-tabs__item) {
  font-size: 15px;
  color: #6b7280;
  padding: 0 20px;
  height: 40px;
  line-height: 40px;
}

:deep(.custom-tabs .el-tabs__item.is-active) {
  color: #1d4ed8;
  font-weight: bold;
}

:deep(.custom-tabs .el-tabs__active-bar) {
  background-color: #1d4ed8;
  height: 3px;
}

:deep(.custom-tabs .el-tabs__nav-wrap::after) {
  background-color: #e5e7eb;
  height: 1px;
}

/* 自定义复选框样式 */
:deep(.custom-checkbox .el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}

:deep(.custom-checkbox .el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #1d4ed8;
}

/* 自定义单选按钮样式 */
:deep(.custom-radio .el-radio-button__inner) {
  background: #f9fafb;
  border-color: #d1d5db;
  color: #4b5563;
}

:deep(.custom-radio .el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
  color: white;
  box-shadow: -1px 0 0 0 #1d4ed8;
}

/* 打印样式 */
@media print {
  .report-header,
  .data-filter,
  .control-panel,
  .el-tabs__header {
    display: none !important;
  }

  .chart-container {
    page-break-inside: avoid;
    margin-bottom: 20px;
    border: none !important;
    box-shadow: none !important;
  }

  .data-table {
    page-break-inside: avoid;
    margin-bottom: 20px;
  }

  .el-table {
    width: 100% !important;
    border: 1px solid #000 !important;
  }

  .el-table th,
  .el-table td {
    padding: 5px !important;
    border: 1px solid #000 !important;
  }

  .report-content {
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
  }

  h3,
  h4 {
    font-size: 14px !important;
    margin-bottom: 8px !important;
    color: #000 !important;
  }
}
</style>
