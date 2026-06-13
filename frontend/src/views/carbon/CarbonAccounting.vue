<template>
  <div class="page-container">
    <div class="page-header">
      <div class="header-left">
        <h2>碳排放核算</h2>
        <p>厂区碳足迹追踪 · 排放源贡献分析 · 减排目标监控</p>
      </div>
      <div class="header-right">
        <a-select
          v-model="selectedYear"
          style="width: 130px;"
          @change="handleYearChange"
        >
          <a-option v-for="y in yearOptions" :key="y" :value="y">{{ y }} 年</a-option>
        </a-select>
      </div>
    </div>

    <a-card class="summary-card" :bordered="false">
      <div class="summary-content">
        <div class="progress-section">
          <div class="progress-header">
            <span class="progress-title">年度累计排放量 vs 减排目标</span>
            <a-tag color="green" v-if="emissionProgress <= 100">进度良好</a-tag>
            <a-tag color="orange" v-else>需加强减排</a-tag>
          </div>
          <div class="progress-main">
            <div class="progress-value-row">
              <div class="progress-value-item">
                <span class="value-label">累计排放</span>
                <span class="value-number emission">{{ formatNumber(summaryData.cumulativeEmission) }}</span>
                <span class="value-unit">t CO₂e</span>
              </div>
              <div class="progress-value-item">
                <span class="value-label">减排目标</span>
                <span class="value-number target">{{ formatNumber(summaryData.reductionTarget) }}</span>
                <span class="value-unit">t CO₂e</span>
              </div>
              <div class="progress-value-item">
                <span class="value-label">剩余预算</span>
                <span class="value-number" :class="remainingBudget >= 0 ? 'budget-safe' : 'budget-risk'">
                  {{ formatNumber(Math.abs(remainingBudget)) }}
                </span>
                <span class="value-unit">t CO₂e {{ remainingBudget >= 0 ? '' : '超支' }}</span>
              </div>
              <div class="progress-value-item">
                <span class="value-label">同比变化</span>
                <span class="value-number" :class="summaryData.yoyChange <= 0 ? 'down' : 'up'">
                  {{ summaryData.yoyChange > 0 ? '+' : '' }}{{ summaryData.yoyChange }}%
                </span>
                <span class="value-unit">{{ summaryData.yoyChange <= 0 ? '下降' : '上升' }}</span>
              </div>
            </div>
            <a-progress
              :percent="Math.min(emissionProgress, 100)"
              :show-text="false"
              style="margin-top: 20px;"
              :stroke-color="emissionProgress > 100 ? '#F53F3F' : emissionProgress > 80 ? '#FF7D00' : '#00B42A'"
            />
            <div class="progress-scale">
              <span>0</span>
              <span>{{ formatNumber(summaryData.reductionTarget * 0.25) }}</span>
              <span>{{ formatNumber(summaryData.reductionTarget * 0.5) }}</span>
              <span>{{ formatNumber(summaryData.reductionTarget * 0.75) }}</span>
              <span>{{ formatNumber(summaryData.reductionTarget) }}</span>
            </div>
          </div>
        </div>
      </div>
    </a-card>

    <a-row :gutter="16" class="stats-row">
      <a-col :span="6" v-for="(stat, idx) in emissionStats" :key="idx">
        <a-card class="stat-card" :bordered="false">
          <div class="stat-icon" :style="{ background: stat.bgColor, color: stat.color }">
            <component :is="stat.icon" />
          </div>
          <div class="stat-content">
            <span class="stat-label">{{ stat.label }}</span>
            <div class="stat-value-row">
              <span class="stat-value">{{ formatNumber(stat.value) }}</span>
              <span class="stat-unit">t CO₂e</span>
            </div>
            <div class="stat-change" :class="stat.change <= 0 ? 'down' : 'up'">
              <icon-arrow-down v-if="stat.change <= 0" />
              <icon-arrow-up v-else />
              {{ Math.abs(stat.change) }}% 同比
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16">
      <a-col :span="12">
        <a-card title="各排放源月度贡献" :bordered="false">
          <template #extra>
            <a-radio-group v-model="chartViewType" type="button" size="small">
              <a-radio value="stack">堆叠</a-radio>
              <a-radio value="group">分组</a-radio>
            </a-radio-group>
          </template>
          <div ref="sourceBarRef" style="height: 380px;"></div>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="同比变化趋势" :bordered="false">
          <template #extra>
            <span class="trend-note">较{{ selectedYear - 1 }}年同期</span>
          </template>
          <div ref="yoyChartRef" style="height: 380px;"></div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px;">
      <a-col :span="14">
        <a-card title="排放源构成占比" :bordered="false">
          <a-row :gutter="16">
            <a-col :span="12">
              <div ref="pieChartRef" style="height: 320px;"></div>
            </a-col>
            <a-col :span="12">
              <div class="source-legend">
                <div
                  v-for="(item, idx) in sourceBreakdown"
                  :key="idx"
                  class="source-legend-item"
                >
                  <div class="legend-dot" :style="{ background: sourceColors[idx] }"></div>
                  <div class="legend-info">
                    <div class="legend-name">{{ item.name }}</div>
                    <div class="legend-meta">
                      <span class="legend-value">{{ formatNumber(item.value) }} t</span>
                      <span class="legend-percent">{{ item.percent }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
      <a-col :span="10">
        <a-card title="活动量明细" :bordered="false">
          <a-table
            :columns="activityColumns"
            :data="activityTableData"
            :pagination="false"
            size="small"
            border
          >
            <template #emission="{ record }">
              <span class="emission-cell">{{ formatNumber(record.emission) }} t</span>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, markRaw } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

interface MonthlySourceData {
  month: string
  electricity: number
  chemical: number
  sludge: number
  gas: number
  transport: number
}

interface SourceBreakdownItem {
  name: string
  value: number
  percent: number
}

const sourceColors = ['#165DFF', '#00B42A', '#FF7D00', '#722ED1', '#F53F3F']
const sourceNames = ['厂区电耗', '药剂消耗', '污泥外运', '天然气', '运输车辆']

const selectedYear = ref(dayjs().year())
const yearOptions = computed(() => {
  const cur = dayjs().year()
  return [cur, cur - 1, cur - 2, cur - 3]
})

const chartViewType = ref('stack')

const summaryData = ref({
  cumulativeEmission: 0,
  reductionTarget: 0,
  yoyChange: 0
})

const sourceBreakdown = ref<SourceBreakdownItem[]>([])
const monthlySourceData = ref<MonthlySourceData[]>([])
const yoyMonthlyData = ref<{ month: string; current: number; lastYear: number; change: number }[]>([])

const emissionProgress = computed(() => {
  if (!summaryData.value.reductionTarget) return 0
  return (summaryData.value.cumulativeEmission / summaryData.value.reductionTarget) * 100
})

const remainingBudget = computed(() => {
  return summaryData.value.reductionTarget - summaryData.value.cumulativeEmission
})

const emissionStats = computed(() => {
  const breakdown = sourceBreakdown.value
  const stats = [
    {
      label: sourceNames[0],
      value: breakdown[0]?.value || 0,
      change: -3.2,
      icon: markRaw({ render: () => '⚡' }),
      bgColor: 'rgba(22, 93, 255, 0.1)',
      color: '#165DFF'
    },
    {
      label: sourceNames[1],
      value: breakdown[1]?.value || 0,
      change: 1.8,
      icon: markRaw({ render: () => '🧪' }),
      bgColor: 'rgba(0, 180, 42, 0.1)',
      color: '#00B42A'
    },
    {
      label: sourceNames[2],
      value: breakdown[2]?.value || 0,
      change: -5.5,
      icon: markRaw({ render: () => '♻️' }),
      bgColor: 'rgba(255, 125, 0, 0.1)',
      color: '#FF7D00'
    },
    {
      label: sourceNames[3],
      value: breakdown[3]?.value || 0,
      change: -2.1,
      icon: markRaw({ render: () => '🔥' }),
      bgColor: 'rgba(114, 46, 209, 0.1)',
      color: '#722ED1'
    }
  ]
  const total = stats.reduce((acc, s) => acc + s.value, 0)
  if (breakdown[4]) {
    stats.push({
      label: sourceNames[4],
      value: breakdown[4].value,
      change: 0.6,
      icon: markRaw({ render: () => '🚛' }),
      bgColor: 'rgba(245, 63, 63, 0.1)',
      color: '#F53F3F'
    })
  }
  return stats.slice(0, 4)
})

const activityTableData = ref([
  { source: '厂区电耗', activity: 286540, unit: 'kWh', factor: '0.6101 kgCO₂e/kWh', emission: 175.02 },
  { source: 'PAC药剂', activity: 4850, unit: 'kg', factor: '2.1 kgCO₂e/kg', emission: 10.19 },
  { source: 'PAM药剂', activity: 1260, unit: 'kg', factor: '3.8 kgCO₂e/kg', emission: 4.79 },
  { source: '污泥外运', activity: 3120, unit: '吨·公里', factor: '0.096 kgCO₂e/t·km', emission: 299.52 },
  { source: '天然气', activity: 18600, unit: 'm³', factor: '2.1622 kgCO₂e/m³', emission: 40.22 },
  { source: '车辆运输', activity: 15800, unit: 'L', factor: '2.68 kgCO₂e/L', emission: 42.34 }
])

const activityColumns = [
  { title: '排放源', dataIndex: 'source', width: 120 },
  { title: '活动量', dataIndex: 'activity', width: 100, align: 'right' as const },
  { title: '单位', dataIndex: 'unit', width: 90 },
  { title: '排放因子', dataIndex: 'factor', width: 160 },
  { title: 'CO₂e 排放', slotName: 'emission', width: 110, align: 'right' as const }
]

const sourceBarRef = ref<HTMLElement>()
const yoyChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()

let sourceBarChart: echarts.ECharts | null = null
let yoyChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

function formatNumber(n: number): string {
  if (n >= 10000) {
    return (n / 10000).toFixed(2) + '万'
  }
  return n.toFixed(2)
}

function generateMockData(year: number) {
  const isCurrentYear = year === dayjs().year()
  const months = isCurrentYear ? dayjs().month() + 1 : 12
  const monthlyData: MonthlySourceData[] = []
  const monthlyTotalsCurrent: number[] = []
  const monthlyTotalsLast: number[] = []
  const yoyData: typeof yoyMonthlyData.value = []

  const baseLine = {
    electricity: [120, 115, 125, 130, 145, 160, 175, 180, 165, 140, 128, 118],
    chemical: [10, 11, 12, 11, 13, 14, 15, 14, 13, 12, 11, 10],
    sludge: [18, 20, 22, 25, 28, 32, 35, 33, 28, 24, 20, 18],
    gas: [3, 3.2, 3.5, 3.8, 4, 4.2, 4.5, 4.4, 4, 3.6, 3.3, 3],
    transport: [3.2, 3.5, 3.8, 4, 4.2, 4.5, 4.8, 4.6, 4.2, 3.8, 3.5, 3.2]
  }

  for (let i = 0; i < months; i++) {
    const variance = 0.92 + (year - 2023) * 0.015
    const row: MonthlySourceData = {
      month: `${i + 1}月`,
      electricity: baseLine.electricity[i] * variance,
      chemical: baseLine.chemical[i] * variance,
      sludge: baseLine.sludge[i] * variance,
      gas: baseLine.gas[i] * variance,
      transport: baseLine.transport[i] * variance
    }
    monthlyData.push(row)
    const total = row.electricity + row.chemical + row.sludge + row.gas + row.transport
    monthlyTotalsCurrent.push(Number(total.toFixed(2)))

    const lastTotal = total * (1.05 + Math.random() * 0.04)
    monthlyTotalsLast.push(Number(lastTotal.toFixed(2)))
    yoyData.push({
      month: `${i + 1}月`,
      current: Number(total.toFixed(2)),
      lastYear: Number(lastTotal.toFixed(2)),
      change: Number(((total - lastTotal) / lastTotal * 100).toFixed(2))
    })
  }

  const cumulative = monthlyTotalsCurrent.reduce((a, b) => a + b, 0)
  const lastYearCum = monthlyTotalsLast.reduce((a, b) => a + b, 0)

  const breakdown: SourceBreakdownItem[] = [
    { name: sourceNames[0], value: monthlyData.reduce((a, b) => a + b.electricity, 0), percent: 0 },
    { name: sourceNames[1], value: monthlyData.reduce((a, b) => a + b.chemical, 0), percent: 0 },
    { name: sourceNames[2], value: monthlyData.reduce((a, b) => a + b.sludge, 0), percent: 0 },
    { name: sourceNames[3], value: monthlyData.reduce((a, b) => a + b.gas, 0), percent: 0 },
    { name: sourceNames[4], value: monthlyData.reduce((a, b) => a + b.transport, 0), percent: 0 }
  ]

  breakdown.forEach(item => {
    item.percent = Number((item.value / cumulative * 100).toFixed(1))
    item.value = Number(item.value.toFixed(2))
  })

  const target = 2000 * (1 - 0.05 * (year - 2023))

  summaryData.value = {
    cumulativeEmission: Number(cumulative.toFixed(2)),
    reductionTarget: Number(target.toFixed(2)),
    yoyChange: Number(((cumulative - lastYearCum) / lastYearCum * 100).toFixed(2))
  }

  sourceBreakdown.value = breakdown
  monthlySourceData.value = monthlyData
  yoyMonthlyData.value = yoyData
}

function renderSourceBar() {
  if (!sourceBarRef.value) return
  if (!sourceBarChart) {
    sourceBarChart = echarts.init(sourceBarRef.value)
  }
  const months = monthlySourceData.value.map(d => d.month)
  const stackMode = chartViewType.value === 'stack'
  sourceBarChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any[]) => {
        let html = `<strong>${params[0].axisValue}</strong><br/>`
        let total = 0
        params.forEach(p => {
          html += `${p.marker} ${p.seriesName}: ${p.value.toFixed(2)} t<br/>`
          total += p.value
        })
        html += `<hr style="margin:4px 0;border-color:#eee"/>合计: ${total.toFixed(2)} t`
        return html
      }
    },
    legend: {
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12
    },
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: '#e5e6eb' } },
      axisLabel: { color: '#4e5969' }
    },
    yAxis: {
      type: 'value',
      name: 't CO₂e',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f2f3f5', type: 'dashed' } },
      axisLabel: { color: '#4e5969' }
    },
    series: sourceNames.map((name, idx) => ({
      name,
      type: 'bar',
      stack: stackMode ? 'total' : undefined,
      data: monthlySourceData.value.map(d => Number((d as any)[['electricity', 'chemical', 'sludge', 'gas', 'transport'][idx]]).toFixed(2)),
      itemStyle: {
        color: sourceColors[idx],
        borderRadius: stackMode ? 0 : [4, 4, 0, 0]
      },
      emphasis: { focus: 'series' }
    }))
  })
}

function renderYoyChart() {
  if (!yoyChartRef.value) return
  if (!yoyChart) {
    yoyChart = echarts.init(yoyChartRef.value)
  }
  const months = yoyMonthlyData.value.map(d => d.month)
  yoyChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        const change = yoyMonthlyData.value[params[0].dataIndex].change
        return `<strong>${params[0].axisValue}</strong><br/>` +
          params.map(p => `${p.marker} ${p.seriesName}: ${p.value.toFixed(2)} t`).join('<br/>') +
          `<hr style="margin:4px 0;border-color:#eee"/>同比变化: <span style="color:${change <= 0 ? '#00B42A' : '#F53F3F'}">${change > 0 ? '+' : ''}${change}%</span>`
      }
    },
    legend: {
      bottom: 0,
      itemWidth: 12,
      itemHeight: 12
    },
    grid: { left: 50, right: 50, top: 20, bottom: 50 },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: '#e5e6eb' } },
      axisLabel: { color: '#4e5969' }
    },
    yAxis: [
      {
        type: 'value',
        name: 't CO₂e',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#f2f3f5', type: 'dashed' } },
        axisLabel: { color: '#4e5969' }
      },
      {
        type: 'value',
        name: '同比 %',
        axisLine: { show: false },
        splitLine: { show: false },
        axisLabel: {
          color: '#4e5969',
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: `${selectedYear.value}年`,
        type: 'line',
        smooth: true,
        data: yoyMonthlyData.value.map(d => d.current),
        lineStyle: { width: 3, color: '#165DFF' },
        itemStyle: { color: '#165DFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(22, 93, 255, 0.25)' },
            { offset: 1, color: 'rgba(22, 93, 255, 0.02)' }
          ])
        },
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: `${selectedYear.value - 1}年`,
        type: 'line',
        smooth: true,
        data: yoyMonthlyData.value.map(d => d.lastYear),
        lineStyle: { width: 2, color: '#86909c', type: 'dashed' },
        itemStyle: { color: '#86909c' },
        symbol: 'circle',
        symbolSize: 5
      },
      {
        name: '同比变化',
        type: 'bar',
        yAxisIndex: 1,
        data: yoyMonthlyData.value.map(d => ({
          value: d.change,
          itemStyle: { color: d.change <= 0 ? '#00B42A' : '#F53F3F' }
        })),
        barWidth: 12,
        itemStyle: { borderRadius: [3, 3, 0, 0] },
        tooltip: { show: false }
      }
    ]
  })
}

function renderPieChart() {
  if (!pieChartRef.value) return
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value)
  }
  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} t ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 600,
          formatter: '{b}\n{d}%'
        },
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.15)'
        }
      },
      data: sourceBreakdown.value.map((item, idx) => ({
        name: item.name,
        value: item.value,
        itemStyle: { color: sourceColors[idx] }
      }))
    }]
  })
}

function handleYearChange() {
  generateMockData(selectedYear.value)
  nextTick(() => {
    renderSourceBar()
    renderYoyChart()
    renderPieChart()
  })
}

watch(chartViewType, () => {
  renderSourceBar()
})

onMounted(() => {
  generateMockData(selectedYear.value)
  nextTick(() => {
    renderSourceBar()
    renderYoyChart()
    renderPieChart()
  })

  window.addEventListener('resize', () => {
    sourceBarChart?.resize()
    yoyChart?.resize()
    pieChart?.resize()
  })
})
</script>

<style scoped>
.page-container {
  min-height: 100%;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e6eb;
}

.header-left h2 {
  margin: 0 0 4px 0;
  font-size: 22px;
  font-weight: 600;
  color: #1d2129;
}

.header-left p {
  margin: 0;
  font-size: 13px;
  color: #86909c;
}

.summary-card {
  margin-bottom: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f4ff 50%, #f0fdf4 100%);
  position: relative;
  overflow: hidden;
}

.summary-card::before {
  content: '';
  position: absolute;
  top: -60px;
  right: -60px;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 180, 42, 0.12) 0%, transparent 70%);
  pointer-events: none;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.progress-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.progress-value-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.progress-value-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.value-label {
  font-size: 12px;
  color: #86909c;
}

.value-number {
  font-size: 26px;
  font-weight: 700;
  color: #1d2129;
  line-height: 1.2;
}

.value-number.emission {
  color: #165DFF;
}

.value-number.target {
  color: #722ED1;
}

.value-number.budget-safe {
  color: #00B42A;
}

.value-number.budget-risk {
  color: #F53F3F;
}

.value-number.down {
  color: #00B42A;
}

.value-number.up {
  color: #F53F3F;
}

.value-unit {
  font-size: 12px;
  color: #86909c;
}

.progress-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 11px;
  color: #86909c;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 10px;
  height: 100%;
}

.stat-card :deep(.arco-card-body) {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: #86909c;
  display: block;
}

.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin: 2px 0;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1d2129;
}

.stat-unit {
  font-size: 11px;
  color: #86909c;
}

.stat-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.stat-change.down {
  color: #00B42A;
}

.stat-change.up {
  color: #F53F3F;
}

.trend-note {
  font-size: 12px;
  color: #86909c;
}

.source-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.source-legend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f7f8fa;
  transition: background 0.2s;
}

.source-legend-item:hover {
  background: #eef0f3;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-info {
  flex: 1;
  min-width: 0;
}

.legend-name {
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
  margin-bottom: 2px;
}

.legend-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.legend-value {
  color: #4e5969;
}

.legend-percent {
  color: #165DFF;
  font-weight: 600;
}

.emission-cell {
  color: #165DFF;
  font-weight: 500;
}
</style>
