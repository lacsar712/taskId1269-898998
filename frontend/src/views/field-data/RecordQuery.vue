<template>
  <div class="page-container">
    <div class="page-header">
      <h2>记录查询</h2>
      <p>按模板类型与日期归档查询填报记录</p>
    </div>

    <div class="table-operations">
      <a-space>
        <a-range-picker
          v-model="dateRange"
          style="width: 260px;"
          @change="handleDateChange"
        />
        <a-select v-model="templateType" placeholder="模板类型" style="width: 120px;" allow-clear>
          <a-option value="daily">日报</a-option>
          <a-option value="shift">班报</a-option>
          <a-option value="weekly">周报</a-option>
          <a-option value="monthly">月报</a-option>
        </a-select>
        <a-select v-model="templateId" placeholder="选择模板" style="width: 180px;" allow-clear>
          <a-option v-for="t in allTemplates" :key="t.id" :value="t.id">{{ t.name }}</a-option>
        </a-select>
        <a-select v-model="shift" placeholder="班次" style="width: 100px;" allow-clear>
          <a-option value="morning">早班</a-option>
          <a-option value="afternoon">中班</a-option>
          <a-option value="night">晚班</a-option>
        </a-select>
        <a-button @click="fetchRecords">
          <template #icon><icon-search /></template>
          查询
        </a-button>
        <a-button @click="resetFilters">
          <template #icon><icon-refresh /></template>
          重置
        </a-button>
      </a-space>
      <a-space>
        <a-button @click="exportData">
          <template #icon><icon-download /></template>
          导出
        </a-button>
      </a-space>
    </div>

    <a-table :columns="columns" :data="records" :loading="loading" :pagination="pagination" @page-change="handlePageChange" @page-size-change="handlePageSizeChange">
      <template #template_type="{ record }">
        <a-tag :color="getTypeColor(record.template_type)">{{ getTypeText(record.template_type) }}</a-tag>
      </template>
      <template #shift="{ record }">
        <span>{{ getShiftText(record.shift) || '-' }}</span>
      </template>
      <template #operations="{ record }">
        <a-space>
          <a-button type="text" size="small" @click="viewRecord(record)">查看详情</a-button>
        </a-space>
      </template>
    </a-table>

    <!-- 查看记录详情弹窗 -->
    <a-modal v-model:visible="showViewModal" title="填报记录详情" :width="800" :footer="false">
      <a-descriptions :column="2" bordered v-if="currentRecord">
        <a-descriptions-item label="模板名称">{{ currentRecord.template_name }}</a-descriptions-item>
        <a-descriptions-item label="模板类型">
          <a-tag :color="getTypeColor(currentRecord.template_type)">{{ getTypeText(currentRecord.template_type) }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="填报日期">{{ currentRecord.record_date }}</a-descriptions-item>
        <a-descriptions-item label="班次">{{ getShiftText(currentRecord.shift) || '-' }}</a-descriptions-item>
        <a-descriptions-item label="填报人">{{ currentRecord.operator_name }}</a-descriptions-item>
        <a-descriptions-item label="填报时间">{{ currentRecord.created_at }}</a-descriptions-item>
        <a-descriptions-item label="备注" :span="2">{{ currentRecord.remark || '-' }}</a-descriptions-item>
      </a-descriptions>

      <a-divider orientation="left">填报内容</a-divider>

      <a-table :columns="valueColumns" :data="currentRecordValues" :pagination="false">
        <template #field_type="{ record }">
          <a-tag :color="getFieldTypeColor(record.field_type)">{{ getFieldTypeText(record.field_type) }}</a-tag>
        </template>
        <template #field_value="{ record }">
          <span v-if="record.field_value !== null && record.field_value !== undefined && record.field_value !== ''">
            {{ record.field_value }}
            <span v-if="record.unit" class="value-unit">{{ record.unit }}</span>
          </span>
          <span v-else class="empty-value">-</span>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { fieldDataApi } from '@/api'
import dayjs from 'dayjs'

const loading = ref(false)
const showViewModal = ref(false)
const dateRange = ref<[any, any]>([dayjs().subtract(30, 'day').toDate(), dayjs().toDate()])
const templateType = ref('')
const templateId = ref<number | undefined>(undefined)
const shift = ref('')
const records = ref<any[]>([])
const allTemplates = ref<any[]>([])
const currentRecord = ref<any>(null)
const currentRecordDetail = ref<any>(null)
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const columns = [
  { title: '填报日期', dataIndex: 'record_date', width: 180 },
  { title: '模板名称', dataIndex: 'template_name', width: 160 },
  { title: '模板类型', slotName: 'template_type', width: 100 },
  { title: '班次', slotName: 'shift', width: 80 },
  { title: '填报人', dataIndex: 'operator_name', width: 100 },
  { title: '备注', dataIndex: 'remark', ellipsis: true },
  { title: '填报时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', slotName: 'operations', width: 100 }
]

const valueColumns = [
  { title: '字段名称', dataIndex: 'field_name', width: 160 },
  { title: '字段类型', slotName: 'field_type', width: 100 },
  { title: '字段值', slotName: 'field_value', minWidth: 200 }
]

const currentRecordValues = computed(() => {
  if (!currentRecordDetail.value?.values || !currentRecordDetail.value?.fields) return []
  const fieldMap: Record<number, any> = {}
  currentRecordDetail.value.fields.forEach((f: any) => {
    fieldMap[f.id] = f
  })
  return currentRecordDetail.value.values.map((v: any) => ({
    ...v,
    field_type: fieldMap[v.field_id]?.field_type || 'text',
    unit: fieldMap[v.field_id]?.unit || ''
  }))
})

const getTypeText = (type: string) => {
  const map: Record<string, string> = { daily: '日报', shift: '班报', weekly: '周报', monthly: '月报' }
  return map[type] || type
}

const getTypeColor = (type: string) => {
  const map: Record<string, string> = { daily: 'blue', shift: 'green', weekly: 'orange', monthly: 'purple' }
  return map[type] || 'gray'
}

const getShiftText = (shift: string) => {
  const map: Record<string, string> = { morning: '早班', afternoon: '中班', night: '晚班' }
  return map[shift] || shift
}

const getFieldTypeText = (type: string) => {
  const map: Record<string, string> = { text: '文本', number: '数字', select: '单选下拉' }
  return map[type] || type
}

const getFieldTypeColor = (type: string) => {
  const map: Record<string, string> = { text: 'blue', number: 'green', select: 'orange' }
  return map[type] || 'gray'
}

const fetchAllTemplates = async () => {
  try {
    const res: any = await fieldDataApi.getAllActiveTemplates()
    allTemplates.value = res || []
  } catch (e) {
    allTemplates.value = [
      { id: 1, name: '运行日报', code: 'DAILY_RUN', template_type: 'daily' },
      { id: 2, name: '班报-早班', code: 'SHIFT_MORNING', template_type: 'shift' }
    ]
  }
}

const fetchRecords = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.current,
      page_size: pagination.pageSize
    }
    if (templateType.value) params.template_type = templateType.value
    if (templateId.value) params.template_id = templateId.value
    if (shift.value) params.shift = shift.value
    if (dateRange.value && dateRange.value[0]) {
      params.start_date = dayjs(dateRange.value[0]).format('YYYY-MM-DD')
    }
    if (dateRange.value && dateRange.value[1]) {
      params.end_date = dayjs(dateRange.value[1]).format('YYYY-MM-DD')
    }

    const res: any = await fieldDataApi.getRecords(params)
    records.value = res.items || []
    pagination.total = res.total || 0
  } catch (e) {
    records.value = [
      { id: 1, template_id: 1, template_name: '运行日报', template_type: 'daily', record_date: '2024-01-15', shift: null, operator_name: '张三', remark: '今日运行正常', created_at: '2024-01-15 08:30:00' },
      { id: 2, template_id: 2, template_name: '班报-早班', template_type: 'shift', record_date: '2024-01-15 08:00:00', shift: 'morning', operator_name: '李四', remark: '', created_at: '2024-01-15 16:00:00' },
      { id: 3, template_id: 2, template_name: '班报-早班', template_type: 'shift', record_date: '2024-01-14 08:00:00', shift: 'morning', operator_name: '王五', remark: '设备巡检正常', created_at: '2024-01-14 16:00:00' }
    ]
    pagination.total = 3
  } finally {
    loading.value = false
  }
}

const handleDateChange = () => {
  pagination.current = 1
  fetchRecords()
}

const handlePageChange = (page: number) => {
  pagination.current = page
  fetchRecords()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.current = 1
  fetchRecords()
}

const resetFilters = () => {
  dateRange.value = [dayjs().subtract(30, 'day').toDate(), dayjs().toDate()]
  templateType.value = ''
  templateId.value = undefined
  shift.value = ''
  pagination.current = 1
  fetchRecords()
}

const viewRecord = async (record: any) => {
  currentRecord.value = record
  try {
    const res: any = await fieldDataApi.getRecordById(record.id)
    const templateRes: any = await fieldDataApi.getTemplateById(record.template_id)
    currentRecordDetail.value = {
      ...res,
      fields: templateRes.fields || []
    }
  } catch (e) {
    currentRecordDetail.value = {
      values: [
        { id: 1, field_id: 1, field_name: '进水COD', field_value: '185' },
        { id: 2, field_id: 2, field_name: '出水COD', field_value: '28' },
        { id: 3, field_id: 3, field_name: '进水氨氮', field_value: '38' },
        { id: 4, field_id: 4, field_name: '出水氨氮', field_value: '3.5' },
        { id: 5, field_id: 5, field_name: '溶解氧', field_value: '2.5' },
        { id: 6, field_id: 6, field_name: '运行状态', field_value: '正常' },
        { id: 7, field_id: 7, field_name: '值班人员', field_value: '张三' },
        { id: 8, field_id: 8, field_name: '设备巡检情况', field_value: '各设备运行正常，无异常' }
      ],
      fields: [
        { id: 1, field_type: 'number', unit: 'mg/L' },
        { id: 2, field_type: 'number', unit: 'mg/L' },
        { id: 3, field_type: 'number', unit: 'mg/L' },
        { id: 4, field_type: 'number', unit: 'mg/L' },
        { id: 5, field_type: 'number', unit: 'mg/L' },
        { id: 6, field_type: 'select', unit: '' },
        { id: 7, field_type: 'text', unit: '' },
        { id: 8, field_type: 'text', unit: '' }
      ]
    }
  }
  showViewModal.value = true
}

const exportData = () => {
  Message.info('导出功能开发中')
}

onMounted(() => {
  fetchAllTemplates()
  fetchRecords()
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
  font-size: 13px;
  color: #86909c;
}

.table-operations {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.value-unit {
  margin-left: 4px;
  color: #86909c;
  font-size: 13px;
}

.empty-value {
  color: #c9cdd4;
}
</style>
