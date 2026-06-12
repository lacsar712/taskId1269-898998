<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模板管理</h2>
      <p>自定义日报、班报等现场数据采集模板，配置字段名称、类型、是否必填及默认值</p>
    </div>

    <div class="table-operations">
      <a-space>
        <a-input-search
          v-model="keyword"
          placeholder="搜索模板名称/编码"
          style="width: 240px;"
          @search="fetchTemplates"
        />
        <a-select v-model="templateType" placeholder="模板类型" style="width: 120px;" allow-clear>
          <a-option value="daily">日报</a-option>
          <a-option value="shift">班报</a-option>
          <a-option value="weekly">周报</a-option>
          <a-option value="monthly">月报</a-option>
        </a-select>
        <a-select v-model="isActive" placeholder="状态" style="width: 100px;" allow-clear>
          <a-option :value="true">启用</a-option>
          <a-option :value="false">停用</a-option>
        </a-select>
        <a-button @click="fetchTemplates">
          <template #icon><icon-search /></template>
          查询
        </a-button>
      </a-space>
      <a-button type="primary" @click="openCreateModal">
        <template #icon><icon-plus /></template>
        新建模板
      </a-button>
    </div>

    <a-table :columns="columns" :data="templates" :loading="loading" :pagination="pagination" @page-change="handlePageChange" @page-size-change="handlePageSizeChange">
      <template #template_type="{ record }">
        <a-tag :color="getTypeColor(record.template_type)">{{ getTypeText(record.template_type) }}</a-tag>
      </template>
      <template #is_active="{ record }">
        <a-tag :color="record.is_active ? 'green' : 'gray'">{{ record.is_active ? '启用' : '停用' }}</a-tag>
      </template>
      <template #operations="{ record }">
        <a-space>
          <a-button type="text" size="small" @click="viewTemplate(record)">查看</a-button>
          <a-button type="text" size="small" @click="editTemplate(record)">编辑</a-button>
          <a-button type="text" size="small" @click="toggleStatus(record)">
            {{ record.is_active ? '停用' : '启用' }}
          </a-button>
          <a-button type="text" size="small" status="danger" @click="deleteTemplate(record)">删除</a-button>
        </a-space>
      </template>
    </a-table>

    <!-- 新建/编辑模板弹窗 -->
    <a-modal
      v-model:visible="showModal"
      :title="isEdit ? '编辑模板' : '新建模板'"
      :width="900"
      @ok="handleSubmit"
      :ok-loading="submitLoading"
      :mask-closable="false"
    >
      <a-form :model="templateForm" layout="vertical" ref="formRef">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="模板名称" required>
              <a-input v-model="templateForm.name" placeholder="请输入模板名称" :max-length="100" show-word-limit />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="模板编码" required>
              <a-input v-model="templateForm.code" placeholder="请输入模板编码" :max-length="50" :disabled="isEdit" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="模板类型" required>
              <a-select v-model="templateForm.template_type">
                <a-option value="daily">日报</a-option>
                <a-option value="shift">班报</a-option>
                <a-option value="weekly">周报</a-option>
                <a-option value="monthly">月报</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="模板描述">
          <a-textarea v-model="templateForm.description" :max-length="500" show-word-limit :auto-size="{ minRows: 2 }" />
        </a-form-item>
        <a-form-item label="是否启用">
          <a-switch v-model="templateForm.is_active" />
        </a-form-item>

        <a-divider orientation="left">字段配置</a-divider>

        <div class="field-list">
          <a-space direction="vertical" :size="12" style="width: 100%;">
            <div v-for="(field, index) in templateForm.fields" :key="field.key" class="field-item">
              <a-card :bordered="false" class="field-card">
                <template #extra>
                  <a-space>
                    <a-button type="text" size="small" @click="moveField(index, -1)" :disabled="index === 0">
                      <icon-up />
                    </a-button>
                    <a-button type="text" size="small" @click="moveField(index, 1)" :disabled="index === templateForm.fields.length - 1">
                      <icon-down />
                    </a-button>
                    <a-button type="text" size="small" status="danger" @click="removeField(index)">
                      <icon-delete />
                    </a-button>
                  </a-space>
                </template>
                <a-row :gutter="12">
                  <a-col :span="5">
                    <a-form-item label="字段名称" required>
                      <a-input v-model="field.field_name" placeholder="字段名称" :max-length="100" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="5">
                    <a-form-item label="字段编码" required>
                      <a-input v-model="field.field_code" placeholder="字段编码" :max-length="50" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="4">
                    <a-form-item label="数据类型" required>
                      <a-select v-model="field.field_type" @change="handleFieldTypeChange(index)">
                        <a-option value="text">文本</a-option>
                        <a-option value="number">数字</a-option>
                        <a-option value="select">单选下拉</a-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                  <a-col :span="3">
                    <a-form-item label="单位">
                      <a-input v-model="field.unit" placeholder="如: mg/L" :max-length="20" :disabled="field.field_type !== 'number'" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="4">
                    <a-form-item label="默认值">
                      <a-input v-if="field.field_type !== 'select'" v-model="field.default_value" placeholder="默认值" :max-length="500" />
                      <a-select v-else v-model="field.default_value" placeholder="选择默认值">
                        <a-option v-for="opt in getOptionsList(field.options)" :key="opt" :value="opt">{{ opt }}</a-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                  <a-col :span="3">
                    <a-form-item label="是否必填">
                      <a-switch v-model="field.is_required" />
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-row v-if="field.field_type === 'select'" :gutter="12">
                  <a-col :span="24">
                    <a-form-item label="下拉选项" required>
                      <a-textarea
                        v-model="field.options_text"
                        placeholder="每行一个选项，例如：&#10;正常&#10;偏高&#10;偏低"
                        :auto-size="{ minRows: 3 }"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>
              </a-card>
            </div>
          </a-space>
        </div>

        <a-button type="dashed" long @click="addField" style="margin-top: 8px;">
          <template #icon><icon-plus /></template>
          添加字段
        </a-button>
      </a-form>
    </a-modal>

    <!-- 查看模板详情弹窗 -->
    <a-modal v-model:visible="showViewModal" title="模板详情" :width="800" :footer="false">
      <a-descriptions :column="2" bordered v-if="currentTemplate">
        <a-descriptions-item label="模板名称">{{ currentTemplate.name }}</a-descriptions-item>
        <a-descriptions-item label="模板编码">{{ currentTemplate.code }}</a-descriptions-item>
        <a-descriptions-item label="模板类型">{{ getTypeText(currentTemplate.template_type) }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="currentTemplate.is_active ? 'green' : 'gray'">{{ currentTemplate.is_active ? '启用' : '停用' }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="创建人">{{ currentTemplate.created_by_name }}</a-descriptions-item>
        <a-descriptions-item label="创建时间">{{ currentTemplate.created_at }}</a-descriptions-item>
        <a-descriptions-item label="描述" :span="2">{{ currentTemplate.description || '-' }}</a-descriptions-item>
      </a-descriptions>

      <a-divider orientation="left">字段列表</a-divider>

      <a-table :columns="fieldColumns" :data="currentTemplate?.fields || []" :pagination="false">
        <template #field_type="{ record }">
          <a-tag :color="getFieldTypeColor(record.field_type)">{{ getFieldTypeText(record.field_type) }}</a-tag>
        </template>
        <template #is_required="{ record }">
          <a-tag :color="record.is_required ? 'red' : 'gray'">{{ record.is_required ? '是' : '否' }}</a-tag>
        </template>
        <template #options="{ record }">
          <template v-if="record.field_type === 'select' && record.options">
            <a-tag v-for="opt in getOptionsList(record.options)" :key="opt" style="margin-bottom: 4px;">{{ opt }}</a-tag>
          </template>
          <span v-else>-</span>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { fieldDataApi } from '@/api'

const loading = ref(false)
const submitLoading = ref(false)
const showModal = ref(false)
const showViewModal = ref(false)
const isEdit = ref(false)
const keyword = ref('')
const templateType = ref('')
const isActive = ref<boolean | undefined>(undefined)
const templates = ref<any[]>([])
const currentTemplate = ref<any>(null)
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })
const formRef = ref()

const templateForm = reactive({
  id: null as number | null,
  name: '',
  code: '',
  description: '',
  template_type: 'daily',
  is_active: true,
  fields: [] as any[]
})

const columns = [
  { title: '模板名称', dataIndex: 'name', width: 180 },
  { title: '模板编码', dataIndex: 'code', width: 140 },
  { title: '类型', slotName: 'template_type', width: 100 },
  { title: '状态', slotName: 'is_active', width: 80 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
  { title: '创建人', dataIndex: 'created_by_name', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', slotName: 'operations', width: 200 }
]

const fieldColumns = [
  { title: '排序', dataIndex: 'sort_order', width: 60 },
  { title: '字段名称', dataIndex: 'field_name', width: 140 },
  { title: '字段编码', dataIndex: 'field_code', width: 140 },
  { title: '数据类型', slotName: 'field_type', width: 100 },
  { title: '单位', dataIndex: 'unit', width: 80 },
  { title: '默认值', dataIndex: 'default_value', width: 120 },
  { title: '是否必填', slotName: 'is_required', width: 80 },
  { title: '下拉选项', slotName: 'options', minWidth: 200 }
]

const getTypeText = (type: string) => {
  const map: Record<string, string> = { daily: '日报', shift: '班报', weekly: '周报', monthly: '月报' }
  return map[type] || type
}

const getTypeColor = (type: string) => {
  const map: Record<string, string> = { daily: 'blue', shift: 'green', weekly: 'orange', monthly: 'purple' }
  return map[type] || 'gray'
}

const getFieldTypeText = (type: string) => {
  const map: Record<string, string> = { text: '文本', number: '数字', select: '单选下拉' }
  return map[type] || type
}

const getFieldTypeColor = (type: string) => {
  const map: Record<string, string> = { text: 'blue', number: 'green', select: 'orange' }
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

const generateFieldKey = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

const fetchTemplates = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.current,
      page_size: pagination.pageSize
    }
    if (keyword.value) params.keyword = keyword.value
    if (templateType.value) params.template_type = templateType.value
    if (isActive.value !== undefined) params.is_active = isActive.value

    const res: any = await fieldDataApi.getTemplates(params)
    templates.value = res.items || []
    pagination.total = res.total || 0
  } catch (e) {
    templates.value = [
      { id: 1, name: '运行日报', code: 'DAILY_RUN', template_type: 'daily', is_active: true, description: '每日运行数据填报', created_by_name: '系统管理员', created_at: '2024-01-15 08:00:00' },
      { id: 2, name: '班报-早班', code: 'SHIFT_MORNING', template_type: 'shift', is_active: true, description: '早班现场数据采集', created_by_name: '系统管理员', created_at: '2024-01-15 09:00:00' },
      { id: 3, name: '水质周报', code: 'WEEKLY_WATER', template_type: 'weekly', is_active: false, description: '每周水质分析汇总', created_by_name: '系统管理员', created_at: '2024-01-10 10:00:00' }
    ]
    pagination.total = 3
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.current = page
  fetchTemplates()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.current = 1
  fetchTemplates()
}

const openCreateModal = () => {
  isEdit.value = false
  templateForm.id = null
  templateForm.name = ''
  templateForm.code = ''
  templateForm.description = ''
  templateForm.template_type = 'daily'
  templateForm.is_active = true
  templateForm.fields = [createEmptyField()]
  showModal.value = true
}

const createEmptyField = () => ({
  key: generateFieldKey(),
  id: null,
  field_name: '',
  field_code: '',
  field_type: 'text',
  is_required: false,
  default_value: '',
  options: '',
  options_text: '',
  unit: '',
  sort_order: 0
})

const addField = () => {
  const newField = createEmptyField()
  newField.sort_order = templateForm.fields.length
  templateForm.fields.push(newField)
}

const removeField = (index: number) => {
  if (templateForm.fields.length <= 1) {
    Message.warning('至少保留一个字段')
    return
  }
  templateForm.fields.splice(index, 1)
  templateForm.fields.forEach((f, i) => {
    f.sort_order = i
  })
}

const moveField = (index: number, direction: number) => {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= templateForm.fields.length) return
  const temp = templateForm.fields[index]
  templateForm.fields[index] = templateForm.fields[newIndex]
  templateForm.fields[newIndex] = temp
  templateForm.fields.forEach((f, i) => {
    f.sort_order = i
  })
}

const handleFieldTypeChange = (index: number) => {
  const field = templateForm.fields[index]
  if (field.field_type !== 'number') {
    field.unit = ''
  }
  if (field.field_type !== 'select') {
    field.options = ''
    field.options_text = ''
  }
  field.default_value = ''
}

const editTemplate = async (record: any) => {
  isEdit.value = true
  try {
    const res: any = await fieldDataApi.getTemplateById(record.id)
    templateForm.id = res.id
    templateForm.name = res.name
    templateForm.code = res.code
    templateForm.description = res.description
    templateForm.template_type = res.template_type
    templateForm.is_active = res.is_active
    templateForm.fields = (res.fields || []).map((f: any, i: number) => ({
      key: generateFieldKey(),
      id: f.id,
      field_name: f.field_name,
      field_code: f.field_code,
      field_type: f.field_type,
      is_required: f.is_required,
      default_value: f.default_value,
      options: f.options,
      options_text: f.field_type === 'select' && f.options ? getOptionsList(f.options).join('\n') : '',
      unit: f.unit,
      sort_order: f.sort_order ?? i
    })).sort((a: any, b: any) => a.sort_order - b.sort_order)
    showModal.value = true
  } catch (e) {
    Message.error('获取模板详情失败')
  }
}

const viewTemplate = async (record: any) => {
  try {
    const res: any = await fieldDataApi.getTemplateById(record.id)
    currentTemplate.value = res
    showViewModal.value = true
  } catch (e) {
    currentTemplate.value = {
      ...record,
      fields: [
        { id: 1, field_name: '进水COD', field_code: 'COD_IN', field_type: 'number', unit: 'mg/L', default_value: '', is_required: true, sort_order: 1, options: null },
        { id: 2, field_name: '出水COD', field_code: 'COD_OUT', field_type: 'number', unit: 'mg/L', default_value: '', is_required: true, sort_order: 2, options: null },
        { id: 3, field_name: '运行状态', field_code: 'STATUS', field_type: 'select', unit: '', default_value: '正常', is_required: true, sort_order: 3, options: '["正常","异常","停机"]' }
      ]
    }
    showViewModal.value = true
  }
}

const toggleStatus = async (record: any) => {
  const action = record.is_active ? '停用' : '启用'
  Modal.confirm({
    title: `确认${action}`,
    content: `确定要${action}模板【${record.name}】吗？`,
    onOk: async () => {
      try {
        await fieldDataApi.toggleTemplateStatus(record.id)
        Message.success(`${action}成功`)
        fetchTemplates()
      } catch (e) {
        Message.error(`${action}失败`)
      }
    }
  })
}

const deleteTemplate = async (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除模板【${record.name}】吗？已有填报记录的模板无法删除。`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await fieldDataApi.deleteTemplate(record.id)
        Message.success('删除成功')
        fetchTemplates()
      } catch (e: any) {
        Message.error(e.response?.data?.detail || '删除失败')
      }
    }
  })
}

const validateForm = () => {
  if (!templateForm.name.trim()) {
    Message.warning('请输入模板名称')
    return false
  }
  if (!templateForm.code.trim()) {
    Message.warning('请输入模板编码')
    return false
  }
  for (let i = 0; i < templateForm.fields.length; i++) {
    const field = templateForm.fields[i]
    if (!field.field_name.trim()) {
      Message.warning(`第${i + 1}个字段请输入字段名称`)
      return false
    }
    if (!field.field_code.trim()) {
      Message.warning(`第${i + 1}个字段请输入字段编码`)
      return false
    }
    if (field.field_type === 'select') {
      const options = field.options_text?.split('\n').filter((o: string) => o.trim())
      if (!options || options.length === 0) {
        Message.warning(`字段【${field.field_name}】请输入下拉选项`)
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
    const fields = templateForm.fields.map((f, i) => {
      const fieldData: any = {
        field_name: f.field_name,
        field_code: f.field_code,
        field_type: f.field_type,
        is_required: f.is_required,
        default_value: f.default_value || undefined,
        unit: f.field_type === 'number' ? f.unit || undefined : undefined,
        sort_order: i
      }
      if (f.id) fieldData.id = f.id
      if (f.field_type === 'select') {
        const options = f.options_text?.split('\n').filter((o: string) => o.trim()) || []
        fieldData.options = JSON.stringify(options)
      }
      return fieldData
    })

    const data: any = {
      name: templateForm.name,
      code: templateForm.code,
      description: templateForm.description || undefined,
      template_type: templateForm.template_type,
      is_active: templateForm.is_active,
      fields
    }

    if (isEdit.value && templateForm.id) {
      await fieldDataApi.updateTemplate(templateForm.id, data)
      Message.success('更新成功')
    } else {
      await fieldDataApi.createTemplate(data)
      Message.success('创建成功')
    }

    showModal.value = false
    fetchTemplates()
  } catch (e: any) {
    Message.error(e.response?.data?.detail || '保存失败')
  } finally {
    submitLoading.value = false
  }
}

fetchTemplates()
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

.field-list {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}

.field-card {
  background: #f7f8fa;
}

.field-card :deep(.arco-card-header) {
  padding: 8px 16px;
  border-bottom: none;
}

.field-card :deep(.arco-card-body) {
  padding: 0 16px 16px 16px;
}
</style>
