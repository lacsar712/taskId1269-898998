<template>
  <div class="page-container">
    <div class="page-header">
      <h2>成本中心台账</h2>
      <p>按成本中心归集运营费用，分析各工艺单元成本结构与控费空间</p>
    </div>

    <a-card class="filter-card">
      <a-form :model="filterForm" layout="inline">
        <a-form-item label="统计月份">
          <a-month-picker v-model="filterForm.month" style="width: 200px;" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="fetchData">
            <template #icon><icon-search /></template>
            查询
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <div class="cost-summary">
      <div class="cost-card">
        <div class="cost-icon" style="background: linear-gradient(135deg, #165DFF, #14C9C9);">
          <icon-dollar />
        </div>
        <div class="cost-info">
          <div class="cost-label">总运营费用</div>
          <div class="cost-value">{{ summary.totalCost.toLocaleString() }}<span class="cost-unit">元</span></div>
          <div class="cost-trend up">较上月 {{ summary.totalGrowth }}</div>
        </div>
      </div>
      <div class="cost-card">
        <div class="cost-icon" style="background: linear-gradient(135deg, #00B42A, #7BE188);">
          <icon-thunderbolt />
        </div>
        <div class="cost-info">
          <div class="cost-label">电费合计</div>
          <div class="cost-value">{{ summary.electricityCost.toLocaleString() }}<span class="cost-unit">元</span></div>
          <div class="cost-trend up">占比 {{ summary.electricityRatio }}%</div>
        </div>
      </div>
      <div class="cost-card">
        <div class="cost-icon" style="background: linear-gradient(135deg, #FF7D00, #FFCF8B);">
          <icon-experiment />
        </div>
        <div class="cost-info">
          <div class="cost-label">药剂费合计</div>
          <div class="cost-value">{{ summary.chemicalCost.toLocaleString() }}<span class="cost-unit">元</span></div>
          <div class="cost-trend down">占比 {{ summary.chemicalRatio }}%</div>
        </div>
      </div>
      <div class="cost-card">
        <div class="cost-icon" style="background: linear-gradient(135deg, #722ED1, #D3ADF7);">
          <icon-user />
        </div>
        <div class="cost-info">
          <div class="cost-label">单位水成本</div>
          <div class="cost-value">{{ summary.unitWaterCost }}<span class="cost-unit">元/m³</span></div>
          <div class="cost-trend down">较上月 -2.3%</div>
        </div>
      </div>
    </div>

    <div class="charts-section">
      <a-card style="margin-bottom: 16px;">
        <template #title>月度费用走势</template>
        <div ref="trendChartRef" style="height: 360px;"></div>
      </a-card>

      <div class="charts-row">
        <a-card>
          <template #title>各成本中心费用占比</template>
          <div ref="pieChartRef" style="height: 320px;"></div>
        </a-card>
        <a-card>
          <template #title>费用构成分析</template>
          <div ref="compositionChartRef" style="height: 320px;"></div>
        </a-card>
      </div>
    </div>

    <a-card style="margin-top: 16px;">
      <template #title>
        <span>成本中心费用明细</span>
        <span style="font-size: 13px; color: #86909c; margin-left: 8px; font-weight: normal;">
          点击行可下钻查看费用构成明细
        </span>
      </template>
      <a-table
        :columns="costCenterColumns"
        :data="costCenterList"
        :loading="loading"
        @row-class-name="(_, index) => `table-row-${index}`"
        @row-click="handleRowClick"
      >
        <template #totalCost="{ record }">
          <span style="font-weight: 600; color: #165DFF;">{{ record.totalCost.toLocaleString() }}</span>
        </template>
        <template #percentage="{ record }">
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="flex: 1;">
              <a-progress :percent="record.percentage" :show-text="false" :stroke-color="#165DFF" />
            </div>
            <span style="min-width: 45px;">{{ record.percentage }}%</span>
          </div>
        </template>
        <template #electricity="{ record }">
          {{ record.electricity.toLocaleString() }}
        </template>
        <template #chemical="{ record }">
          {{ record.chemical.toLocaleString() }}
        </template>
        <template #maintenance="{ record }">
          {{ record.maintenance.toLocaleString() }}
        </template>
        <template #labor="{ record }">
          {{ record.labor.toLocaleString() }}
        </template>
        <template #other="{ record }">
          {{ record.other.toLocaleString() }}
        </template>
        <template #action="{ record }">
          <a-button type="text" size="small" @click.stop="handleViewDetail(record)">
            查看明细
          </a-button>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:visible="detailVisible"
      :title="`${currentCenter?.name} - 费用构成明细`"
      :footer="false"
      width="900px"
    >
      <div class="detail-content">
        <div class="detail-summary">
          <div class="detail-item">
            <div class="detail-label">总费用</div>
            <div class="detail-value">{{ currentCenter?.totalCost.toLocaleString() }} 元</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">占比</div>
            <div class="detail-value">{{ currentCenter?.percentage }}%</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">统计月份</div>
            <div class="detail-value">{{ filterForm.month || '2024-06' }}</div>
          </div>
        </div>

        <div class="detail-chart" ref="detailPieRef" style="height: 280px; margin-top: 16px;"></div>

        <a-table
          :columns="detailColumns"
          :data="detailList"
          :pagination="false"
          style="margin-top: 16px;"
        >
          <template #amount="{ record }">
            <span style="font-weight: 500;">{{ record.amount.toLocaleString() }}</span>
          </template>
          <template #ratio="{ record }">
            {{ record.ratio }}%
          </template>
        </a-table>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { Message } from '@arco-design/web-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const loading = ref(false)
const detailVisible = ref(false)
const currentCenter = ref<any>(null)

const filterForm = reactive({
  month: dayjs().format('YYYY-MM')
})

const summary = reactive({
  totalCost: 486500,
  electricityCost: 185000,
  chemicalCost: 126000,
  unitWaterCost: 0.85,
  totalGrowth: '+3.5%',
  electricityRatio: 38.0,
  chemicalRatio: 25.9
})

const trendChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
const compositionChartRef = ref<HTMLElement>()
const detailPieRef = ref<HTMLElement>()

let trendChart: echarts.ECharts
let pieChart: echarts.ECharts
let compositionChart: echarts.ECharts
let detailPieChart: echarts.ECharts

const costCenterColors = ['#165DFF', '#00B42A', '#FF7D00', '#722ED1', '#F53F3F']

const costCenterColumns = [
  { title: '成本中心', dataIndex: 'name', width: 140 },
  { title: '总费用(元)', dataIndex: 'totalCost', slotName: 'totalCost', width: 140 },
  { title: '占比', slotName: 'percentage', width: 200 },
  { title: '电费(元)', slotName: 'electricity', width: 120 },
  { title: '药剂费(元)', slotName: 'chemical', width: 120 },
  { title: '维修费(元)', slotName: 'maintenance', width: 120 },
  { title: '人工分摊(元)', slotName: 'labor', width: 130 },
  { title: '其他费用(元)', slotName: 'other', width: 120 },
  { title: '操作', slotName: 'action', width: 100 }
]

const detailColumns = [
  { title: '费用项目', dataIndex: 'name', width: 200 },
  { title: '金额(元)', slotName: 'amount', width: 150 },
  { title: '占比', slotName: 'ratio', width: 100 },
  { title: '说明', dataIndex: 'remark', ellipsis: true }
]

const costCenterList = ref([
  {
    id: 1,
    name: '预处理',
    totalCost: 87600,
    percentage: 18.0,
    electricity: 35200,
    chemical: 18500,
    maintenance: 12000,
    labor: 15400,
    other: 6500
  },
  {
    id: 2,
    name: '生化处理',
    totalCost: 198500,
    percentage: 40.8,
    electricity: 98600,
    chemical: 52300,
    maintenance: 18500,
    labor: 22400,
    other: 6700
  },
  {
    id: 3,
    name: '深度处理',
    totalCost: 124800,
    percentage: 25.7,
    electricity: 38500,
    chemical: 45600,
    maintenance: 15800,
    labor: 18600,
    other: 6300
  },
  {
    id: 4,
    name: '污泥处置',
    totalCost: 68200,
    percentage: 14.0,
    electricity: 21500,
    chemical: 18200,
    maintenance: 14600,
    labor: 9800,
    other: 4100
  },
  {
    id: 5,
    name: '其他',
    totalCost: 7400,
    percentage: 1.5,
    electricity: 3200,
    chemical: 1500,
    maintenance: 1600,
    labor: 800,
    other: 300
  }
])

const detailList = ref<any[]>([])

const initCharts = () => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      legend: {
        data: ['预处理', '生化处理', '深度处理', '污泥处置'],
        top: 0
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: ['1月', '2月', '3月', '4月', '5月', '6月']
      },
      yAxis: {
        type: 'value',
        name: '费用(元)'
      },
      series: [
        {
          name: '预处理',
          type: 'line',
          smooth: true,
          stack: 'total',
          areaStyle: { opacity: 0.3 },
          data: [82000, 79500, 84200, 81800, 85600, 87600],
          itemStyle: { color: '#165DFF' }
        },
        {
          name: '生化处理',
          type: 'line',
          smooth: true,
          stack: 'total',
          areaStyle: { opacity: 0.3 },
          data: [186000, 178000, 192000, 185000, 196000, 198500],
          itemStyle: { color: '#00B42A' }
        },
        {
          name: '深度处理',
          type: 'line',
          smooth: true,
          stack: 'total',
          areaStyle: { opacity: 0.3 },
          data: [118000, 115000, 121000, 119000, 123000, 124800],
          itemStyle: { color: '#FF7D00' }
        },
        {
          name: '污泥处置',
          type: 'line',
          smooth: true,
          stack: 'total',
          areaStyle: { opacity: 0.3 },
          data: [64000, 62500, 66800, 65200, 67500, 68200],
          itemStyle: { color: '#722ED1' }
        }
      ]
    })
  }

  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}元 ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center'
      },
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 18,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            { value: 87600, name: '预处理', itemStyle: { color: '#165DFF' } },
            { value: 198500, name: '生化处理', itemStyle: { color: '#00B42A' } },
            { value: 124800, name: '深度处理', itemStyle: { color: '#FF7D00' } },
            { value: 68200, name: '污泥处置', itemStyle: { color: '#722ED1' } },
            { value: 7400, name: '其他', itemStyle: { color: '#86909c' } }
          ]
        }
      ]
    })
  }

  if (compositionChartRef.value) {
    compositionChart = echarts.init(compositionChartRef.value)
    compositionChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      legend: {
        data: ['电费', '药剂费', '维修费', '人工分摊', '其他'],
        top: 0
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: ['预处理', '生化处理', '深度处理', '污泥处置']
      },
      yAxis: {
        type: 'value',
        name: '费用(元)'
      },
      series: [
        {
          name: '电费',
          type: 'bar',
          stack: 'total',
          data: [35200, 98600, 38500, 21500],
          itemStyle: { color: '#165DFF' }
        },
        {
          name: '药剂费',
          type: 'bar',
          stack: 'total',
          data: [18500, 52300, 45600, 18200],
          itemStyle: { color: '#00B42A' }
        },
        {
          name: '维修费',
          type: 'bar',
          stack: 'total',
          data: [12000, 18500, 15800, 14600],
          itemStyle: { color: '#FF7D00' }
        },
        {
          name: '人工分摊',
          type: 'bar',
          stack: 'total',
          data: [15400, 22400, 18600, 9800],
          itemStyle: { color: '#722ED1' }
        },
        {
          name: '其他',
          type: 'bar',
          stack: 'total',
          data: [6500, 6700, 6300, 4100],
          itemStyle: { color: '#86909c' }
        }
      ]
    })
  }
}

const initDetailChart = () => {
  nextTick(() => {
    if (detailPieRef.value && currentCenter.value) {
      detailPieChart = echarts.init(detailPieRef.value)
      detailPieChart.setOption({
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}元 ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center'
        },
        series: [
          {
            type: 'pie',
            radius: ['45%', '70%'],
            center: ['35%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 8,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false
            },
            labelLine: {
              show: false
            },
            data: [
              { value: currentCenter.value.electricity, name: '电费', itemStyle: { color: '#165DFF' } },
              { value: currentCenter.value.chemical, name: '药剂费', itemStyle: { color: '#00B42A' } },
              { value: currentCenter.value.maintenance, name: '维修费', itemStyle: { color: '#FF7D00' } },
              { value: currentCenter.value.labor, name: '人工分摊', itemStyle: { color: '#722ED1' } },
              { value: currentCenter.value.other, name: '其他费用', itemStyle: { color: '#86909c' } }
            ]
          }
        ]
      })
    }
  })
}

const handleRowClick = (record: any) => {
  handleViewDetail(record)
}

const handleViewDetail = (record: any) => {
  currentCenter.value = record
  detailVisible.value = true

  const total = record.totalCost
  detailList.value = [
    { name: '电费', amount: record.electricity, ratio: (record.electricity / total * 100).toFixed(1), remark: '包含水泵、风机、搅拌器等设备用电' },
    { name: '药剂费', amount: record.chemical, ratio: (record.chemical / total * 100).toFixed(1), remark: 'PAC、PAM、碳源等药剂消耗' },
    { name: '维修费', amount: record.maintenance, ratio: (record.maintenance / total * 100).toFixed(1), remark: '设备维保、备件更换等费用' },
    { name: '人工分摊', amount: record.labor, ratio: (record.labor / total * 100).toFixed(1), remark: '按人员配置比例分摊人工成本' },
    { name: '其他费用', amount: record.other, ratio: (record.other / total * 100).toFixed(1), remark: '其他杂项运营费用' }
  ]

  initDetailChart()
}

const fetchData = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    Message.success('查询成功')
  }, 500)
}

const handleResize = () => {
  trendChart?.resize()
  pieChart?.resize()
  compositionChart?.resize()
  detailPieChart?.resize()
}

onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
  compositionChart?.dispose()
  detailPieChart?.dispose()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
}

.page-header p {
  margin: 0;
  font-size: 14px;
  color: #86909c;
}

.filter-card {
  margin-bottom: 16px;
}

.cost-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

@media (max-width: 1400px) {
  .cost-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .cost-summary {
    grid-template-columns: 1fr;
  }
}

.cost-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 16px;
}

.cost-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
}

.cost-info {
  flex: 1;
}

.cost-label {
  font-size: 14px;
  color: #86909c;
  margin-bottom: 4px;
}

.cost-value {
  font-size: 28px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.cost-unit {
  font-size: 14px;
  color: #86909c;
  margin-left: 4px;
  font-weight: normal;
}

.cost-trend {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.cost-trend.up {
  color: #f53f3f;
}

.cost-trend.down {
  color: #00b42a;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}

.detail-content {
  padding: 8px 0;
}

.detail-summary {
  display: flex;
  gap: 32px;
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
}

.detail-item {
  flex: 1;
}

.detail-label {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 6px;
}

.detail-value {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
}

:deep(.arco-table-tr) {
  cursor: pointer;
}

:deep(.arco-table-tr:hover) {
  background-color: #f2f3f5 !important;
}
</style>
