<template>
  <div class="page-container">
    <div class="page-header">
      <h2>视频巡检点位</h2>
      <p>厂区视频监控摄像头点位管理与巡检记录台账</p>
    </div>

    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic :value="statistics.total_points" title="点位总数" :value-style="{ color: '#165DFF' }">
            <template #prefix><icon-apartment /></template>
          </a-statistic>
          <div class="stat-sub">在线: {{ statistics.online_points }} / 离线: {{ statistics.offline_points }}</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic :value="statistics.today_inspections" title="今日巡检次数" :value-style="{ color: '#00B42A' }">
            <template #prefix><icon-schedule /></template>
          </a-statistic>
          <div class="stat-sub">在线率: {{ onlineRate }}%</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic :value="statistics.pending_abnormal" title="待处理异常" :value-style="{ color: '#F53F3F' }">
            <template #prefix><icon-exclamation-circle /></template>
          </a-statistic>
          <div class="stat-sub">累计异常: {{ statistics.total_abnormal }}</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="severity-stats">
            <div class="severity-item critical">
              <span class="severity-dot"></span>
              <span class="severity-label">严重</span>
              <span class="severity-value">{{ statistics.severity_counts?.critical || 0 }}</span>
            </div>
            <div class="severity-item severe">
              <span class="severity-dot"></span>
              <span class="severity-label">高危</span>
              <span class="severity-value">{{ statistics.severity_counts?.severe || 0 }}</span>
            </div>
            <div class="severity-item moderate">
              <span class="severity-dot"></span>
              <span class="severity-label">中危</span>
              <span class="severity-value">{{ statistics.severity_counts?.moderate || 0 }}</span>
            </div>
            <div class="severity-item mild">
              <span class="severity-dot"></span>
              <span class="severity-label">轻微</span>
              <span class="severity-value">{{ statistics.severity_counts?.mild || 0 }}</span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-card class="content-card">
      <div class="table-operations">
        <div class="operations-left">
          <a-input-search
            v-model="searchKeyword"
            placeholder="搜索点位名称/位置/编号"
            style="width: 260px;"
            @search="fetchCameraPoints"
          />
          <a-select v-model="filterOnlineStatus" placeholder="在线状态" style="width: 140px; margin-left: 12px;" @change="fetchCameraPoints" allow-clear>
            <a-option value="online">在线</a-option>
            <a-option value="offline">离线</a-option>
            <a-option value="maintenance">维护中</a-option>
          </a-select>
        </div>
        <div class="operations-right">
          <a-space>
            <a-button @click="goToAbnormalPage">
              <template #icon><icon-exclamation /></template>
              异常汇总
            </a-button>
            <a-button type="primary" @click="openPointModal()">
              <template #icon><icon-plus /></template>
              新增点位
            </a-button>
          </a-space>
        </div>
      </div>

      <a-table
        :columns="pointColumns"
        :data="cameraPoints"
        :loading="loadingPoints"
        :pagination="pointPagination"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
      >
        <template #online_status="{ record }">
          <a-tag :color="getOnlineStatusColor(record.online_status)">
            {{ getOnlineStatusText(record.online_status) }}
          </a-tag>
        </template>
        <template #last_inspection="{ record }">
          <div v-if="record.last_inspection_time" class="last-inspection">
            <div class="inspection-time">{{ formatTime(record.last_inspection_time) }}</div>
            <div class="inspection-info">
              <span>{{ record.last_inspector || '-' }}</span>
              <a-tag
                v-if="record.last_inspection_result"
                :color="record.last_inspection_result === 'normal' ? 'green' : 'red'"
                style="margin-left: 8px;"
              >
                {{ record.last_inspection_result === 'normal' ? '正常' : '异常' }}
              </a-tag>
            </div>
          </div>
          <span v-else style="color: #c9cdd4;">暂无巡检记录</span>
        </template>
        <template #operations="{ record }">
          <a-space>
            <a-button type="text" size="small" status="primary" @click="openInspectModal(record)">
              <template #icon><icon-camera /></template>
              巡检
            </a-button>
            <a-button type="text" size="small" @click="viewInspectionHistory(record)">
              <template #icon><icon-history /></template>
              历史
            </a-button>
            <a-button type="text" size="small" @click="openPointModal(record)">
              <template #icon><icon-edit /></template>
              编辑
            </a-button>
            <a-popconfirm content="确定删除该点位？" @ok="deletePoint(record)">
              <a-button type="text" size="small" status="danger">
                <template #icon><icon-delete /></template>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:visible="showPointModal"
      :title="editingPoint ? '编辑点位' : '新增点位'"
      @ok="handlePointSubmit"
      ok-text="确定"
      cancel-text="取消"
      width="560px"
    >
      <a-form :model="pointForm" layout="vertical" ref="pointFormRef">
        <a-form-item label="点位名称" required>
          <a-input v-model="pointForm.point_name" placeholder="请输入点位名称" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="安装位置">
              <a-input v-model="pointForm.install_location" placeholder="如:厂区北区-粗格栅间" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="覆盖区域">
              <a-input v-model="pointForm.coverage_area" placeholder="请输入覆盖区域" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="设备型号">
              <a-input v-model="pointForm.device_model" placeholder="请输入设备型号" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="IP地址">
              <a-input v-model="pointForm.ip_address" placeholder="如:192.168.1.101" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="在线状态">
              <a-select v-model="pointForm.online_status">
                <a-option value="online">在线</a-option>
                <a-option value="offline">离线</a-option>
                <a-option value="maintenance">维护中</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="责任人">
              <a-input v-model="pointForm.responsible_person" placeholder="请输入责任人" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="备注">
          <a-textarea v-model="pointForm.remark" :auto-size="{ minRows: 2, maxRows: 4 }" placeholder="请输入备注信息" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:visible="showInspectModal"
      :title="`视频巡检 - ${inspectingPoint?.point_name || ''}`"
      @ok="handleInspectSubmit"
      ok-text="提交巡检"
      cancel-text="取消"
      width="560px"
    >
      <div v-if="inspectingPoint" class="inspect-point-info">
        <a-descriptions :column="2" size="small" bordered>
          <a-descriptions-item label="点位编号">{{ inspectingPoint.point_no }}</a-descriptions-item>
          <a-descriptions-item label="安装位置">{{ inspectingPoint.install_location || '-' }}</a-descriptions-item>
          <a-descriptions-item label="覆盖区域">{{ inspectingPoint.coverage_area || '-' }}</a-descriptions-item>
          <a-descriptions-item label="设备型号">{{ inspectingPoint.device_model || '-' }}</a-descriptions-item>
        </a-descriptions>
      </div>
      <a-form :model="inspectForm" layout="vertical" style="margin-top: 16px;">
        <a-form-item label="巡检时间" required>
          <a-date-picker
            v-model="inspectForm.inspection_time"
            type="datetime"
            style="width: 100%;"
            format="YYYY-MM-DD HH:mm:ss"
            :show-time="{ defaultValue: dayjs() }"
            placeholder="选择巡检时间"
          />
        </a-form-item>
        <a-form-item label="巡检结论" required>
          <a-radio-group v-model="inspectForm.result" type="button">
            <a-radio value="normal">
              <span style="color: #00B42A;"><icon-check-circle /></span> 正常
            </a-radio>
            <a-radio value="abnormal">
              <span style="color: #F53F3F;"><icon-close-circle /></span> 异常
            </a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item v-if="inspectForm.result === 'abnormal'" label="严重程度" required>
          <a-radio-group v-model="inspectForm.severity">
            <a-radio value="mild">
              <a-tag color="lime">轻微</a-tag>
            </a-radio>
            <a-radio value="moderate">
              <a-tag color="yellow">中危</a-tag>
            </a-radio>
            <a-radio value="severe">
              <a-tag color="orange">高危</a-tag>
            </a-radio>
            <a-radio value="critical">
              <a-tag color="red">严重</a-tag>
            </a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item v-if="inspectForm.result === 'abnormal'" label="异常描述" required>
          <a-textarea
            v-model="inspectForm.abnormal_description"
            :auto-size="{ minRows: 3, maxRows: 5 }"
            placeholder="请详细描述发现的异常情况"
          />
        </a-form-item>
        <a-form-item label="巡检备注">
          <a-textarea
            v-model="inspectForm.remark"
            :auto-size="{ minRows: 2, maxRows: 4 }"
            placeholder="请输入巡检备注信息"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-drawer
      v-model:visible="showHistoryDrawer"
      :title="`巡检历史 - ${historyPoint?.point_name || ''}`"
      :width="720"
      ok-text="关闭"
      @ok="showHistoryDrawer = false"
    >
      <a-table
        :columns="historyColumns"
        :data="historyRecords"
        :loading="loadingHistory"
        :pagination="false"
        size="small"
      >
        <template #result="{ record }">
          <a-tag :color="record.result === 'normal' ? 'green' : 'red'">
            {{ record.result === 'normal' ? '正常' : '异常' }}
          </a-tag>
        </template>
        <template #severity="{ record }">
          <a-tag v-if="record.severity" :color="getSeverityColor(record.severity)">
            {{ getSeverityText(record.severity) }}
          </a-tag>
          <span v-else>-</span>
        </template>
        <template #handle_status="{ record }">
          <a-tag :color="getHandleStatusColor(record.handle_status)">
            {{ getHandleStatusText(record.handle_status) }}
          </a-tag>
        </template>
      </a-table>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import dayjs from 'dayjs'
import { videoInspectionApi } from '@/api'

const router = useRouter()

const loadingPoints = ref(false)
const loadingHistory = ref(false)
const searchKeyword = ref('')
const filterOnlineStatus = ref<string | undefined>(undefined)
const cameraPoints = ref<any[]>([])
const pointPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})
const statistics = reactive({
  total_points: 0,
  online_points: 0,
  offline_points: 0,
  today_inspections: 0,
  pending_abnormal: 0,
  total_abnormal: 0,
  severity_counts: { critical: 0, severe: 0, moderate: 0, mild: 0 }
})

const onlineRate = computed(() => {
  if (!statistics.total_points) return 0
  return ((statistics.online_points / statistics.total_points) * 100).toFixed(1)
})

const pointColumns = [
  { title: '点位编号', dataIndex: 'point_no', width: 140 },
  { title: '点位名称', dataIndex: 'point_name', width: 160 },
  { title: '安装位置', dataIndex: 'install_location', width: 160 },
  { title: '覆盖区域', dataIndex: 'coverage_area', width: 160 },
  { title: '设备型号', dataIndex: 'device_model', width: 200 },
  { title: '在线状态', slotName: 'online_status', width: 100 },
  { title: '最近巡检', slotName: 'last_inspection', width: 200 },
  { title: '操作', slotName: 'operations', width: 220, fixed: 'right' as const }
]

const historyColumns = [
  { title: '记录编号', dataIndex: 'record_no', width: 140 },
  { title: '巡检时间', dataIndex: 'inspection_time', width: 160 },
  { title: '巡检人', dataIndex: 'inspector_name', width: 100 },
  { title: '巡检结果', slotName: 'result', width: 80 },
  { title: '严重程度', slotName: 'severity', width: 90 },
  { title: '处理状态', slotName: 'handle_status', width: 100 },
  { title: '异常描述', dataIndex: 'abnormal_description' },
  { title: '备注', dataIndex: 'remark' }
]

const showPointModal = ref(false)
const editingPoint = ref<any>(null)
const pointFormRef = ref()
const pointForm = reactive({
  point_name: '',
  install_location: '',
  coverage_area: '',
  device_model: '',
  online_status: 'online',
  ip_address: '',
  responsible_person: '',
  remark: ''
})

const showInspectModal = ref(false)
const inspectingPoint = ref<any>(null)
const inspectForm = reactive({
  inspection_time: dayjs() as any,
  result: 'normal',
  severity: '',
  remark: '',
  abnormal_description: ''
})

const showHistoryDrawer = ref(false)
const historyPoint = ref<any>(null)
const historyRecords = ref<any[]>([])

const formatTime = (time: string) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const getOnlineStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    online: 'green',
    offline: 'red',
    maintenance: 'orangered'
  }
  return colorMap[status] || 'gray'
}

const getOnlineStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    online: '在线',
    offline: '离线',
    maintenance: '维护中'
  }
  return textMap[status] || status
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

const fetchStatistics = async () => {
  try {
    const res: any = await videoInspectionApi.getStatistics()
    Object.assign(statistics, res)
  } catch (e) {
    console.error('获取统计数据失败', e)
  }
}

const fetchCameraPoints = async () => {
  loadingPoints.value = true
  try {
    const params: any = {
      page: pointPagination.current,
      page_size: pointPagination.pageSize
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterOnlineStatus.value) params.online_status = filterOnlineStatus.value

    const res: any = await videoInspectionApi.getCameraPoints(params)
    cameraPoints.value = res.items
    pointPagination.total = res.total
  } catch (e) {
    Message.error('获取点位列表失败')
  } finally {
    loadingPoints.value = false
  }
}

const handlePageChange = (page: number) => {
  pointPagination.current = page
  fetchCameraPoints()
}

const handlePageSizeChange = (pageSize: number) => {
  pointPagination.pageSize = pageSize
  pointPagination.current = 1
  fetchCameraPoints()
}

const openPointModal = (record?: any) => {
  editingPoint.value = record || null
  if (record) {
    Object.assign(pointForm, {
      point_name: record.point_name || '',
      install_location: record.install_location || '',
      coverage_area: record.coverage_area || '',
      device_model: record.device_model || '',
      online_status: record.online_status || 'online',
      ip_address: record.ip_address || '',
      responsible_person: record.responsible_person || '',
      remark: record.remark || ''
    })
  } else {
    Object.assign(pointForm, {
      point_name: '',
      install_location: '',
      coverage_area: '',
      device_model: '',
      online_status: 'online',
      ip_address: '',
      responsible_person: '',
      remark: ''
    })
  }
  showPointModal.value = true
}

const handlePointSubmit = async () => {
  if (!pointForm.point_name.trim()) {
    Message.warning('请输入点位名称')
    return
  }
  try {
    if (editingPoint.value) {
      await videoInspectionApi.updateCameraPoint(editingPoint.value.id, pointForm)
      Message.success('编辑成功')
    } else {
      await videoInspectionApi.createCameraPoint(pointForm)
      Message.success('新增成功')
    }
    showPointModal.value = false
    fetchCameraPoints()
    fetchStatistics()
  } catch (e) {
    Message.error(editingPoint.value ? '编辑失败' : '新增失败')
  }
}

const deletePoint = async (record: any) => {
  try {
    await videoInspectionApi.deleteCameraPoint(record.id)
    Message.success('删除成功')
    fetchCameraPoints()
    fetchStatistics()
  } catch (e) {
    Message.error('删除失败')
  }
}

const openInspectModal = (record: any) => {
  inspectingPoint.value = record
  Object.assign(inspectForm, {
    inspection_time: dayjs(),
    result: 'normal',
    severity: '',
    remark: '',
    abnormal_description: ''
  })
  showInspectModal.value = true
}

const handleInspectSubmit = async () => {
  if (!inspectForm.inspection_time) {
    Message.warning('请选择巡检时间')
    return
  }
  if (inspectForm.result === 'abnormal') {
    if (!inspectForm.severity) {
      Message.warning('请选择异常严重程度')
      return
    }
    if (!inspectForm.abnormal_description?.trim()) {
      Message.warning('请描述异常情况')
      return
    }
  }
  try {
    const payload = {
      camera_point_id: inspectingPoint.value.id,
      inspection_time: inspectForm.inspection_time.format ? inspectForm.inspection_time.format('YYYY-MM-DD HH:mm:ss') : inspectForm.inspection_time,
      result: inspectForm.result,
      severity: inspectForm.result === 'abnormal' ? inspectForm.severity : undefined,
      remark: inspectForm.remark || undefined,
      abnormal_description: inspectForm.result === 'abnormal' ? inspectForm.abnormal_description : undefined
    }
    await videoInspectionApi.createInspectionRecord(payload)
    Message.success('巡检记录提交成功')
    showInspectModal.value = false
    fetchCameraPoints()
    fetchStatistics()
  } catch (e) {
    Message.error('提交巡检记录失败')
  }
}

const viewInspectionHistory = async (record: any) => {
  historyPoint.value = record
  showHistoryDrawer.value = true
  loadingHistory.value = true
  try {
    const res: any = await videoInspectionApi.getInspectionRecords({
      camera_point_id: record.id,
      page: 1,
      page_size: 50
    })
    historyRecords.value = res.items
  } catch (e) {
    Message.error('获取巡检历史失败')
  } finally {
    loadingHistory.value = false
  }
}

const goToAbnormalPage = () => {
  router.push('/safety/video-abnormal')
}

onMounted(() => {
  fetchStatistics()
  fetchCameraPoints()
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
}

.stat-sub {
  margin-top: 8px;
  font-size: 12px;
  color: #86909c;
}

.severity-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.severity-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.severity-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.severity-item.critical .severity-dot { background: #F53F3F; }
.severity-item.severe .severity-dot { background: #FF7D00; }
.severity-item.moderate .severity-dot { background: #FFAA00; }
.severity-item.mild .severity-dot { background: #9BBB35; }

.severity-label {
  color: #4e5969;
  width: 36px;
}

.severity-value {
  font-weight: 600;
  color: #1d2129;
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

.last-inspection {
  line-height: 1.4;
}

.inspection-time {
  font-size: 13px;
  color: #1d2129;
}

.inspection-info {
  font-size: 12px;
  color: #86909c;
  display: flex;
  align-items: center;
}

.inspect-point-info {
  padding: 4px 0;
}
</style>
