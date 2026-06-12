<template>
  <div class="page-container">
    <div class="page-header">
      <h2>视频巡检异常汇总</h2>
      <p>按严重程度排列巡检发现的异常问题，统一跟踪处理进度</p>
    </div>

    <a-row :gutter="16" class="stats-row">
      <a-col :span="4">
        <a-card class="stat-card stat-all" @click="filterBySeverity('')">
          <div class="stat-number">{{ statistics.total_abnormal || 0 }}</div>
          <div class="stat-label">全部异常</div>
        </a-card>
      </a-col>
      <a-col :span="5">
        <a-card class="stat-card stat-critical" @click="filterBySeverity('critical')">
          <div class="stat-badge">严重</div>
          <div class="stat-number">{{ statistics.severity_counts?.critical || 0 }}</div>
          <div class="stat-label">需立即处理</div>
        </a-card>
      </a-col>
      <a-col :span="5">
        <a-card class="stat-card stat-severe" @click="filterBySeverity('severe')">
          <div class="stat-badge">高危</div>
          <div class="stat-number">{{ statistics.severity_counts?.severe || 0 }}</div>
          <div class="stat-label">优先处理</div>
        </a-card>
      </a-col>
      <a-col :span="5">
        <a-card class="stat-card stat-moderate" @click="filterBySeverity('moderate')">
          <div class="stat-badge">中危</div>
          <div class="stat-number">{{ statistics.severity_counts?.moderate || 0 }}</div>
          <div class="stat-label">尽快处理</div>
        </a-card>
      </a-col>
      <a-col :span="5">
        <a-card class="stat-card stat-mild" @click="filterBySeverity('mild')">
          <div class="stat-badge">轻微</div>
          <div class="stat-number">{{ statistics.severity_counts?.mild || 0 }}</div>
          <div class="stat-label">计划处理</div>
        </a-card>
      </a-col>
    </a-row>

    <a-card class="content-card">
      <div class="table-operations">
        <div class="operations-left">
          <a-input-search
            v-model="searchKeyword"
            placeholder="搜索点位名称/异常描述"
            style="width: 260px;"
            @search="fetchAbnormalList"
          />
          <a-select v-model="filterHandleStatus" placeholder="处理状态" style="width: 140px; margin-left: 12px;" @change="fetchAbnormalList" allow-clear>
            <a-option value="pending">待处理</a-option>
            <a-option value="handling">处理中</a-option>
            <a-option value="resolved">已解决</a-option>
            <a-option value="closed">已关闭</a-option>
          </a-select>
        </div>
        <div class="operations-right">
          <a-space>
            <a-button @click="resetFilters">
              <template #icon><icon-refresh /></template>
              重置筛选
            </a-button>
            <a-button @click="goToPointsPage">
              <template #icon><icon-apartment /></template>
              返回点位列表
            </a-button>
          </a-space>
        </div>
      </div>

      <a-table
        :columns="abnormalColumns"
        :data="abnormalList"
        :loading="loading"
        :pagination="pagination"
        :row-class-name="getRowClassName"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
      >
        <template #severity="{ record }">
          <div class="severity-cell">
            <div class="severity-bar" :class="`severity-${record.severity}`"></div>
            <a-tag :color="getSeverityColor(record.severity)">
              {{ getSeverityText(record.severity) }}
            </a-tag>
          </div>
        </template>
        <template #handle_status="{ record }">
          <a-space>
            <a-tag :color="getHandleStatusColor(record.handle_status)">
              {{ getHandleStatusText(record.handle_status) }}
            </a-tag>
            <a-dropdown trigger="click" @select="(val) => updateHandleStatus(record, val)">
              <a-button type="text" size="mini">
                <template #icon><icon-down /></template>
              </a-button>
              <template #content>
                <a-doption value="pending">待处理</a-doption>
                <a-doption value="handling">处理中</a-doption>
                <a-doption value="resolved">已解决</a-doption>
                <a-doption value="closed">已关闭</a-doption>
              </template>
            </a-dropdown>
          </a-space>
        </template>
        <template #abnormal_description="{ record }">
          <div class="desc-cell">
            <div class="desc-title">{{ record.abnormal_description || '-' }}</div>
            <div v-if="record.remark" class="desc-remark">备注: {{ record.remark }}</div>
          </div>
        </template>
        <template #info="{ record }">
          <div class="info-cell">
            <div class="info-item">
              <span class="info-label">点位:</span>
              <span class="info-value">{{ record.camera_point_name || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">巡检人:</span>
              <span class="info-value">{{ record.inspector_name || '-' }}</span>
            </div>
          </div>
        </template>
        <template #time="{ record }">
          <div class="time-cell">
            <div class="time-main">{{ formatTime(record.inspection_time) }}</div>
            <div class="time-no">{{ record.record_no }}</div>
          </div>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import dayjs from 'dayjs'
import { videoInspectionApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const searchKeyword = ref('')
const filterHandleStatus = ref<string | undefined>(undefined)
const filterSeverity = ref<string | undefined>(undefined)
const abnormalList = ref<any[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})
const statistics = reactive({
  total_abnormal: 0,
  severity_counts: { critical: 0, severe: 0, moderate: 0, mild: 0 }
})

const abnormalColumns = [
  {
    title: '严重程度',
    slotName: 'severity',
    width: 120,
    sorter: (a: any, b: any) => getSeverityOrder(a.severity) - getSeverityOrder(b.severity)
  },
  { title: '时间/编号', slotName: 'time', width: 180 },
  { title: '点位/巡检人', slotName: 'info', width: 180 },
  { title: '异常描述', slotName: 'abnormal_description' },
  { title: '处理状态', slotName: 'handle_status', width: 160 }
]

const formatTime = (time: string) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const getSeverityOrder = (severity: string) => {
  const orderMap: Record<string, number> = {
    critical: 0,
    severe: 1,
    moderate: 2,
    mild: 3
  }
  return orderMap[severity] ?? 99
}

const getSeverityColor = (severity: string) => {
  const colorMap: Record<string, string> = {
    mild: 'lime',
    moderate: 'yellow',
    severe: 'orange',
    critical: 'red'
  }
  return colorMap[severity] || 'gray'
}

const getSeverityText = (severity: string) => {
  const textMap: Record<string, string> = {
    mild: '轻微',
    moderate: '中危',
    severe: '高危',
    critical: '严重'
  }
  return textMap[severity] || severity
}

const getHandleStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'red',
    handling: 'orangered',
    resolved: 'green',
    closed: 'gray'
  }
  return colorMap[status] || 'gray'
}

const getHandleStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '待处理',
    handling: '处理中',
    resolved: '已解决',
    closed: '已关闭'
  }
  return textMap[status] || status
}

const getRowClassName = (record: any) => {
  return `row-severity-${record.severity}`
}

const fetchStatistics = async () => {
  try {
    const res: any = await videoInspectionApi.getStatistics()
    Object.assign(statistics, {
      total_abnormal: res.total_abnormal,
      severity_counts: res.severity_counts
    })
  } catch (e) {
    console.error('获取统计数据失败', e)
  }
}

const fetchAbnormalList = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.current,
      page_size: pagination.pageSize
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterSeverity.value) params.severity = filterSeverity.value
    if (filterHandleStatus.value) params.handle_status = filterHandleStatus.value

    const res: any = await videoInspectionApi.getAbnormalList(params)
    abnormalList.value = res.items
    pagination.total = res.total
  } catch (e) {
    Message.error('获取异常列表失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.current = page
  fetchAbnormalList()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.current = 1
  fetchAbnormalList()
}

const filterBySeverity = (severity: string) => {
  filterSeverity.value = severity || undefined
  pagination.current = 1
  fetchAbnormalList()
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterSeverity.value = undefined
  filterHandleStatus.value = undefined
  pagination.current = 1
  fetchAbnormalList()
}

const updateHandleStatus = async (record: any, status: string) => {
  try {
    await videoInspectionApi.updateHandleStatus(record.id, { handle_status: status })
    Message.success(`状态已更新为「${getHandleStatusText(status)}」`)
    fetchAbnormalList()
    fetchStatistics()
  } catch (e) {
    Message.error('状态更新失败')
  }
}

const goToPointsPage = () => {
  router.push('/safety/video-inspection')
}

onMounted(() => {
  fetchStatistics()
  fetchAbnormalList()
})
</script>

<style scoped>
.page-container {
  padding: 0;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
}

.page-header p {
  margin: 0;
  color: #86909c;
  font-size: 13px;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.stat-all::before { background: #165DFF; }
.stat-critical::before { background: #F53F3F; }
.stat-severe::before { background: #FF7D00; }
.stat-moderate::before { background: #FFAA00; }
.stat-mild::before { background: #9BBB35; }

.stat-number {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  color: #1d2129;
}

.stat-all .stat-number { color: #165DFF; }
.stat-critical .stat-number { color: #F53F3F; }
.stat-severe .stat-number { color: #FF7D00; }
.stat-moderate .stat-number { color: #FFAA00; }
.stat-mild .stat-number { color: #9BBB35; }

.stat-label {
  font-size: 13px;
  color: #86909c;
  margin-top: 6px;
}

.stat-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}

.stat-critical .stat-badge {
  background: #FEECEC;
  color: #F53F3F;
}

.stat-severe .stat-badge {
  background: #FFF3E8;
  color: #FF7D00;
}

.stat-moderate .stat-badge {
  background: #FFF8E1;
  color: #FFAA00;
}

.stat-mild .stat-badge {
  background: #F3F8E8;
  color: #9BBB35;
}

.content-card {
  border-radius: 8px;
}

.table-operations {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.operations-left,
.operations-right {
  display: flex;
  align-items: center;
}

.severity-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.severity-bar {
  width: 4px;
  height: 32px;
  border-radius: 2px;
  flex-shrink: 0;
}

.severity-critical { background: #F53F3F; }
.severity-severe { background: #FF7D00; }
.severity-moderate { background: #FFAA00; }
.severity-mild { background: #9BBB35; }

.desc-cell {
  line-height: 1.5;
}

.desc-title {
  color: #1d2129;
  font-size: 13px;
  word-break: break-all;
}

.desc-remark {
  margin-top: 4px;
  color: #86909c;
  font-size: 12px;
}

.info-cell {
  line-height: 1.6;
}

.info-item {
  display: flex;
  font-size: 12px;
}

.info-label {
  color: #86909c;
  width: 48px;
  flex-shrink: 0;
}

.info-value {
  color: #4e5969;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.time-cell {
  line-height: 1.5;
}

.time-main {
  font-size: 13px;
  color: #1d2129;
  font-weight: 500;
}

.time-no {
  font-size: 11px;
  color: #c9cdd4;
  margin-top: 2px;
}

:deep(.arco-table-tr.row-severity-critical td) {
  background-color: rgba(245, 63, 63, 0.04);
}

:deep(.arco-table-tr.row-severity-severe td) {
  background-color: rgba(255, 125, 0, 0.03);
}

:deep(.arco-table-tr.row-severity-moderate td) {
  background-color: rgba(255, 170, 0, 0.02);
}
</style>
