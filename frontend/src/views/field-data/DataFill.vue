<template>
  <div class="page-container">
    <div class="page-header">
      <h2>数据填报</h2>
      <p>选择模板后按表单填写当日或当班现场数据并提交</p>
    </div>

    <div v-if="!selectedTemplate" class="template-select-section">
      <div class="section-title">请选择填报模板</div>
      <a-row :gutter="16">
        <a-col :span="6" v-for="template in activeTemplates" :key="template.id">
          <a-card
            hoverable
            class="template-card"
            @click="selectTemplate(template)"
          >
            <div class="template-icon" :class="template.template_type">
              <icon-file />
            </div>
            <div class="template-info">
              <div class="template-name">{{ template.name }}</div>
              <div class="template-meta">
                <a-tag :color="getTypeColor(template.template_type)" size="small">
                  {{ getTypeText(template.template_type) }}
                </a-tag>
              </div>
              <div class="template-desc">{{ template.description || '暂无描述' }}</div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-if="activeTemplates.length === 0" description="暂无可用的填报模板">
        <template #image>
          <icon-file />
        </template>
      </a-empty>
    </div>

    <div v-else class="fill-form-section">
      <div class="form-header">
        <a-space>
          <a-button @click="backToSelect">
            <template #icon><icon-left /></template>
            返回选择
          </a-button>
          <div class="current-template">
            <icon-file />
            <span class="template-name">{{ selectedTemplate.name }}</span>
            <a-tag :color="getTypeColor(selectedTemplate.template_type)" size="small">
              {{ getTypeText(selectedTemplate.template_type) }}
            </a-tag>
          </div>
        </a-space>
      </div>

      <a-card class="form-card">
        <a-form :model="fillForm" layout="vertical" ref="formRef">
          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item label="填报日期" required>
                <a-date-picker v-model="fillForm.record_date" style="width: 100%;" :show-time="selectedTemplate.template_type === 'shift'" />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="班次" v-if="selectedTemplate.template_type === 'shift'" required>
                <a-select v-model="fillForm.shift" style="width: 100%;">
                  <a-option value="morning">早班</a-option>
                  <a-option value="afternoon">中班</a-option>
                  <a-option value="night">晚班</a-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-divider orientation="left">填报内容</a-divider>

          <a-row :gutter="24">
            <a-col :span="12" v-for="field in sortedFields" :key="field.id">
              <a-form-item :label="field.field_name + (field.is_required ? ' *' : '')">
                <template v-if="field.field_type === 'number'">
                  <a-input-number
                    v-model="fillForm.values[field.id]"
                    :placeholder="'请输入' + field.field_name"
                    :style="{ width: '100%' }"
                    :default-value="field.default_value ? parseFloat(field.default_value) : undefined"
                  />
                  <span v-if="field.unit" class="field-unit">{{ field.unit }}</span>
                </template>
                <template v-else-if="field.field_type === 'select'">
                  <a-select
                    v-model="fillForm.values[field.id]"
                    :placeholder="'请选择' + field.field_name"
                    style="width: 100%;"
                    :default-value="field.default_value || undefined"
                  >
                    <a-option v-for="opt in getOptionsList(field.options)" :key="opt" :value="opt">
                      {{ opt }}
                    </a-option>
                  </a-select>
                </template>
                <template v-else>
                  <a-textarea
                    v-model="fillForm.values[field.id]"
                    :placeholder="'请输入' + field.field_name"
                    :auto-size="{ minRows: 2, maxRows: 4 }"
                    :default-value="field.default_value || undefined"
                    :max-length="500"
                    show-word-limit
                  />
                </template>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="备注">
            <a-textarea
              v-model="fillForm.remark"
              placeholder="请输入备注信息（选填）"
              :auto-size="{ minRows: 2, maxRows: 4 }"
              :max-length="1000"
              show-word-limit
            />
          </a-form-item>

          <a-space style="margin-top: 24px;">
            <a-button type="primary" :loading="submitLoading" @click="handleSubmit">
              <template #icon><icon-save /></template>
              提交填报
            </a-button>
            <a-button @click="resetForm">
              <template #icon><icon-redo /></template>
              重置
            </a-button>
          </a-space>
        </a-form>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { fieldDataApi } from '@/api'
import dayjs from 'dayjs'

const loading = ref(false)
const submitLoading = ref(false)
const activeTemplates = ref<any[]>([])
const selectedTemplate = ref<any>(null)
const formRef = ref()

const fillForm = reactive({
  template_id: null as number | null,
  record_date: dayjs().toISOString(),
  shift: 'morning',
  remark: '',
  values: {} as Record<number, any>
})

const sortedFields = computed(() => {
  if (!selectedTemplate.value?.fields) return []
  return [...selectedTemplate.value.fields].sort((a: any, b: any) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
})

const getTypeText = (type: string) => {
  const map: Record<string, string> = { daily: '日报', shift: '班报', weekly: '周报', monthly: '月报' }
  return map[type] || type
}

const getTypeColor = (type: string) => {
  const map: Record<string, string> = { daily: 'blue', shift: 'green', weekly: 'orange', monthly: 'purple' }
  return map[type] || 'gray'
}

const getOptionsList = (options: string) => {
  if (!options) return []
  try {
    const parsed = JSON.parse(options)
    if (Array.isArray(parsed)) return parsed
  } catch (e) {}
  return options.split('\n').filter((o: string) => o.trim())
}

const fetchActiveTemplates = async () => {
  loading.value = true
  try {
    const res: any = await fieldDataApi.getAllActiveTemplates()
    activeTemplates.value = res || []
  } catch (e) {
    activeTemplates.value = [
      { id: 1, name: '运行日报', code: 'DAILY_RUN', template_type: 'daily', is_active: true, description: '每日运行数据填报' },
      { id: 2, name: '班报-早班', code: 'SHIFT_MORNING', template_type: 'shift', is_active: true, description: '早班现场数据采集' },
      { id: 3, name: '生产运行班报', code: 'SHIFT_PROD', template_type: 'shift', is_active: true, description: '生产运行数据班报' }
    ]
  } finally {
    loading.value = false
  }
}

const selectTemplate = async (template: any) => {
  try {
    const res: any = await fieldDataApi.getTemplateById(template.id)
    selectedTemplate.value = res
  } catch (e) {
    selectedTemplate.value = {
      ...template,
      fields: [
        { id: 1, field_name: '进水COD', field_code: 'COD_IN', field_type: 'number', unit: 'mg/L', default_value: '', is_required: true, sort_order: 1, options: null },
        { id: 2, field_name: '出水COD', field_code: 'COD_OUT', field_type: 'number', unit: 'mg/L', default_value: '', is_required: true, sort_order: 2, options: null },
        { id: 3, field_name: '进水氨氮', field_code: 'NH3N_IN', field_type: 'number', unit: 'mg/L', default_value: '', is_required: true, sort_order: 3, options: null },
        { id: 4, field_name: '出水氨氮', field_code: 'NH3N_OUT', field_type: 'number', unit: 'mg/L', default_value: '', is_required: true, sort_order: 4, options: null },
        { id: 5, field_name: '溶解氧', field_code: 'DO', field_type: 'number', unit: 'mg/L', default_value: '2.0', is_required: false, sort_order: 5, options: null },
        { id: 6, field_name: '运行状态', field_code: 'STATUS', field_type: 'select', unit: '', default_value: '正常', is_required: true, sort_order: 6, options: '["正常","异常","停机"]' },
        { id: 7, field_name: '值班人员', field_code: 'DUTY', field_type: 'text', unit: '', default_value: '', is_required: false, sort_order: 7, options: null },
        { id: 8, field_name: '设备巡检情况', field_code: 'INSPECTION', field_type: 'text', unit: '', default_value: '', is_required: false, sort_order: 8, options: null }
      ]
    }
  }
  fillForm.template_id = template.id
  fillForm.record_date = dayjs().toISOString()
  fillForm.shift = 'morning'
  fillForm.remark = ''
  fillForm.values = {}
  if (selectedTemplate.value.fields) {
    selectedTemplate.value.fields.forEach((f: any) => {
      if (f.default_value !== null && f.default_value !== undefined && f.default_value !== '') {
        if (f.field_type === 'number') {
          fillForm.values[f.id] = parseFloat(f.default_value)
        } else {
          fillForm.values[f.id] = f.default_value
        }
      }
    })
  }
}

const backToSelect = () => {
  selectedTemplate.value = null
  fillForm.template_id = null
}

const validateForm = () => {
  if (!fillForm.record_date) {
    Message.warning('请选择填报日期')
    return false
  }
  if (selectedTemplate.value.template_type === 'shift' && !fillForm.shift) {
    Message.warning('请选择班次')
    return false
  }
  for (const field of sortedFields.value) {
    const value = fillForm.values[field.id]
    if (field.is_required && (value === null || value === undefined || value === '')) {
      Message.warning(`请填写必填项：${field.field_name}`)
      return false
    }
    if (field.field_type === 'number' && value !== '' && value !== null && value !== undefined) {
      if (isNaN(parseFloat(value))) {
        Message.warning(`字段【${field.field_name}】必须是数字`)
        return false
      }
    }
  }
  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return

  submitLoading.value = true
  try {
    const values = sortedFields.value.map((field: any) => ({
      field_id: field.id,
      field_name: field.field_name,
      field_value: fillForm.values[field.id] !== undefined && fillForm.values[field.id] !== null
        ? String(fillForm.values[field.id])
        : ''
    }))

    const data = {
      template_id: fillForm.template_id,
      record_date: fillForm.record_date,
      shift: selectedTemplate.value.template_type === 'shift' ? fillForm.shift : undefined,
      remark: fillForm.remark || undefined,
      values
    }

    await fieldDataApi.createRecord(data)
    Message.success('填报成功')
    backToSelect()
  } catch (e: any) {
    Message.error(e.response?.data?.detail || '填报失败')
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  fillForm.record_date = dayjs().toISOString()
  fillForm.shift = 'morning'
  fillForm.remark = ''
  fillForm.values = {}
  if (selectedTemplate.value?.fields) {
    selectedTemplate.value.fields.forEach((f: any) => {
      if (f.default_value !== null && f.default_value !== undefined && f.default_value !== '') {
        if (f.field_type === 'number') {
          fillForm.values[f.id] = parseFloat(f.default_value)
        } else {
          fillForm.values[f.id] = f.default_value
        }
      }
    })
  }
}

onMounted(() => {
  fetchActiveTemplates()
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

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 16px;
}

.template-select-section {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 16px;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.template-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
  margin-bottom: 12px;
}

.template-icon.daily {
  background: linear-gradient(135deg, #165dff 0%, #4080ff 100%);
}

.template-icon.shift {
  background: linear-gradient(135deg, #00b42a 0%, #23c343 100%);
}

.template-icon.weekly {
  background: linear-gradient(135deg, #ff7d00 0%, #ff9a2e 100%);
}

.template-icon.monthly {
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
}

.template-info .template-name {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 8px;
}

.template-info .template-meta {
  margin-bottom: 8px;
}

.template-info .template-desc {
  font-size: 12px;
  color: #86909c;
  line-height: 1.5;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.current-template {
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-template .template-name {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.form-card {
  background: #fff;
  padding: 24px;
}

.field-unit {
  margin-left: 8px;
  color: #86909c;
  font-size: 13px;
}
</style>
