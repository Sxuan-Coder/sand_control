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
        <!-- 移除全局/局部切换按钮 -->
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
            <el-button 
              type="success" 
              @click="loadLatestData" 
              class="ml-2 rounded-md bg-green-600 hover:bg-green-700 border-green-700">
              <el-icon class="mr-1"><Refresh /></el-icon>
              刷新数据
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-tabs v-model="activeTab" class="border-b border-gray-200 custom-tabs">
        <el-tab-pane label="粒径分布直方图" name="curves">
          <div
            class="chart-container mb-5 border border-blue-100 rounded-lg shadow-sm bg-white p-4"
          >
            <h3 class="text-blue-700 text-base font-semibold mb-3">粒径分布直方图</h3>
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
                  v-model="selectedGroups" 
                  :value="item.group"
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
              :data="filteredMxData"
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
              <el-table-column prop="difference" label="差值(%)" />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- <el-tab-pane label="误差分析" name="error">
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
        </el-tab-pane> -->
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Download, Printer, PictureFilled, RefreshRight, Search, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { saveAs } from 'file-saver'
import * as XLSX from 'xlsx'
import { ElMessage, ElLoading } from 'element-plus'
import { getProcessingResults } from '../api/sandImageApi'

export default {
  name: 'DataReport',
  components: {
    Download,
    Printer,
    PictureFilled,
    RefreshRight,
    Search,
    Refresh
  },
  setup() {
    const activeTab = ref('curves')
    const mxComparisonChart = ref(null)
    const distributionChart = ref(null)
    const errorChart = ref(null)
    const curvesChart = ref(null)
    const imageRefs = ref([]) // 注意：这个 ref 在模板中没有被使用
    let chartInstances = []
    let resizeTimeout = null;
    let initTimeout = null;


    // 筛选条件
    const filterDate = ref([])
    const filterGroups = ref('all')
    const isLoading = ref(false)

    // 粒径分布曲线控制
    const selectedGroups = ref([1]) // 默认只选择第一组
    const curveDisplayMode = ref('mixed')

    // 图片分析数据 (示例数据，实际应从API获取)
    const imageData = ref([]) // 注意：这个 ref 在模板中没有被使用

    // 处理全局/局部分析数据
    const processAnalysisData = (data, view = 'local') => {
      const distributions = [];
      let index = 0;

      // Process grade distributions
      if (data.grade_statistics) {
        data.grade_statistics.forEach((group, gradeIdx) => {
          // Skip empty or invalid grades
          if (!group) return;

          const stats = Array(6).fill(0);
          let totalCount = 0;

          // Calculate percentages for each grade
          group.forEach((grade, index) => {
            if (index < 6) {
              stats[index] = {
                count: grade.count || 0,
                percentage: 0 // Will calculate after getting total
              };
              totalCount += grade.count || 0;
            }
          });

          // Convert counts to percentages
          stats.forEach(stat => {
            stat.percentage = (stat.count / totalCount) * 100;
          });

          // Only add if we have valid data
          if (totalCount > 0) {
            distributions.push({
              group: index + 1,
              stats: stats,
              range: `<0.075mm - 2.36mm`,
              color: ['#1890ff', '#ff9c6e', '#52c41a', '#f5222d', '#722ed1', '#a0522d'][index % 6]
            });
            index++;
          }
        });
      }

      return distributions;
    };

    const loadProcessingResults = async () => {
      const loadingInstance = ElLoading.service({
        lock: true,
        text: '加载分析数据中...',
        background: 'rgba(255, 255, 255, 0.7)'
      })

      try {
        const data = await getProcessingResults()

        if (!data.global || data.global.length === 0) {
          ElMessage.error('未找到有效的粒度分布数据')
          return
        }

        // 提取粒度分布数据
        const gradeData = data.global.map((result, index) => {
          const gradeStats = result.grade_statistics.map((stat, gradeIndex) => ({
            grade: gradeIndex,
            count: stat.count,
            percentage: stat.percentage
          }))

          // 计算该组图片的粒径范围
          const hasParticles = gradeStats.some(stat => stat.count > 0)
          
          return {
            group: index + 1,
            stats: gradeStats,
            path: result.image_path,
            contours_count: result.contours_count,
            range: hasParticles ? '0.075-2.36mm' : '无数据',
            mx: computeMX(gradeStats),
            loss: ((1 - gradeStats.reduce((sum, stat) => sum + stat.percentage, 0)) * 100).toFixed(2)
          }
        })

        // 更新组数据
        groupData.value = gradeData

        // 更新MX数据
        mxData.value = gradeData.map(group => {
          const cameraMx = parseFloat(group.mx);
          // 模拟筛分法MX值 (后续替换为真实数据)
          const randomOffset = (Math.random() * 0.2 - 0.1) * cameraMx;
          const screeningMx = cameraMx + randomOffset;
          
          return {
            group: group.group,
            cameraMx: cameraMx,
            screeningMx: parseFloat(screeningMx.toFixed(2)),
            loss: parseFloat(group.loss)
          };
        });
        filteredMxData.value = [...mxData.value];

        // 处理粒度分布数据
        if (data.global.length > 0) {
          const firstSample = data.global[0].grade_statistics;
          const gradeRanges = ['<0.075', '0.075-0.15', '0.15-0.3', '0.3-0.6', '0.6-1.18', '1.18-2.36'];
          
          distributionData.value = firstSample.map((stat, index) => {
            const cameraPercentage = (stat.percentage * 100).toFixed(2);
            // 模拟筛分法数据 (后续替换为真实数据)
            const screeningPercentage = (parseFloat(cameraPercentage) + (Math.random() * 4 - 2)).toFixed(2);
            
            return {
              range: gradeRanges[index],
              camera: cameraPercentage,
              screening: screeningPercentage,
              difference: (parseFloat(cameraPercentage) - parseFloat(screeningPercentage)).toFixed(2)
            };
          });
        }

        // 初始化只选中第一组
        selectedGroups.value = [1];
        
        ElMessage.success('数据加载成功')
        nextTick(() => {
          updateCurvesChart();
        });
      } catch (error) {
        console.error('加载数据失败:', error)
        ElMessage.error('加载数据失败: ' + error.message)
      } finally {
        loadingInstance.close()
      }
    };

    // 辅助函数：计算MX值
    const computeMX = (gradeStats) => {
      const weights = [0.075, 0.15, 0.3, 0.6, 1.18, 2.36];
      return gradeStats.reduce((mx, stat, idx) => {
        return mx + weights[idx] * stat.percentage;
      }, 0).toFixed(2);
    };

    const loadRealData = async () => {
      try {
        isLoading.value = true;
        const loadingInstance = ElLoading.service({
          fullscreen: true,
          text: '正在获取沙粒分析数据...',
          background: 'rgba(0, 0, 0, 0.7)',
        });

        const analysisParams = {
          view: 'global', // 移除本地/全局切换后固定使用全局视图
          gradeNames: [0.075, 0.15, 0.3, 0.6, 1.18, 2.36], // 示例级配
          gradeEnabled: [1, 1, 1, 1, 1, 1],
          volume_corrections: [1, 1, 1, 1, 1, 1],
        };

        const result = await sandImageApi.analyzeSandData(analysisParams);
        
        // MX Data
        if (result.mx_value !== undefined) {
             mxData.value = [{ // 假设API返回单个MX值，或者一个包含多组的数组
                group: '全局分析',
                screeningMx: result.manual_mx_value !== undefined ? result.manual_mx_value : (mxData.value[0]?.screeningMx || '-'), // 保留旧值或用API值
                cameraMx: result.mx_value,
                loss: result.mx_loss !== undefined ? result.mx_loss : (mxData.value[0]?.loss || '-') // 保留旧值或用API值
            }];
            // 如果API返回多组MX数据，则相应处理
            // mxData.value = result.mx_data_array.map(item => ({...}));
            filteredMxData.value = [...mxData.value];
        }


        // Distribution Data
        if (result.distribution && result.distribution.length > 0) {
          distributionData.value = result.distribution.map(item => ({
            range: item.range,
            screening: item.manual_percentage !== undefined ? item.manual_percentage * 100 : '-',
            camera: item.auto_percentage !== undefined ? item.auto_percentage * 100 : '-',
            difference: 0 // Will be calculated
          }));
          distributionData.value.forEach(item => {
            if (item.screening !== '-' && item.camera !== '-') {
              item.difference = (parseFloat(item.camera) - parseFloat(item.screening)).toFixed(2);
            }
          });
        }

        // Group Data for Curves (Particle Size Distribution)
        if (result.distributions && result.distributions.length > 0) {
          groupData.value = result.distributions.map((dist, index) => {
            // Check if this is the new format with points array
            if (dist.points && Array.isArray(dist.points)) {
              return {
                group: dist.group_id || index + 1,
                range: dist.range || `粒级 ${index + 1}`,
                color: ['#1890ff', '#ff9c6e', '#52c41a', '#f5222d', '#722ed1', '#a0522d'][index % 6],
                points: dist.points, // Already in the correct format
                stats: dist.grade_statistics || []
              };
            } 
            // Backward compatibility for old format
            else {
              // Generate some placeholder points based on mean and std
              const mean = dist.mean || 0;
              const std = dist.std || 1;
              const points = [];
              // Generate a simple bell curve using the mean and std
              for (let i = 0; i < 21; i++) {
                const x = mean - 3 * std + i * (6 * std / 20);
                const y = Math.exp(-0.5 * Math.pow((x - mean) / std, 2)) / (std * Math.sqrt(2 * Math.PI));
                points.push({ x, y });
              }
              return {
                group: index + 1,
                range: `粒级 ${index + 1}`,
                color: ['#1890ff', '#ff9c6e', '#52c41a', '#f5222d', '#722ed1', '#a0522d'][index % 6],
                points,
              };
            }
          });
           if (groupData.value.length === 0) { // Fallback
                groupData.value = [{ group: 1, range: 'N/A', color: '#1890ff', points: [{x:0, y:0}] }];
            }
            selectedGroups.value = groupData.value.map(g => g.group).slice(0,6);
        }


        // Error Data
        if (result.error_analysis && result.error_analysis.length > 0) {
          errorData.value = result.error_analysis.map(item => ({
            range: item.range,
            totalError: item.total_error_percentage !== undefined ? item.total_error_percentage * 100 : 0,
            previousError: item.misclassified_to_previous_percentage !== undefined ? item.misclassified_to_previous_percentage * 100 : 0,
            nextError: item.misclassified_to_next_percentage !== undefined ? item.misclassified_to_next_percentage * 100 : 0,
          }));
        }
        
        loadingInstance.close();
        isLoading.value = false;
        ElMessage.success('数据加载成功');
        await nextTick();
        initCharts();
      } catch (error) {
        console.error('加载真实数据失败:', error);
        ElMessage.error(`加载真实数据失败: ${error.message || '未知错误'}`);
        isLoading.value = false;
        if (loadingInstance) loadingInstance.close();
      }
    };


    // 粒径分布数据点
    const groupData = ref([]);

    const mxData = ref([
      { group: 1, screeningMx: 2.0, cameraMx: 2.05, loss: 7.0 },
    ]);
    const filteredMxData = ref([...mxData.value]);

    const distributionData = ref([
      { range: '0.075-0.15', screening: 20.0, camera: 18.9, difference: -1.1 },
    ]);

    const errorData = ref([
      { range: '0.15-0.3', totalError: 13.0, previousError: 0.0, nextError: 0.0 },
    ]);

    const createChart = (containerRef, options) => {
      if (!containerRef.value || !document.body.contains(containerRef.value)) {
        console.warn('Chart container is not available or not in DOM.');
        return null;
      }
      if (containerRef.value.offsetParent === null || containerRef.value.offsetWidth === 0 || containerRef.value.offsetHeight === 0) {
        console.warn('Chart container is not visible or has no dimensions.');
        return null;
      }
      try {
        const existingChart = chartInstances.find(chart => chart && chart.getDom && chart.getDom() === containerRef.value);
        if (existingChart) {
          existingChart.dispose();
          chartInstances = chartInstances.filter(chart => chart !== existingChart);
        }
        const chart = echarts.init(containerRef.value, null, { renderer: 'canvas', useDirtyRect: false });
        chart.setOption(options);
        chartInstances.push(chart);
        return chart;
      } catch (error) {
        console.error('创建图表失败:', error, containerRef.value);
        return null;
      }
    };
    
    const createCurvesChart = () => {
      if (!curvesChart.value) return null;
      try {
        const legendData = [];
        const series = [];
        
        // 筛选选中的组
        const filteredGroups = groupData.value.filter(group => 
          selectedGroups.value.includes(group.group)
        );
        
        // 定义粒径区间
        const gradeRanges = ['<0.075', '0.075-0.15', '0.15-0.3', '0.3-0.6', '0.6-1.18', '1.18-2.36'];

        // 为每个选中的组创建数据系列
        filteredGroups.forEach(group => {
          const groupName = `第 ${group.group} 组`;
          legendData.push(groupName);

          // 获取该组的各区间百分比数据
          const percentageData = group.stats.map(stat => stat.percentage * 100); // 转换为百分比

          // 添加直方图数据系列
          series.push({
            name: groupName,
            type: 'bar',
            barWidth: '40%', // 控制柱子宽度
            data: percentageData,
            itemStyle: {
              color: ['#1890ff', '#ff9c6e', '#52c41a', '#f5222d', '#722ed1', '#a0522d'][series.length % 6]
            },
            label: {
              show: true,
              position: 'top',
              formatter: '{c}%'
            }
          });
        });

        const option = {
          title: {
            text: '粒径分布直方图',
            left: 'center',
            textStyle: {
              fontSize: 16,
              color: '#333'
            },
            subtext: '各区间粒径分布百分比'
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            },
            formatter: (params) => {
              let result = `${params[0].name}<br/>`;
              params.forEach(param => {
                result += `${param.seriesName}: ${param.value.toFixed(1)}%<br/>`;
              });
              return result;
            }
          },
          legend: {
            type: 'scroll',
            orient: 'vertical',
            right: 10,
            top: 'middle',
            data: legendData
          },
          grid: {
            left: '3%',
            right: '22%',
            bottom: '8%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            name: '粒径区间 (mm)',
            nameLocation: 'middle',
            nameGap: 30,
            data: gradeRanges,
            axisLabel: {
              interval: 0,
              rotate: 30
            },
            splitLine: {
              show: true,
              lineStyle: {
                type: 'dashed',
                color: 'rgba(139, 158, 176, 0.2)'
              }
            }
          },
          yAxis: {
            type: 'value',
            name: '百分比 (%)',
            min: 0,
            max: 100,
            splitLine: {
              lineStyle: {
                type: 'dashed',
                color: 'rgba(139, 158, 176, 0.2)'
              }
            }
          },
          series: series
        };

        let chart = echarts.getInstanceByDom(curvesChart.value);
        if (!chart) {
          chart = echarts.init(curvesChart.value);
          chartInstances.push(chart);
        }
        chart.setOption(option);
        return chart;
      } catch (error) {
        console.error('创建粒径分布直方图失败:', error);
        return null;
      }
    };

    const updateCurvesChart = () => {
      if (activeTab.value !== 'curves') return;
      disposeAllCharts(); // Dispose before creating new to avoid issues
      nextTick(() => { // Ensure DOM is ready for new chart
         createCurvesChart();
      });
    };
    
    watch(selectedGroups, () => {
        if (activeTab.value === 'curves') {
            updateCurvesChart();
        }
    }, { deep: true });


    const initCharts = async () => {
      try {
        disposeAllCharts();
        await nextTick();
        setTimeout(() => { // Further delay can sometimes help with complex DOM updates
          if (document.visibilityState === 'visible') {
            createChartByTab(activeTab.value);
          }
        }, 100); // Reduced delay, 300ms might be too long
      } catch (error) {
        console.error('初始化图表时出错:', error);
      }
    };

    const createChartByTab = (tab) => {
      disposeAllCharts(); // Ensure previous charts are cleared
      nextTick(() => {
        try {
          const containerMap = {
            mx: mxComparisonChart.value,
            distribution: distributionChart.value,
            error: errorChart.value,
            curves: curvesChart.value,
          };
          if (!containerMap[tab] || !document.body.contains(containerMap[tab])) {
             console.warn(`Container for tab ${tab} not ready.`);
            return;
          }
          switch (tab) {
            case 'mx': createMxChart(); break;
            case 'distribution': createDistributionChart(); break;
            case 'error': createErrorChart(); break;
            case 'curves': createCurvesChart(); break;
          }
        } catch (error) {
          console.error(`创建图表失败 for tab ${tab}:`, error);
        }
      });
    };

    const handleTabChange = (tabName) => {
      // activeTab is already updated by v-model
      createChartByTab(tabName);
    };

    const disposeAllCharts = () => {
      chartInstances.forEach(chart => {
        if (chart && typeof chart.dispose === 'function') {
          try {
            chart.dispose();
          } catch (e) {
            console.warn('图表清理异常:', e);
          }
        }
      });
      chartInstances = [];
    };
    
    // =========================================================================
    // Correctly defined chart creation functions and other methods
    // =========================================================================

    const createMxChart = () => {
      if (!mxComparisonChart.value) return null;
      try {
        const options = {
          title: {
            text: '筛分法MX值与双相机MX值对比',
            textStyle: { color: '#333', fontSize: 16 }
          },
          tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
          legend: { data: ['筛分法MX', '双相机MX', 'Loss'], textStyle: { color: '#333' } },
          grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
          xAxis: [
            {
              type: 'category',
              data: filteredMxData.value.map(item => item.group),
              name: '土组样本对比',
              axisLine: { lineStyle: { color: '#8b9eb0' } },
              axisLabel: { color: '#333' }
            },
          ],
          yAxis: [
            {
              type: 'value', name: 'MX值', position: 'left',
              axisLine: { lineStyle: { color: '#8b9eb0' } },
              axisLabel: { color: '#333' },
              splitLine: { lineStyle: { color: 'rgba(139, 158, 176, 0.1)' } }
            },
            {
              type: 'value', name: 'Loss (%)', position: 'right',
              axisLine: { lineStyle: { color: '#8b9eb0' } },
              axisLabel: { color: '#333' },
              splitLine: { show: false }
            }
          ],
          series: [
            { name: '筛分法MX', type: 'bar', data: filteredMxData.value.map(item => item.screeningMx), itemStyle: { color: '#5470c6' } },
            { name: '双相机MX', type: 'bar', data: filteredMxData.value.map(item => item.cameraMx), itemStyle: { color: '#fac858' } },
            { name: 'Loss', type: 'line', yAxisIndex: 1, data: filteredMxData.value.map(item => item.loss), itemStyle: { color: '#91cc75' }, lineStyle: { width: 2 }, symbol: 'circle', symbolSize: 8 }
          ]
        };
        return createChart(mxComparisonChart, options);
      } catch (error) {
        console.error('创建MX图表失败:', error);
        return null;
      }
    };

    const createDistributionChart = () => {
      if (!distributionChart.value) return null;
      try {
        const options = {
          title: { 
            text: '筛分法与双相机粒径分布对比',
            subtext: '各区间粒径分布百分比对比',
            textStyle: { color: '#333', fontSize: 16 },
            subtextStyle: { color: '#666', fontSize: 12 }
          },
          tooltip: { 
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: (params) => {
              let result = `${params[0].name}<br/>`;
              params.forEach(param => {
                if (param.seriesName === '误差') {
                  result += `${param.seriesName}: ${param.value > 0 ? '+' : ''}${param.value}%<br/>`;
                } else {
                  result += `${param.seriesName}: ${param.value}%<br/>`;
                }
              });
              return result;
            }
          },
          legend: {
            data: ['筛分法', '双相机', '误差'],
            textStyle: { color: '#333' },
            selected: {
              '筛分法': true,
              '双相机': true,
              '误差': true
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
              data: distributionData.value.map(item => item.range),
              name: '粒径范围 (mm)',
              nameLocation: 'middle',
              nameGap: 30,
              axisLine: { lineStyle: { color: '#8b9eb0' } },
              axisLabel: {
                color: '#333',
                rotate: 30,
                interval: 0
              },
              splitLine: {
                show: true,
                lineStyle: {
                  type: 'dashed',
                  color: 'rgba(139, 158, 176, 0.2)'
                }
              }
            }
          ],
          yAxis: [
            {
              type: 'value',
              name: '百分比 (%)',
              position: 'left',
              min: 0,
              max: function(value) {
                return Math.ceil(value.max * 1.1);
              },
              axisLine: { lineStyle: { color: '#8b9eb0' } },
              axisLabel: { color: '#333' },
              splitLine: { lineStyle: { color: 'rgba(139, 158, 176, 0.1)' } }
            },
            {
              type: 'value',
              name: '误差 (%)',
              position: 'right',
              axisLine: { lineStyle: { color: '#8b9eb0' } },
              axisLabel: {
                color: '#333',
                formatter: (value) => {
                  return `${value > 0 ? '+' : ''}${value}%`;
                }
              },
              splitLine: { show: false }
            }
          ],
          series: [
            {
              name: '筛分法',
              type: 'bar',
              data: distributionData.value.map(item => parseFloat(item.screening)),
              itemStyle: { color: '#5470c6' },
              barGap: '0%',
              label: {
                show: true,
                position: 'top',
                formatter: '{c}%'
              }
            },
            {
              name: '双相机',
              type: 'bar',
              data: distributionData.value.map(item => parseFloat(item.camera)),
              itemStyle: { color: '#91cc75' },
              label: {
                show: true,
                position: 'top',
                formatter: '{c}%'
              }
            },
            {
              name: '误差',
              type: 'line',
              yAxisIndex: 1,
              data: distributionData.value.map(item => parseFloat(item.difference)),
              itemStyle: { color: '#ee6666' },
              lineStyle: { width: 2 },
              symbol: 'circle',
              symbolSize: 8,
              label: {
                show: true,
                position: 'top',
                formatter: (params) => {
                  return `${params.value > 0 ? '+' : ''}${params.value}%`;
                }
              }
            }
          ]
        };

        return createChart(distributionChart, options);
      } catch (error) {
        console.error('创建分布图表失败:', error);
        return null;
      }
    };

    const createErrorChart = () => {
      if (!errorChart.value) return null;
      try {
        const options = {
          title: { text: '不同粒径区间的错误分类概率对比', textStyle: { color: '#333', fontSize: 16 } },
          tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
          legend: { data: ['总错误分类概率', '错误分类到前一个区间', '错误分类到后一个区间'], textStyle: { color: '#333' } },
          grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
          xAxis: {
            type: 'category',
            data: errorData.value.map(item => item.range),
            name: '粒径范围 (mm)',
            axisLine: { lineStyle: { color: '#8b9eb0' } },
            axisLabel: { color: '#333' }
          },
          yAxis: {
            type: 'value', name: '错误分类概率 (%)',
            axisLine: { lineStyle: { color: '#8b9eb0' } },
            axisLabel: { color: '#333' },
            splitLine: { lineStyle: { color: 'rgba(139, 158, 176, 0.1)' } }
          },
          series: [
            { name: '总错误分类概率', data: errorData.value.map(item => item.totalError), type: 'line', smooth: true, lineStyle: { width: 3 }, symbol: 'circle', symbolSize: 10, itemStyle: { color: '#91cc75' } },
            { name: '错误分类到前一个区间', type: 'bar', stack: 'total', data: errorData.value.map(item => item.previousError), itemStyle: { color: '#fac858' } },
            { name: '错误分类到后一个区间', type: 'bar', stack: 'total', data: errorData.value.map(item => item.nextError), itemStyle: { color: '#ee6666' } }
          ]
        };
        return createChart(errorChart, options);
      } catch (error) {
        console.error('创建误差图表失败:', error);
        return null;
      }
    };

    const exportImage = () => {
      let activeChartInstance = null;
      // Find the chart instance for the currently active tab
      const activeChartRefMap = {
        curves: curvesChart.value,
        mx: mxComparisonChart.value,
        distribution: distributionChart.value,
        error: errorChart.value,
      };
      const activeChartDom = activeChartRefMap[activeTab.value];
      if (activeChartDom) {
        activeChartInstance = chartInstances.find(inst => inst.getDom() === activeChartDom);
      }

      if (activeChartInstance) {
        try {
          const url = activeChartInstance.getDataURL({
            type: 'png',
            pixelRatio: 2,
            backgroundColor: '#fff' // Use white background for better compatibility
          });
          const link = document.createElement('a');
          link.download = `数据报表_${activeTab.value}_${new Date().toISOString().split('T')[0]}.png`;
          link.href = url;
          link.click();
        } catch (error) {
          console.error('导出图片失败:', error);
          ElMessage.error('导出图片失败，请重试');
        }
      } else {
        ElMessage.warning('当前标签页没有可导出的图表或图表未初始化。');
      }
    };

    const exportData = () => {
      const wb = XLSX.utils.book_new();
      const mxWs = XLSX.utils.json_to_sheet(filteredMxData.value); // Use filtered data for MX
      XLSX.utils.book_append_sheet(wb, mxWs, 'MX值对比');
      const distributionWs = XLSX.utils.json_to_sheet(distributionData.value);
      XLSX.utils.book_append_sheet(wb, distributionWs, '粒径分布');
      const errorWs = XLSX.utils.json_to_sheet(errorData.value);
      XLSX.utils.book_append_sheet(wb, errorWs, '误差分析');

      // 添加粒径分布曲线的源数据
      groupData.value.forEach(group => {
        const pointsData = group.points.map(p => ({粒径_mm: p.x, 百分比: p.y}));
        const groupWs = XLSX.utils.json_to_sheet(pointsData);
        XLSX.utils.book_append_sheet(wb, groupWs, `曲线数据_组${group.group}`);
      });
      
      const summaryData = [
        ['报告生成日期', new Date().toLocaleDateString()],
        ['总样本数 (MX)', mxData.value.length > 0 ? mxData.value.length : 'N/A'],
        ['平均筛分法MX', mxData.value.length > 0 ? (mxData.value.reduce((sum, item) => sum + (parseFloat(item.screeningMx) || 0), 0) / mxData.value.length).toFixed(2) : 'N/A'],
        ['平均双相机MX', mxData.value.length > 0 ? (mxData.value.reduce((sum, item) => sum + (parseFloat(item.cameraMx) || 0), 0) / mxData.value.length).toFixed(2) : 'N/A'],
        ['平均Loss', mxData.value.length > 0 ? (mxData.value.reduce((sum, item) => sum + (parseFloat(item.loss) || 0), 0) / mxData.value.length).toFixed(2) + '%' : 'N/A']
      ];
      const summaryWs = XLSX.utils.aoa_to_sheet(summaryData);
      XLSX.utils.book_append_sheet(wb, summaryWs, '报告摘要');

      const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      saveAs(new Blob([wbout], { type: 'application/octet-stream' }), `数据分析报告_${new Date().toISOString().split('T')[0]}.xlsx`);
    };

    const printReport = () => {
      ElMessage.info('正在准备打印...');
      nextTick(() => { window.print(); });
    };
    
    const loadLatestData = () => {
      // loadRealData(); // Prefer more specific API if available
      loadProcessingResults(); // Reload the latest data
    };

    const applyFilter = () => {
      try {
        if (filterGroups.value === 'all') {
          filteredMxData.value = [...mxData.value];
        } else {
          const count = parseInt(filterGroups.value);
          if (mxData.value.length > 0) { // Check if mxData has items
             const startIdx = Math.max(0, mxData.value.length - count);
             filteredMxData.value = mxData.value.slice(startIdx);
          } else {
            filteredMxData.value = [];
          }
        }
        if (activeTab.value === 'mx') {
          disposeAllCharts();
          setTimeout(() => { createMxChart(); }, 100);
        }
        ElMessage.success(`已应用筛选: ${filterGroups.value === 'all' ? '全部' : `最近${filterGroups.value}组`}数据`);
      } catch (error) {
        console.error('应用筛选失败:', error);
        ElMessage.error('应用筛选失败，请重试');
      }
    };

    const resetFilter = () => {
      try {
        filterDate.value = [];
        filterGroups.value = 'all';
        filteredMxData.value = [...mxData.value];
        if (activeTab.value === 'mx') {
          disposeAllCharts();
          setTimeout(() => { createMxChart(); }, 100);
        }
        ElMessage.info('已重置筛选条件');
      } catch (error) {
        console.error('重置筛选失败:', error);
        ElMessage.error('重置筛选失败，请重试');
      }
    };

    // Dummy function from original code, ensure it's defined if called anywhere (though it's not)
    const generateTestImages = () => { console.log("generateTestImages called"); };
    const handleHover = (img, index) => { if(imageData.value[index]) imageData.value[index].hovering = true; };
    const handleHoverEnd = (index) => { if(imageData.value[index]) imageData.value[index].hovering = false; };
    
    // 处理窗口调整大小的函数
    const handleResize = () => {
      if (document.visibilityState === 'visible') {
        chartInstances.forEach(chart => {
          if (chart && chart.getDom && document.body.contains(chart.getDom())) {
            try {
              requestAnimationFrame(() => { chart.resize(); });
            } catch (e) { console.warn('调整图表大小失败:', e); }
          }
        });
      }
    };
    
    const debouncedResize = () => {
      if (resizeTimeout) clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(handleResize, 200);
    };
    
    // 处理可见性变化的函数
    const visibilityHandler = () => {
      if (document.visibilityState === 'visible') {
        if (initTimeout) clearTimeout(initTimeout);
        initTimeout = setTimeout(initCharts, 200); // Re-init charts when tab becomes visible
      }
    };
    
    onMounted(() => {
      loadProcessingResults(); // Load initial data
      window.addEventListener('resize', debouncedResize);
      document.addEventListener('visibilitychange', visibilityHandler);
    });

    onUnmounted(() => {
      if (resizeTimeout) clearTimeout(resizeTimeout);
      if (initTimeout) clearTimeout(initTimeout);
      window.removeEventListener('resize', debouncedResize);
      document.removeEventListener('visibilitychange', visibilityHandler);
      disposeAllCharts();
    });

    watch(activeTab, (newTab) => {
      handleTabChange(newTab);
    });

    // Removed watch for filterDate and filterGroups as applyFilter is manual

    return {
      activeTab, mxComparisonChart, distributionChart, errorChart, curvesChart,
      filterDate, filterGroups,
      groupData, curveDisplayMode, selectedGroups, 
      mxData, filteredMxData, distributionData, errorData, imageData, // imageData and imageRefs not used in template but kept for consistency
      imageRefs,
      
      exportData, exportImage, printReport,
      applyFilter, resetFilter, loadLatestData,
      updateCurvesChart,
      // Dummy/unused functions if needed by other parts or for future use
      generateTestImages, handleHover, handleHoverEnd, 
      // Chart creation functions are internal, not typically returned unless for testing/specific needs
      // createMxChart, createDistributionChart, createErrorChart, createCurvesChart,
    };
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
  height: 100%; /* Ensure chart div takes full height of its container */
}

/* Custom table styles */
.custom-table {
  --el-table-border-color: #e5e7eb;
  --el-table-border: 1px solid #e5e7eb;
  --el-table-text-color: #374151;
  --el-table-header-text-color: #1d4ed8;
  --el-table-row-hover-bg-color: #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* Custom tab styles */
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

/* Custom checkbox styles */
:deep(.custom-checkbox .el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}
:deep(.custom-checkbox .el-checkbox__label) { /* Ensure label color updates correctly */
  color: #333; /* Default label color */
}
:deep(.custom-checkbox .el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #1d4ed8;
}


/* Custom radio button styles */
:deep(.custom-radio .el-radio-button__inner) {
  background: #f9fafb;
  border-color: #d1d5db;
  color: #4b5563;
}

:deep(.custom-radio .el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
  color: white;
  box-shadow: -1px 0 0 0 #1d4ed8; /* Check this shadow if it causes issues */
}

/* Print styles */
@media print {
  .report-header,
  .data-filter,
  .control-panel,
  .el-tabs__header,
  .el-button, .el-button-group { /* Hide buttons too */
    display: none !important;
  }

  .chart-container {
    page-break-inside: avoid;
    margin-bottom: 20px;
    border: 1px solid #ccc !important; /* Light border for print */
    box-shadow: none !important;
    padding: 10px !important;
  }
  
  .chart {
    height: 300px !important; /* Fixed height for print consistency */
  }

  .data-table {
    page-break-inside: avoid;
    margin-bottom: 20px;
  }

  .el-table {
    width: 100% !important;
    font-size: 10pt !important; /* Smaller font for print */
  }

  .el-table th,
  .el-table td {
    padding: 4px !important;
    border: 1px solid #ddd !important;
  }
  
  .el-table th {
    background-color: #f0f0f0 !important; /* Light gray header for print */
    color: #000 !important;
  }

  .report-content {
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
  }

  h2, h3, h4 { /* Adjust heading sizes for print */
    font-size: 14pt !important;
    margin-bottom: 8px !important;
    color: #000 !important;
  }
  h3 { font-size: 12pt !important; }
  h4 { font-size: 11pt !important; }

  body, .data-report { /* Ensure full width for printing */
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
}
</style>