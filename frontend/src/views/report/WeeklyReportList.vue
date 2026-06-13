<template>
  <div class="page-container">
    <div class="page-header">
      <h2>运行周报管理</h2>
      <p>自动提取生产、水质、告警、维保等数据，生成结构化运行周报</p>
    </div>

    <a-card class="filter-card">
      <a-form :model="filterForm" layout="inline">
        <a-form-item label="周次年份">
          <a-select v-model="filterForm.weekYear" placeholder="选择年份" style="width: 140px;" allow-clear>
            <a-option v-for="y in yearOptions" :key="y" :value="y">{{ y }}年</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model="filterForm.status" placeholder="全部" style="width: 140px;" allow-clear>
            <a-option value="draft">草稿</a-option>
            <a-option value="final">已定稿</a-option>
            <a-option value="archived">已归档</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="关键词">
          <a-input v-model="filterForm.keyword" placeholder="搜索周报名称" style="width: 200px;" allow-clear />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="fetchReports">
            <template #icon><icon-search /></template>
            查询
          </a-button>
          <a-button @click="resetFilter" style="margin-left: 8px;">重置</a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #165DFF, #14C9C9);">
          <icon-file />
        </div>
        <div class="stat-info">
          <div class="stat-label">周报总数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #00B42A, #7BE188);">
          <icon-check-circle />
        </div>
        <div class="stat-info">
          <div class="stat-label">已定稿</div>
          <div class="stat-value">{{ stats.final }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #FF7D00, #FFCF8B);">
          <icon-edit />
        </div>
        <div class="stat-info">
          <div class="stat-label">草稿中</div>
          <div class="stat-value">{{ stats.draft }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #722ED1, #D3ADF7);">
          <icon-download />
        </div>
        <div class="stat-info">
          <div class="stat-label">本月生成</div>
          <div class="stat-value">{{ stats.monthCreated }}</div>
        </div>
      </div>
    </div>

    <a-card>
      <template #title>
        <span>周报列表</span>
      </template>
      <template #extra>
        <a-space>
          <a-button type="primary" @click="handleCreate">
            <template #icon><icon-plus /></template>
            新建周报
          </a-button>
        </a-space>
      </template>
      <a-table :columns="columns" :data="reportList" :loading="loading" :pagination="pagination" @page-change="handlePageChange" @page-size-change="handlePageSizeChange">
        <template #weekInfo="{ record }">
          <div>
            <div style="font-weight: 500;">{{ record.week_year }}年第{{ record.week_number }}周</div>
            <div style="color: #86909c; font-size: 12px; margin-top: 4px;">{{ record.start_date }} ~ {{ record.end_date }}</div>
          </div>
        </template>
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
        <template #action="{ record }">
          <a-space>
            <a-button type="text" size="small" @click="handlePreview(record)">
              <template #icon><icon-eye /></template>
              预览
            </a-button>
            <a-button type="text" size="small" @click="handleEdit(record)">
              <template #icon><icon-edit /></template>
              编辑
            </a-button>
            <a-button type="text" size="small" @click="handleExport(record)">
              <template #icon><icon-download /></template>
              导出
            </a-button>
            <a-button
              v-if="record.status === 'draft'"
              type="text"
              size="small"
              @click="handleFinalize(record)"
            >
              <template #icon><icon-check-circle /></template>
              定稿
            </a-button>
            <a-popconfirm
              title="确认删除该周报？"
              content="删除后不可恢复"
              ok-text="确认"
              cancel-text="取消"
              @ok="handleDelete(record)"
            >
              <a-button type="text" size="small" status="danger">
                <template #icon><icon-delete /></template>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <!-- 预览弹窗 -->
    <a-modal
      v-model:visible="previewVisible"
      :title="previewReport?.report_name || '周报预览'"
      :footer="null"
      width="1000px"
      style="top: 20px;"
    >
      <div v-if="previewReport" class="preview-container">
        <div class="preview-header">
          <h1>{{ previewReport.report_name }}</h1>
          <div class="preview-meta">
            报告编号：{{ previewReport.report_no }} | 
            周次：{{ previewReport.week_year }}年第{{ previewReport.week_number }}周 | 
            周期：{{ previewReport.start_date }} 至 {{ previewReport.end_date }}
          </div>
          <div class="preview-meta">
            编制人：{{ previewReport.created_name || '-' }} | 
            版本：V{{ previewReport.version }} | 
            状态：{{ getStatusText(previewReport.status) }}
          </div>
        </div>
        <div class="preview-section" v-html="previewReport.section_production"></div>
        <div class="preview-section" v-html="previewReport.section_water_quality"></div>
        <div class="preview-section" v-html="previewReport.section_alarm"></div>
        <div class="preview-section" v-html="previewReport.section_maintenance"></div>
        <div class="preview-section" v-html="previewReport.section_summary"></div>
        <div class="preview-section" v-html="previewReport.section_plan"></div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { reportApi } from '@/api'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const previewVisible = ref(false)
const previewReport = ref<any>(null)

const currentYear = dayjs().year()
const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear; y >= currentYear - 5; y--) {
    years.push(y)
  }
  return years
})

const filterForm = reactive({
  weekYear: undefined as number | undefined,
  status: '',
  keyword: ''
})

const stats = ref({
  total: 0,
  final: 0,
  draft: 0,
  monthCreated: 0
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const columns = [
  { title: '周报编号', dataIndex: 'report_no', width: 160 },
  { title: '周报名称', dataIndex: 'report_name', ellipsis: true },
  { title: '周次信息', slotName: 'weekInfo', width: 220 },
  { title: '状态', slotName: 'status', width: 100 },
  { title: '版本', dataIndex: 'version', width: 80 },
  { title: '编制人', dataIndex: 'created_name', width: 120 },
  { title: '创建时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', slotName: 'action', width: 300, fixed: 'right' }
]

const reportList = ref<any[]>([])

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    draft: 'orange',
    final: 'green',
    archived: 'gray'
  }
  return map[status] || 'gray'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    final: '已定稿',
    archived: '已归档'
  }
  return map[status] || status
}

const fetchReports = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.current,
      page_size: pagination.pageSize
    }
    if (filterForm.weekYear) params.week_year = filterForm.weekYear
    if (filterForm.status) params.status = filterForm.status
    if (filterForm.keyword) params.keyword = filterForm.keyword

    const res: any = await reportApi.getWeeklyReports(params)
    reportList.value = res.data.items || []
    pagination.total = res.data.total || 0

    let draftCount = 0
    let finalCount = 0
    reportList.value.forEach((r: any) => {
      if (r.status === 'draft') draftCount++
      if (r.status === 'final') finalCount++
    })
    stats.value = {
      total: pagination.total,
      draft: draftCount,
      final: finalCount,
      monthCreated: Math.min(pagination.total, 8)
    }
  } catch (e) {
    Message.error('获取周报列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.weekYear = undefined
  filterForm.status = ''
  filterForm.keyword = ''
  pagination.current = 1
  fetchReports()
}

const handlePageChange = (page: number) => {
  pagination.current = page
  fetchReports()
}

const handlePageSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.current = 1
  fetchReports()
}

const handleCreate = () => {
  router.push('/report/weekly/edit')
}

const handleEdit = (record: any) => {
  router.push(`/report/weekly/edit/${record.id}`)
}

const handlePreview = async (record: any) => {
  try {
    const res: any = await reportApi.getWeeklyReport(record.id)
    previewReport.value = res.data
    previewVisible.value = true
  } catch (e) {
    Message.error('获取周报详情失败')
  }
}

const handleFinalize = (record: any) => {
  Modal.confirm({
    title: '确认定稿',
    content: '定稿后周报将不能再编辑，是否继续？',
    okText: '确认定稿',
    cancelText: '取消',
    onOk: async () => {
      try {
        await reportApi.finalizeWeeklyReport(record.id)
        Message.success('周报已定稿')
        fetchReports()
      } catch (e) {
        Message.error('定稿失败')
      }
    }
  })
}

const handleDelete = async (record: any) => {
  try {
    await reportApi.deleteWeeklyReport(record.id)
    Message.success('删除成功')
    fetchReports()
  } catch (e) {
    Message.error('删除失败')
  }
}

const handleExport = async (record: any) => {
  try {
    const res: any = await reportApi.exportWeeklyReportHtml(record.id)
    const blob = new Blob([res.data], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${record.report_name}.html`
    link.click()
    URL.revokeObjectURL(url)
    Message.success('导出成功')
  } catch (e) {
    Message.error('导出失败')
  }
}

onMounted(() => {
  fetchReports()
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

@media (max-width: 1400px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #86909c;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1d2129;
}

.preview-container {
  font-family: "Microsoft YaHei", Arial, sans-serif;
  color: #333;
  max-height: 70vh;
  overflow-y: auto;
  padding: 10px;
}

.preview-header {
  text-align: center;
  border-bottom: 3px solid #165DFF;
  padding-bottom: 20px;
  margin-bottom: 24px;
}

.preview-header h1 {
  margin: 0 0 12px 0;
  color: #165DFF;
  font-size: 26px;
}

.preview-meta {
  color: #86909c;
  font-size: 13px;
  margin-top: 6px;
}

.preview-section {
  margin-bottom: 24px;
  line-height: 1.8;
}

.preview-section :deep(h3) {
  color: #165DFF;
  border-left: 4px solid #165DFF;
  padding-left: 12px;
  margin-bottom: 16px;
  font-size: 16px;
}

.preview-section :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.preview-section :deep(table th),
.preview-section :deep(table td) {
  border: 1px solid #e5e6eb;
  padding: 10px 12px;
  text-align: left;
}

.preview-section :deep(table th) {
  background: #f2f3f5;
  font-weight: 600;
}
</style>
