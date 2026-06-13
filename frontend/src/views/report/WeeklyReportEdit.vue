<template>
  <div class="page-container">
    <div class="page-header">
      <a-space align="center">
        <a-button @click="goBack" style="margin-right: 8px;">
          <template #icon><icon-left /></template>
          返回
        </a-button>
        <div>
          <h2 style="margin: 0;">{{ isEdit ? '编辑周报' : '新建周报' }}</h2>
          <p style="margin: 4px 0 0 0; color: #86909c; font-size: 13px;">
            自动提取生产、水质、告警、维保业务数据，支持富文本在线编辑
          </p>
        </div>
      </a-space>
    </div>

    <a-card class="basic-info-card">
      <template #title>
        <template #icon><icon-info-circle /></template>
        基本信息
      </template>
      <a-form :model="formData" layout="inline">
        <a-form-item label="周次年份" required>
          <a-select v-model="formData.weekYear" placeholder="选择年份" style="width: 140px;" :disabled="isEdit">
            <a-option v-for="y in yearOptions" :key="y" :value="y">{{ y }}年</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="周次" required>
          <a-select v-model="formData.weekNumber" placeholder="选择周次" style="width: 140px;" :disabled="isEdit">
            <a-option v-for="w in 53" :key="w" :value="w">第{{ w }}周</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="日期范围">
          <a-input
            :value="formData.startDate && formData.endDate ? `${formData.startDate} ~ ${formData.endDate}` : ''"
            readonly
            style="width: 280px;"
            placeholder="选择周次后自动计算"
          />
        </a-form-item>
        <a-form-item label="周报名称" required>
          <a-input v-model="formData.reportName" placeholder="请输入周报名称" style="width: 300px;" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" :disabled="!canSummarize" @click="handleSummarize" :loading="summarizing">
            <template #icon><icon-sync /></template>
            自动提取数据
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card v-if="summaryData" class="data-card">
      <template #title>
        <template #icon><icon-bar-chart /></template>
        本周业务数据概览
      </template>
      <div class="data-overview">
        <div class="data-item">
          <div class="data-label">本周处理水量</div>
          <div class="data-value">{{ productionData.total_intake?.toLocaleString() }} <span class="data-unit">m³</span></div>
          <div class="data-sub">日均 {{ productionData.daily_avg_intake?.toLocaleString() }} m³</div>
        </div>
        <div class="data-item">
          <div class="data-label">水质达标率</div>
          <div class="data-value highlight-green">{{ waterQualityData.qualified_rate }}%</div>
          <div class="data-sub">{{ waterQualityData.qualified_count }}/{{ waterQualityData.total_detection }} 样品达标</div>
        </div>
        <div class="data-item">
          <div class="data-label">异常告警</div>
          <div class="data-value">{{ alarmData.total }} 起</div>
          <div class="data-sub">已处理 {{ alarmData.resolved }} 起，处理率 {{ alarmData.resolution_rate }}%</div>
        </div>
        <div class="data-item">
          <div class="data-label">设备维保完成</div>
          <div class="data-value">{{ maintenanceData.completed }}/{{ maintenanceData.planned }}</div>
          <div class="data-sub">完成率 {{ maintenanceData.completion_rate }}%</div>
        </div>
      </div>
    </a-card>

    <a-tabs v-model:activeTab="activeTab" class="editor-tabs">
      <a-tab-pane key="production" title="生产运行情况">
        <div class="editor-wrapper">
          <RichTextEditor v-model="formData.sectionProduction" />
        </div>
      </a-tab-pane>
      <a-tab-pane key="waterQuality" title="水质达标情况">
        <div class="editor-wrapper">
          <RichTextEditor v-model="formData.sectionWaterQuality" />
        </div>
      </a-tab-pane>
      <a-tab-pane key="alarm" title="异常告警情况">
        <div class="editor-wrapper">
          <RichTextEditor v-model="formData.sectionAlarm" />
        </div>
      </a-tab-pane>
      <a-tab-pane key="maintenance" title="设备维保情况">
        <div class="editor-wrapper">
          <RichTextEditor v-model="formData.sectionMaintenance" />
        </div>
      </a-tab-pane>
      <a-tab-pane key="summary" title="本周工作总结">
        <div class="editor-wrapper">
          <RichTextEditor v-model="formData.sectionSummary" />
        </div>
      </a-tab-pane>
      <a-tab-pane key="plan" title="下周工作计划">
        <div class="editor-wrapper">
          <RichTextEditor v-model="formData.sectionPlan" />
        </div>
      </a-tab-pane>
    </a-tabs>

    <div class="action-bar">
      <a-space>
        <a-button @click="goBack">取消</a-button>
        <a-button @click="handleSave" :loading="saving">
          <template #icon><icon-save /></template>
          保存草稿
        </a-button>
        <a-button type="primary" @click="handleSaveAndFinalize" :loading="saving">
          <template #icon><icon-check-circle /></template>
          保存并定稿
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { reportApi } from '@/api'
import dayjs from 'dayjs'
import RichTextEditor from './components/RichTextEditor.vue'

const route = useRoute()
const router = useRouter()

const reportId = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})
const isEdit = computed(() => !!reportId.value)

const currentYear = dayjs().year()
const currentWeek = dayjs().isoWeek()
const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear + 1; y >= currentYear - 5; y--) {
    years.push(y)
  }
  return years
})

const activeTab = ref('production')
const summarizing = ref(false)
const saving = ref(false)
const summaryData = ref<any>(null)

const formData = reactive({
  reportName: '',
  weekYear: currentYear,
  weekNumber: currentWeek,
  startDate: '',
  endDate: '',
  sectionProduction: '',
  sectionWaterQuality: '',
  sectionAlarm: '',
  sectionMaintenance: '',
  sectionSummary: '',
  sectionPlan: '',
  productionData: '',
  waterQualityData: '',
  alarmData: '',
  maintenanceData: ''
})

const productionData = computed(() => {
  try {
    return formData.productionData ? JSON.parse(formData.productionData) : {}
  } catch { return {} }
})

const waterQualityData = computed(() => {
  try {
    return formData.waterQualityData ? JSON.parse(formData.waterQualityData) : {}
  } catch { return {} }
})

const alarmData = computed(() => {
  try {
    return formData.alarmData ? JSON.parse(formData.alarmData) : {}
  } catch { return {} }
})

const maintenanceData = computed(() => {
  try {
    return formData.maintenanceData ? JSON.parse(formData.maintenanceData) : {}
  } catch { return {} }
})

const canSummarize = computed(() => {
  return formData.weekYear && formData.weekNumber && formData.startDate && formData.endDate
})

const calculateWeekRange = () => {
  if (!formData.weekYear || !formData.weekNumber) {
    formData.startDate = ''
    formData.endDate = ''
    return
  }
  const start = dayjs().year(formData.weekYear).isoWeek(formData.weekNumber).startOf('isoWeek')
  const end = start.add(6, 'day')
  formData.startDate = start.format('YYYY-MM-DD')
  formData.endDate = end.format('YYYY-MM-DD')
  if (!isEdit.value && formData.weekYear && formData.weekNumber) {
    formData.reportName = `${formData.weekYear}年第${formData.weekNumber}周运行周报`
  }
}

watch([() => formData.weekYear, () => formData.weekNumber], calculateWeekRange)

const handleSummarize = async () => {
  if (!canSummarize.value) {
    Message.warning('请先选择周次')
    return
  }
  summarizing.value = true
  try {
    const res: any = await reportApi.getWeeklySummary({
      start_date: formData.startDate,
      end_date: formData.endDate
    })
    const data = res.data
    summaryData.value = data
    formData.productionData = data.production_data
    formData.waterQualityData = data.water_quality_data
    formData.alarmData = data.alarm_data
    formData.maintenanceData = data.maintenance_data
    
    if (!formData.sectionProduction) formData.sectionProduction = data.section_production
    if (!formData.sectionWaterQuality) formData.sectionWaterQuality = data.section_water_quality
    if (!formData.sectionAlarm) formData.sectionAlarm = data.section_alarm
    if (!formData.sectionMaintenance) formData.sectionMaintenance = data.section_maintenance
    if (!formData.sectionSummary) formData.sectionSummary = data.section_summary
    if (!formData.sectionPlan) formData.sectionPlan = data.section_plan

    Message.success('数据提取成功，请在下方各章节进行编辑调整')
  } catch (e) {
    Message.error('数据提取失败')
  } finally {
    summarizing.value = false
  }
}

const fetchReportDetail = async () => {
  if (!reportId.value) return
  try {
    const res: any = await reportApi.getWeeklyReport(reportId.value)
    const r = res.data
    formData.reportName = r.report_name
    formData.weekYear = r.week_year
    formData.weekNumber = r.week_number
    formData.startDate = r.start_date
    formData.endDate = r.end_date
    formData.sectionProduction = r.section_production || ''
    formData.sectionWaterQuality = r.section_water_quality || ''
    formData.sectionAlarm = r.section_alarm || ''
    formData.sectionMaintenance = r.section_maintenance || ''
    formData.sectionSummary = r.section_summary || ''
    formData.sectionPlan = r.section_plan || ''
    formData.productionData = r.production_data || ''
    formData.waterQualityData = r.water_quality_data || ''
    formData.alarmData = r.alarm_data || ''
    formData.maintenanceData = r.maintenance_data || ''
    if (formData.productionData) summaryData.value = true
  } catch (e) {
    Message.error('获取周报详情失败')
  }
}

const validateForm = () => {
  if (!formData.reportName.trim()) {
    Message.warning('请输入周报名称')
    return false
  }
  if (!formData.weekYear || !formData.weekNumber) {
    Message.warning('请选择周次')
    return false
  }
  return true
}

const handleSave = async (finalize = false) => {
  if (!validateForm()) return
  saving.value = true
  try {
    const payload: any = {
      report_name: formData.reportName,
      week_year: formData.weekYear,
      week_number: formData.weekNumber,
      start_date: formData.startDate,
      end_date: formData.endDate,
      production_data: formData.productionData,
      water_quality_data: formData.waterQualityData,
      alarm_data: formData.alarmData,
      maintenance_data: formData.maintenanceData,
      section_production: formData.sectionProduction,
      section_water_quality: formData.sectionWaterQuality,
      section_alarm: formData.sectionAlarm,
      section_maintenance: formData.sectionMaintenance,
      section_summary: formData.sectionSummary,
      section_plan: formData.sectionPlan
    }

    if (isEdit.value) {
      await reportApi.updateWeeklyReport(reportId.value!, payload)
      if (finalize) {
        await reportApi.finalizeWeeklyReport(reportId.value!)
      }
    } else {
      const res: any = await reportApi.createWeeklyReport(payload)
      if (finalize) {
        await reportApi.finalizeWeeklyReport(res.data.id)
      }
    }
    Message.success(finalize ? '周报已定稿' : '保存成功')
    router.push('/report/weekly')
  } catch (e) {
    Message.error(finalize ? '定稿失败' : '保存失败')
  } finally {
    saving.value = false
  }
}

const handleSaveAndFinalize = () => {
  Modal.confirm({
    title: '确认定稿',
    content: '定稿后周报将不能再编辑，是否继续？',
    okText: '确认定稿',
    cancelText: '取消',
    onOk: () => handleSave(true)
  })
}

const goBack = () => {
  router.push('/report/weekly')
}

onMounted(() => {
  calculateWeekRange()
  if (isEdit.value) {
    fetchReportDetail()
  }
})
</script>

<style scoped>
.page-container {
  padding: 16px;
  padding-bottom: 100px;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
  display: inline;
}

.basic-info-card {
  margin-bottom: 16px;
}

.data-card {
  margin-bottom: 16px;
}

.data-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .data-overview {
    grid-template-columns: repeat(2, 1fr);
  }
}

.data-item {
  background: linear-gradient(135deg, #f7f8fa 0%, #f2f3f5 100%);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.data-label {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 8px;
}

.data-value {
  font-size: 28px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.data-value.highlight-green {
  color: #00B42A;
}

.data-unit {
  font-size: 14px;
  font-weight: 400;
  color: #86909c;
}

.data-sub {
  font-size: 12px;
  color: #86909c;
}

.editor-tabs {
  background: #fff;
  border-radius: 4px;
  padding: 0;
}

.editor-tabs :deep(.arco-tabs-header) {
  padding: 0 16px;
  border-bottom: 1px solid #e5e6eb;
}

.editor-wrapper {
  padding: 16px;
  min-height: 500px;
}

.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  border-top: 1px solid #e5e6eb;
  padding: 16px 24px;
  z-index: 100;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: flex-end;
}
</style>
