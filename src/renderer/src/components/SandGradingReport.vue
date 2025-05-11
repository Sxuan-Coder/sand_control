<template>
  <div class="sand-grading-report bg-white text-gray-900">
    <div class="report-header bg-gray-100 p-3 rounded-md mb-4">
      <h2 class="text-blue-700 mb-2">机制砂级配检测报告</h2>
      <div class="report-actions flex items-center justify-between">
        <el-button-group>
          <el-button
            type="primary"
            size="small"
            @click="generateRandomData"
            class="bg-blue-600 hover:bg-blue-700"
          >
            <el-icon><Refresh /></el-icon>
            AI建议
          </el-button>
          <el-button
            type="success"
            size="small"
            @click="exportPDF"
            class="bg-green-600 hover:bg-green-700"
          >
            <el-icon><Printer /></el-icon>
            打印报告
          </el-button>
          <el-button
            type="warning"
            size="small"
            @click="exportAsImage"
            class="bg-amber-500 hover:bg-amber-600"
          >
            <el-icon><Picture /></el-icon>
            导出长图片
          </el-button>
        </el-button-group>
        <el-checkbox v-model="showLineChart" class="ml-4 text-gray-700">显示级配曲线图</el-checkbox>
      </div>
    </div>

    <!-- 报告内容 -->
    <div
      class="mx-auto py-4 px-3 print-container bg-white border border-gray-200 rounded-md shadow-sm"
    >
      <!-- 标题和报告编号 -->
      <div class="mb-3 border-b-2 border-blue-600 pb-2 flex items-center justify-between">
        <h1 class="text-xl font-bold text-blue-800">机制砂级配检测报告</h1>
        <div class="flex items-center">
          <span class="text-sm font-bold mr-2 text-gray-700">报告编号: {{ reportNumber }}</span>
          <!-- 二维码 -->
          <div
            class="w-10 h-10 bg-white flex items-center justify-center border border-gray-300 rounded-sm"
          >
            <img
              :src="`https://api.qrserver.com/v1/create-qr-code/?size=70x70&data=${reportNumber}`"
              alt="报告二维码"
              class="w-full h-full"
            />
          </div>
        </div>
      </div>

      <!-- 描述信息区域 - 段落布局 -->
      <div class="mb-2 text-xs leading-4">
        <p class="mb-0.5">
          <strong>送检单位：</strong>中交一公局集团有限公司
          <strong class="ml-2">送检人：</strong>王强 <strong class="ml-2">采样时间：</strong
          >{{ currentDateTime }}
        </p>
        <p class="mb-0.5">
          <strong>收样时间：</strong>{{ currentDateTime }}
          <strong class="ml-2">采样批次编号：</strong>{{ Math.floor(Math.random() * 1000) }}
          <strong class="ml-2">样品编号：</strong>{{ Math.floor(Math.random() * 100) }}
        </p>
        <p class="mb-0.5">
          <strong>检测人：</strong>张明 <strong class="ml-2">检测时间：</strong
          >{{ currentDateTime }} <strong class="ml-2">报告时间：</strong>{{ currentDateTime }}
        </p>
        <p class="mb-0.5">
          <strong>复核人：</strong>李华 <strong class="ml-2">审核人：</strong>吴涛
        </p>
      </div>

      <!-- 检测结果摘要 -->
      <div class="mb-2 bg-gray-100 border-l-4 border-blue-600 p-1 relative">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <p class="text-xs mr-3">
              <strong>细度模数：</strong><span class="font-bold">{{ fineModulus }}</span>
            </p>
            <p class="text-xs flex items-center">
              <strong>检测结论：</strong>
              <span
                class="font-bold ml-1"
                :class="{
                  'text-green-700':
                    parseFloat(fineModulus) >= 2.3 && parseFloat(fineModulus) <= 3.7,
                  'text-red-600': parseFloat(fineModulus) < 2.3 || parseFloat(fineModulus) > 3.7
                }"
              >
                {{
                  parseFloat(fineModulus) >= 2.3 && parseFloat(fineModulus) <= 3.7
                    ? '合格'
                    : '不合格'
                }}
              </span>
            </p>
          </div>
        </div>
      </div>

      <!-- 级配表格 - 不分栏 -->
      <div class="mb-2">
        <h2 class="text-xs font-semibold mb-1 text-blue-800">级配表格</h2>
        <table class="w-full border-collapse border border-gray-400 text-xs">
          <thead class="bg-gray-200">
            <tr>
              <th class="border px-1 py-0.5">粒径 (mm)</th>
              <th
                v-for="(category, index) in reportData.categories"
                :key="index"
                class="border px-1 py-0.5"
              >
                {{ category }}
              </th>
            </tr>
          </thead>
          <tbody class="text-center">
            <tr>
              <td class="border px-1 py-0.5 font-semibold">占比 (%)</td>
              <td
                v-for="(percentage, index) in reportData.percentages"
                :key="index"
                class="border px-1 py-0.5"
              >
                {{ percentage.toFixed(2) }}
              </td>
            </tr>
            <tr>
              <td class="border px-1 py-0.5 font-semibold">累计占比 (%)</td>
              <td
                v-for="(cumulative, index) in reportData.cumulative"
                :key="index"
                class="border px-1 py-0.5"
              >
                {{ cumulative.toFixed(2) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 级配曲线图 -->
      <div v-if="showLineChart" class="mb-2">
        <h2 class="text-xs font-semibold mb-1 text-blue-800">级配曲线图</h2>
        <div
          id="lineChartContainer"
          ref="lineChartRef"
          class="border border-gray-200 bg-gray-50 chart-container print-chart rounded-sm shadow-sm"
          style="height: 200px; overflow: hidden"
        >
          <!-- 静态折线图用于打印 -->
          <img id="staticLineChart" class="static-chart" alt="机制砂级配曲线图" />
        </div>
      </div>

      <!-- 标准解释部分和饼图正确布局 -->
      <div class="flex gap-2 mb-2">
        <!-- 左侧标准解释部分 -->
        <div class="w-2/3">
          <h2 class="text-xs font-semibold mb-1 text-blue-800">标准解释</h2>
          <div class="border border-gray-400 p-1 bg-gray-50 text-xs leading-4 rounded-sm">
            <div class="flex mb-1">
              <div class="w-full pr-1">
                <p class="font-semibold mb-0.5">机制砂分类标准（GB/T 14684-2022）：</p>
                <table class="w-full border border-gray-400 text-xs">
                  <thead class="bg-gray-200">
                    <tr>
                      <th class="border px-1 py-0.5">砂的类别</th>
                      <th class="border px-1 py-0.5">细度模数范围</th>
                      <th class="border px-1 py-0.5">特点</th>
                    </tr>
                  </thead>
                  <tbody class="text-center">
                    <tr>
                      <td class="border px-1 py-0.5">粗砂</td>
                      <td
                        class="border px-1 py-0.5"
                        :class="{
                          'bg-gray-200':
                            parseFloat(fineModulus) >= 3.1 && parseFloat(fineModulus) <= 3.7
                        }"
                      >
                        3.7~3.1
                      </td>
                      <td class="border px-1 py-0.5">粒径较大，表面积小</td>
                    </tr>
                    <tr>
                      <td class="border px-1 py-0.5">中砂</td>
                      <td
                        class="border px-1 py-0.5"
                        :class="{
                          'bg-gray-200':
                            parseFloat(fineModulus) >= 2.3 && parseFloat(fineModulus) < 3.1
                        }"
                      >
                        3.0~2.3
                      </td>
                      <td class="border px-1 py-0.5">粒径中等，性能均衡</td>
                    </tr>
                    <tr>
                      <td class="border px-1 py-0.5">细砂</td>
                      <td
                        class="border px-1 py-0.5"
                        :class="{
                          'bg-gray-200':
                            parseFloat(fineModulus) >= 1.6 && parseFloat(fineModulus) < 2.3
                        }"
                      >
                        2.2~1.6
                      </td>
                      <td class="border px-1 py-0.5">粒径较小，表面积大</td>
                    </tr>
                    <tr>
                      <td class="border px-1 py-0.5">特细砂</td>
                      <td
                        class="border px-1 py-0.5"
                        :class="{
                          'bg-gray-200':
                            parseFloat(fineModulus) >= 0.7 && parseFloat(fineModulus) < 1.6
                        }"
                      >
                        1.5~0.7
                      </td>
                      <td class="border px-1 py-0.5">粒径极小，需水量大</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="border border-gray-400 p-1 bg-gray-50 mb-1 rounded-sm">
              <p class="font-semibold mb-0.5 text-blue-800">细度模数计算方法：</p>
              <p class="mb-0.5">细度模数(MF) = (各筛孔累计筛余百分率之和) ÷ 100</p>
              <p class="mb-0.5">本样品计算：</p>
              <p class="mb-0.5">
                MF = ({{ reportData.cumulative.map((val) => (100 - val).toFixed(2)).join(' + ') }} +
                100) ÷ 100 = {{ fineModulus }}
              </p>
            </div>
            <p class="font-semibold mb-0.5 mt-1 text-blue-800">机制砂质量要求（部分）：</p>
            <ul class="list-disc pl-4 space-y-0.5">
              <li>石粉含量(&lt;0.075mm)：Ⅰ类≤3.0%，Ⅱ类≤5.0%，Ⅲ类≤7.0%</li>
              <li>压碎值指标：≤26%（高强混凝土）；≤30%（普通混凝土）</li>
              <li>MB值：≤1.4（高性能混凝土）；≤1.8（普通混凝土）</li>
            </ul>
          </div>
        </div>

        <!-- 右侧饼图 -->
        <div class="w-1/3 h-full">
          <h2 class="text-xs font-semibold mb-1 text-blue-800">粒径占比饼图</h2>
          <div
            id="pieChartContainer"
            ref="pieChartRef"
            class="border border-gray-200 bg-gray-50 chart-container print-chart rounded-sm shadow-sm"
            style="height: 180px; overflow: hidden"
          >
            <!-- 静态饼图用于打印 -->
            <img id="staticPieChart" class="static-chart" alt="机制砂粒径占比饼图" />
          </div>
        </div>
      </div>

      <!-- AI建议区域 - 不分栏 -->
      <div class="mb-2">
        <h2 class="text-xs font-semibold mb-1 text-blue-800">AI智能分析建议</h2>
        <div class="border border-green-200 p-2 bg-green-50 text-xs leading-4 rounded-sm">
          <!-- 加载动画 -->
          <div v-if="aiLoading" class="flex justify-center items-center py-4">
            <el-progress
              type="circle"
              :percentage="100"
              :width="50"
              :stroke-width="4"
              status="success"
              indeterminate
            />
            <span class="ml-3 text-gray-600">正在分析数据，请稍候...</span>
          </div>
          <!-- AI建议内容 -->
          <div v-else>
            <p class="font-semibold mb-0.5 text-blue-800">分析结论：</p>
            <p>{{ aiRecommendation.conclusion }}</p>

            <p class="font-semibold mb-0.5 mt-1 text-blue-800">优化建议：</p>
            <ol class="list-decimal pl-4 space-y-0.5">
              <li
                v-for="(suggestion, index) in aiRecommendation.optimizationSuggestions"
                :key="index"
              >
                {{ suggestion }}
              </li>
            </ol>

            <p class="font-semibold mb-0.5 mt-1 text-green-800">应用适宜性：</p>
            <p>{{ aiRecommendation.applicationSuitability }}</p>
          </div>
        </div>
      </div>

      <!-- 页脚区域 - 包含条码和报告编号 -->
      <div class="flex justify-between items-center border-t pt-2 mt-2">
        <div class="flex items-center space-x-2">
          <!-- 条码 -->
          <div class="w-24 h-10 bg-gray-200 flex items-center justify-center border">
            <svg xmlns="http://www.w3.org/2000/svg" width="80" height="30" viewBox="0 0 80 30">
              <rect x="5" y="5" width="1" height="20" fill="black" />
              <rect x="8" y="5" width="1" height="20" fill="black" />
              <rect x="12" y="5" width="2" height="20" fill="black" />
              <rect x="16" y="5" width="1" height="20" fill="black" />
              <rect x="20" y="5" width="1" height="20" fill="black" />
              <rect x="24" y="5" width="2" height="20" fill="black" />
              <rect x="28" y="5" width="1" height="20" fill="black" />
              <rect x="32" y="5" width="1" height="20" fill="black" />
              <rect x="36" y="5" width="2" height="20" fill="black" />
              <rect x="40" y="5" width="1" height="20" fill="black" />
              <rect x="44" y="5" width="2" height="20" fill="black" />
              <rect x="48" y="5" width="1" height="20" fill="black" />
              <rect x="52" y="5" width="1" height="20" fill="black" />
              <rect x="56" y="5" width="2" height="20" fill="black" />
              <rect x="60" y="5" width="1" height="20" fill="black" />
              <rect x="64" y="5" width="1" height="20" fill="black" />
              <rect x="68" y="5" width="2" height="20" fill="black" />
              <rect x="72" y="5" width="1" height="20" fill="black" />
            </svg>
          </div>
          <span class="text-xs">{{ reportNumber }}</span>
        </div>
        <p class="text-xs text-gray-500">2023 ICDIO检验中心</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Printer, Picture } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import html2canvas from 'html2canvas'
import { chatWithXfyun } from '../api'

export default {
  name: 'SandGradingReport',
  components: {
    Refresh,
    Printer,
    Picture
  },
  setup() {
    const showLineChart = ref(true)
    const reportData = ref({
      categories: [
        '<0.075',
        '0.075~0.15',
        '0.15~0.3',
        '0.3~0.6',
        '0.6~1.18',
        '1.18~2.36',
        '2.36~4.75'
      ],
      percentages: [5.2, 7.36, 13.25, 18.4, 22.65, 25.84, 7.3],
      cumulative: [5.2, 12.56, 25.81, 44.21, 66.86, 92.7, 100.0]
    })
    const fineModulus = ref('2.54')
    const reportNumber = ref('ICDIO-2025-0425-001')
    const pieChartRef = ref(null)
    const lineChartRef = ref(null)
    const currentDateTime = ref('2025-04-25 14:30')
    let pieChart = null
    let lineChart = null

    // AI建议加载状态
    const aiLoading = ref(false)

    // AI建议
    const aiRecommendation = ref({
      conclusion:
        '本次检测的机制砂样品细度模数为2.54，符合中砂级配范围。粒径分布呈现明显的中间粒级含量高、两端粒级含量低的特征。其中1.18~2.36占比最高，达25.84%，0.6~1.18次之，为22.65%。',
      optimizationSuggestions: [
        '当前级配中细粉含量(<0.075mm)为5.20%，处于合理范围内，有利于提高混凝土的和易性。',
        '中间粒级(0.3~2.36mm)含量较高(66.89%)，有利于减少孔隙率，但可考虑适当增加2.36~4.75mm粒级含量，以完善机制砂级配的连续性。',
        '建议在混凝土配合比设计时，可适当调整水灰比和掺合料用量，以充分发挥当前机制砂级配特点的优势。'
      ],
      applicationSuitability:
        '当前级配的机制砂适合应用于C25-C40强度等级的普通混凝土工程，如建筑结构、路面等。细度模数为2.54的中砂特性使其具有良好的工作性能，适合大多数常规混凝土应用场景。'
    })

    // 生成随机数据
    const generateRandomData = () => {
      // 显示AI加载状态
      aiLoading.value = true

      // 生成随机百分比，总和为100
      let percentages = []
      let total = 0

      // 生成随机数
      for (let i = 0; i < 7; i++) {
        const rand = Math.random() * 20 + 5
        percentages.push(rand)
        total += rand
      }

      // 归一化，使总和为100
      const normalizedPercentages = percentages.map((p) =>
        parseFloat(((p / total) * 100).toFixed(2))
      )

      // 确保总和为100
      let sum = normalizedPercentages.reduce((a, b) => a + b, 0)
      if (sum !== 100) {
        const diff = 100 - sum
        normalizedPercentages[0] += diff
        normalizedPercentages[0] = parseFloat(normalizedPercentages[0].toFixed(2))
      }

      // 计算累计值
      const cumulativeValues = []
      let cumulative = 0
      for (let i = 0; i < normalizedPercentages.length; i++) {
        cumulative += normalizedPercentages[i]
        cumulativeValues.push(parseFloat(cumulative.toFixed(2)))
      }

      // 更新数据
      reportData.value = {
        categories: [
          '<0.075',
          '0.075~0.15',
          '0.15~0.3',
          '0.3~0.6',
          '0.6~1.18',
          '1.18~2.36',
          '2.36~4.75'
        ],
        percentages: normalizedPercentages,
        cumulative: cumulativeValues
      }

      // 更新细度模数
      calculateFineModulus()

      // 更新报告编号
      reportNumber.value = `ICDIO-2025-0425-${Math.floor(Math.random() * 1000)}`

      // 更新当前日期时间
      const now = new Date()
      currentDateTime.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`

      // 通过API获取AI建议
      generateAIRecommendation()

      // 重新渲染图表
      nextTick(() => {
        if (pieChart) {
          initPieChart()
        }
        if (lineChart && showLineChart.value) {
          initLineChart()
        }
      })
    }

    // 计算细度模数
    const calculateFineModulus = () => {
      // 细度模数 = (各筛孔累计筛余百分率之和) ÷ 100
      const cumulativeRetained = reportData.value.cumulative.map((val) => 100 - val)
      const sum = cumulativeRetained.reduce((acc, val) => acc + val, 0) + 100
      fineModulus.value = (sum / 100).toFixed(2)
    }

    // 通过API获取AI建议
    const generateAIRecommendation = async () => {
      try {
        // 准备发送给AI的数据
        const fm = parseFloat(fineModulus.value)
        let sandType = ''

        if (fm >= 3.7) {
          sandType = '超粗砂'
        } else if (fm >= 3.1) {
          sandType = '粗砂'
        } else if (fm >= 2.3) {
          sandType = '中砂'
        } else if (fm >= 1.6) {
          sandType = '细砂'
        } else if (fm >= 0.7) {
          sandType = '特细砂'
        } else {
          sandType = '极细砂'
        }

        // 计算中间粒级含量
        const midSizeContent =
          reportData.value.percentages[3] +
          reportData.value.percentages[4] +
          reportData.value.percentages[5]
        const midSizeContentStr = midSizeContent.toFixed(2)

        // 细粉含量
        const fineContent = reportData.value.percentages[0].toFixed(2)

        // 构建提示词
        const prompt = `
作为一名专业的砂石级配分析专家，请根据以下机制砂级配数据进行分析并给出专业建议：

1. 细度模数：${fm}，砂类型：${sandType}
2. 粒径分布数据（百分比）：
   - <0.075mm: ${reportData.value.percentages[0].toFixed(2)}%
   - 0.075~0.15mm: ${reportData.value.percentages[1].toFixed(2)}%
   - 0.15~0.3mm: ${reportData.value.percentages[2].toFixed(2)}%
   - 0.3~0.6mm: ${reportData.value.percentages[3].toFixed(2)}%
   - 0.6~1.18mm: ${reportData.value.percentages[4].toFixed(2)}%
   - 1.18~2.36mm: ${reportData.value.percentages[5].toFixed(2)}%
   - 2.36~4.75mm: ${reportData.value.percentages[6].toFixed(2)}%
3. 中间粒级(0.3~2.36mm)含量：${midSizeContentStr}%
4. 细粉含量(<0.075mm)：${fineContent}%

请提供以下三部分内容：
1. 分析结论：对当前级配特点的简要总结，包括细度模数是否符合砂类型范围、粒径分布特征等。
2. 优化建议：针对当前级配提出3点具体改进建议，包括如何调整各粒径含量以优化级配。
3. 应用适宜性：说明当前级配的机制砂适合应用的混凝土类型和工程场景。

请确保回答专业、简洁，每部分不超过100字。回答格式为JSON，包含conclusion、optimizationSuggestions（数组）和applicationSuitability三个字段。
`

        // 调用API获取AI建议
        const response = await chatWithXfyun(prompt)

        try {
          // 尝试解析JSON
          const aiResponse = JSON.parse(response)
          aiRecommendation.value = {
            conclusion: aiResponse.conclusion || '无法获取分析结论',
            optimizationSuggestions: aiResponse.optimizationSuggestions || ['无法获取优化建议'],
            applicationSuitability: aiResponse.applicationSuitability || '无法获取应用适宜性分析'
          }
        } catch (parseError) {
          console.error('解析AI响应失败:', parseError)

          // 如果解析失败，使用本地生成的建议
          generateLocalAIRecommendation()
        }
      } catch (error) {
        console.error('获取AI建议失败:', error)
        ElMessage.error('获取AI建议失败，将使用本地生成的建议')

        // 如果API调用失败，使用本地生成的建议
        generateLocalAIRecommendation()
      } finally {
        // 隐藏加载状态
        aiLoading.value = false
      }
    }

    // 生成本地AI建议（作为备用）
    const generateLocalAIRecommendation = () => {
      const fm = parseFloat(fineModulus.value)
      let sandType = ''

      if (fm >= 3.7) {
        sandType = '超粗砂'
      } else if (fm >= 3.1) {
        sandType = '粗砂'
      } else if (fm >= 2.3) {
        sandType = '中砂'
      } else if (fm >= 1.6) {
        sandType = '细砂'
      } else if (fm >= 0.7) {
        sandType = '特细砂'
      } else {
        sandType = '极细砂'
      }

      // 计算中间粒级含量
      const midSizeContent =
        reportData.value.percentages[3] +
        reportData.value.percentages[4] +
        reportData.value.percentages[5]
      const midSizeContentStr = midSizeContent.toFixed(2)

      // 细粉含量
      const fineContent = reportData.value.percentages[0].toFixed(2)

      // 生成结论
      const conclusion = `本次检测的机制砂样品细度模数为${fm}，${fm >= 3.7 ? '超出' : '符合'}${sandType}级配范围。粒径分布呈现明显的中间粒级含量高、两端粒级含量低的特征。其中1.18~2.36占比最高，达${reportData.value.percentages[5].toFixed(2)}%，0.6~1.18次之，为${reportData.value.percentages[4].toFixed(2)}%。`

      // 生成优化建议
      const suggestions = [
        `当前级配中细粉含量(<0.075mm)为${fineContent}%，${parseFloat(fineContent) > 7 ? '偏高，应适当降低以减少用水量，建议控制在7%以下' : '处于合理范围内，有利于提高混凝土的和易性'}。`,
        `中间粒级(0.3~2.36mm)含量${parseFloat(midSizeContentStr) > 60 ? '较高' : '适中'}(${midSizeContentStr}%)，有利于减少孔隙率，但可考虑适当${parseFloat(reportData.value.percentages[6].toFixed(2)) < 10 ? '增加2.36~4.75mm粒级含量，以完善机制砂级配的连续性' : '平衡各粒径含量，提高级配的均匀性'}。`,
        `建议在混凝土配合比设计时，可适当调整水灰比和掺合料用量，以充分发挥当前机制砂级配特点的优势。`
      ]

      // 生成应用适宜性
      let suitability = ''
      if (fm >= 3.7) {
        suitability = `当前级配的机制砂适合应用于C40以上强度等级的混凝土工程，如高强度混凝土结构、重要水工建筑等。细度模数为${fm}的${sandType}特性使其具有较高的强度发展能力，但需注意提高混凝土的和易性。`
      } else if (fm >= 3.1) {
        suitability = `当前级配的机制砂适合应用于C30-C50强度等级的普通混凝土工程，如建筑结构、路面、一般水工建筑等。细度模数为${fm}的${sandType}特性使其具有良好的工作性能和力学性能平衡，可获得较好的混凝土和易性和强度发展。`
      } else if (fm >= 2.3) {
        suitability = `当前级配的机制砂适合应用于C25-C40强度等级的普通混凝土工程，如建筑结构、路面等。细度模数为${fm}的${sandType}特性使其具有良好的工作性能，适合大多数常规混凝土应用场景。`
      } else {
        suitability = `当前级配的机制砂适合应用于对和易性要求较高、强度要求不太高的混凝土工程，如抹灰砂浆、填充混凝土等。细度模数为${fm}的${sandType}特性使其需水量较大，但具有良好的粘聚性和可泵性。`
      }

      // 更新AI建议
      aiRecommendation.value = {
        conclusion,
        optimizationSuggestions: suggestions,
        applicationSuitability: suitability
      }
    }

    // 初始化饼图
    const initPieChart = () => {
      if (!pieChartRef.value) return

      // 如果已经初始化，则销毁
      if (pieChart) {
        pieChart.dispose()
      }

      // 确保DOM元素已经渲染
      nextTick(() => {
        try {
          console.log('初始化饼图', pieChartRef.value)
          pieChart = echarts.init(pieChartRef.value)

          // 为饼图准备数据
          const pieData = reportData.value.categories.map((category, index) => {
            return {
              name: category,
              value: reportData.value.percentages[index]
            }
          })

          // 饼图配置
          const pieOption = {
            tooltip: {
              trigger: 'item',
              formatter: '{b}: {c}% ({d}%)'
            },
            legend: {
              orient: 'vertical',
              right: 10,
              top: 'center',
              itemWidth: 10,
              itemHeight: 10,
              textStyle: {
                fontSize: 8
              }
            },
            series: [
              {
                name: '粒径占比',
                type: 'pie',
                radius: ['30%', '70%'],
                center: ['40%', '50%'],
                avoidLabelOverlap: false,
                itemStyle: {
                  borderRadius: 4,
                  borderColor: '#fff',
                  borderWidth: 1
                },
                label: {
                  show: false
                },
                emphasis: {
                  label: {
                    show: false
                  }
                },
                labelLine: {
                  show: false
                },
                data: pieData
              }
            ]
          }

          // 设置饼图配置并渲染
          pieChart.setOption(pieOption)

          // 创建静态饼图用于打印
          setTimeout(() => {
            try {
              const pieImgUrl = pieChart.getDataURL({
                type: 'png',
                pixelRatio: 2,
                backgroundColor: '#fff'
              })
              const staticPieImg = document.getElementById('staticPieChart')
              if (staticPieImg) {
                staticPieImg.src = pieImgUrl
              }
            } catch (e) {
              console.error('生成饼图静态图失败:', e)
            }
          }, 500)
        } catch (e) {
          console.error('饼图初始化失败:', e)
        }
      })
    }

    // 初始化折线图
    const initLineChart = () => {
      if (!lineChartRef.value) return

      // 如果已经初始化，则销毁
      if (lineChart) {
        lineChart.dispose()
      }

      lineChart = echarts.init(lineChartRef.value)

      // 折线图配置
      const lineOption = {
        grid: {
          left: 60,
          right: 20,
          bottom: 60,
          top: 20
        },
        xAxis: {
          type: 'category',
          data: reportData.value.categories,
          axisLabel: {
            rotate: 30,
            fontSize: 10,
            interval: 0
          },
          name: '粒径 (mm)',
          nameLocation: 'middle',
          nameGap: 35,
          nameTextStyle: {
            fontSize: 10
          }
        },
        yAxis: {
          type: 'value',
          name: '累计百分比 (%)',
          nameLocation: 'middle',
          nameGap: 40,
          nameTextStyle: {
            fontSize: 10
          },
          splitLine: {
            lineStyle: {
              color: '#ddd'
            }
          },
          max: 100
        },
        series: [
          {
            name: '累计百分比',
            type: 'line',
            data: reportData.value.cumulative,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              color: '#666',
              type: 'solid'
            },
            itemStyle: {
              color: '#666',
              borderWidth: 1,
              borderColor: '#fff'
            },
            label: {
              show: true,
              position: 'top',
              formatter: '{c}%',
              fontSize: 9,
              color: '#000'
            }
          }
        ]
      }

      // 设置折线图配置并渲染
      lineChart.setOption(lineOption)

      // 创建静态折线图用于打印
      setTimeout(() => {
        try {
          const lineImgUrl = lineChart.getDataURL({
            type: 'png',
            pixelRatio: 2,
            backgroundColor: '#fff'
          })
          const staticLineImg = document.getElementById('staticLineChart')
          if (staticLineImg) {
            staticLineImg.src = lineImgUrl
          }
        } catch (e) {
          console.error('生成折线图静态图失败:', e)
        }
      }, 500)
    }

    // 导出为PDF
    const exportPDF = () => {
      // 确保图表已经渲染完成
      nextTick(() => {
        // 更新静态图表用于打印
        if (pieChart) {
          try {
            const pieImgUrl = pieChart.getDataURL({
              type: 'png',
              pixelRatio: 2,
              backgroundColor: '#fff'
            })
            const staticPieImg = document.getElementById('staticPieChart')
            if (staticPieImg) {
              staticPieImg.src = pieImgUrl
            }
          } catch (e) {
            console.error('生成饼图静态图失败:', e)
          }
        }

        if (lineChart && showLineChart.value) {
          try {
            const lineImgUrl = lineChart.getDataURL({
              type: 'png',
              pixelRatio: 2,
              backgroundColor: '#fff'
            })
            const staticLineImg = document.getElementById('staticLineChart')
            if (staticLineImg) {
              staticLineImg.src = lineImgUrl
            }
          } catch (e) {
            console.error('生成折线图静态图失败:', e)
          }
        }

        // 延迟一下确保图片加载完成
        setTimeout(() => {
          window.print()
        }, 500)
      })
    }

    // 导出为长图片
    const exportAsImage = async () => {
      try {
        ElMessage.info('正在生成图片，请稍候...')

        // 确保图表已经渲染完成
        await nextTick()

        const printContainer = document.querySelector('.print-container')

        if (!printContainer) {
          ElMessage.error('未找到报告容器')
          return
        }

        // 使用html2canvas将报告转换为图片
        const canvas = await html2canvas(printContainer, {
          scale: 2, // 提高清晰度
          useCORS: true, // 允许加载跨域图片
          logging: false,
          backgroundColor: '#ffffff'
        })

        // 将canvas转换为图片并下载
        const imgData = canvas.toDataURL('image/png')
        const link = document.createElement('a')
        link.href = imgData
        link.download = `砂级配报告_${reportNumber.value}.png`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        ElMessage.success('图片已生成并下载')
      } catch (error) {
        console.error('导出图片失败:', error)
        ElMessage.error('导出图片失败，请重试')
      }
    }

    // 监听窗口大小变化
    const handleResize = () => {
      if (pieChart) {
        pieChart.resize()
      }
      if (lineChart) {
        lineChart.resize()
      }
    }

    onMounted(() => {
      // 初始化图表
      nextTick(() => {
        initPieChart()
        if (showLineChart.value) {
          initLineChart()
        }
      })

      // 监听窗口大小变化
      window.addEventListener('resize', handleResize)

      // 监听打印前事件
      window.addEventListener('beforeprint', () => {
        // 更新静态图表用于打印
        if (pieChart) {
          try {
            const pieImgUrl = pieChart.getDataURL({
              type: 'png',
              pixelRatio: 2,
              backgroundColor: '#fff'
            })
            const staticPieImg = document.getElementById('staticPieChart')
            if (staticPieImg) {
              staticPieImg.src = pieImgUrl
            }
          } catch (e) {
            console.error('生成饼图静态图失败:', e)
          }
        }

        if (lineChart && showLineChart.value) {
          try {
            const lineImgUrl = lineChart.getDataURL({
              type: 'png',
              pixelRatio: 2,
              backgroundColor: '#fff'
            })
            const staticLineImg = document.getElementById('staticLineChart')
            if (staticLineImg) {
              staticLineImg.src = lineImgUrl
            }
          } catch (e) {
            console.error('生成折线图静态图失败:', e)
          }
        }
      })
    })

    return {
      showLineChart,
      reportData,
      fineModulus,
      reportNumber,
      pieChartRef,
      lineChartRef,
      currentDateTime,
      aiRecommendation,
      aiLoading,
      generateRandomData,
      exportPDF,
      exportAsImage
    }
  }
}
</script>

<style scoped>
.sand-grading-report {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.print-container {
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 5px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 21cm;
  margin: 0 auto;
  padding: 15px;
}

.chart-container {
  height: 180px;
  background-color: #fff;
}

/* 打印样式 */
@media print {
  @page {
    size: A4;
    margin: 0.5cm;
  }

  body {
    font-size: 12px !important;
    line-height: 1.3 !important;
  }

  .report-header {
    display: none !important;
  }

  .print-container {
    width: 100% !important;
    max-width: none !important;
    min-height: auto !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    box-shadow: none !important;
    page-break-after: avoid !important;
    page-break-before: avoid !important;
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }

  /* 防止重复打印 */
  .sand-grading-report {
    page-break-after: avoid !important;
    page-break-before: avoid !important;
    page-break-inside: avoid !important;
  }

  /* 保持布局一致性 */
  .flex {
    display: flex !important;
  }

  .items-center {
    align-items: center !important;
  }

  .justify-between {
    justify-content: space-between !important;
  }

  /* 确保标题和报告编号在同一行 */
  h1 {
    font-size: 18px !important;
    margin: 0 !important;
    font-weight: bold !important;
  }

  h2 {
    font-size: 16px !important;
    margin: 0 0 4px 0 !important;
    font-weight: bold !important;
  }

  /* 调整二维码大小 */
  .w-10,
  .h-10 {
    width: 70px !important;
    height: 70px !important;
  }

  /* 调整基本信息段落 */
  .leading-4 {
    line-height: 1.4 !important;
  }

  .mb-0\.5 {
    margin-bottom: 2px !important;
  }

  .ml-2 {
    margin-left: 8px !important;
  }

  /* 调整表格样式 */
  table {
    border-collapse: collapse !important;
    width: 100% !important;
    margin-bottom: 8px !important;
  }

  td,
  th {
    padding: 4px 6px !important;
    font-size: 11px !important;
    border: 1px solid #000 !important;
  }

  /* 确保图表在打印时可见 */
  .chart-container {
    height: 180px !important;
    width: 100% !important;
    page-break-inside: avoid;
    margin-bottom: 8px !important;
  }

  /* 减小各部分间距 */
  .mb-2 {
    margin-bottom: 6px !important;
  }

  .mb-3 {
    margin-bottom: 10px !important;
  }

  .p-1 {
    padding: 4px !important;
  }

  .gap-2 {
    gap: 8px !important;
  }

  /* 确保所有文本大小一致 */
  .text-xs {
    font-size: 11px !important;
  }

  .text-sm {
    font-size: 12px !important;
  }

  /* 黑白打印优化 */
  .print-chart {
    -webkit-print-color-adjust: exact !important;
  }

  /* 确保所有颜色在黑白打印时有足够对比度 */
  .text-red-600 {
    color: #000 !important;
    font-weight: bold !important;
  }

  .text-green-700 {
    color: #000 !important;
    font-weight: bold !important;
  }

  .border-blue-700 {
    border-color: #666 !important;
  }

  table th {
    background-color: #ddd !important;
  }

  /* 确保生成的静态图表图像能正常显示 */
  .static-chart {
    width: 100%;
    height: auto;
    display: none;
  }

  .static-chart {
    display: block;
    max-height: 180px;
  }

  .chart-container > div {
    display: none;
  }

  /* 确保SVG图标在打印时显示正确 */
  svg {
    fill: black !important;
    width: 12px !important;
    height: 12px !important;
  }

  /* 确保合格图标显示正确 */
  .hege-icon {
    width: 50px !important;
    height: 50px !important;
    opacity: 0.8 !important;
  }
}
</style>
