<template>
  <div class="page-container">
    <div class="page-header">
      <div class="header-left">
        <h2>排放因子管理</h2>
        <p>维护各类排放因子参数 · 因子调整即时重算预览</p>
      </div>
      <div class="header-right">
        <a-space>
          <a-select v-model="targetYear" style="width: 130px;" @change="handleYearChange">
            <a-option v-for="y in yearOptions" :key="y" :value="y">{{ y }} 年目标</a-option>
          </a-select>
          <a-button type="outline" @click="openTargetModal">
            <template #icon><icon-edit /></template>
            减排目标
          </a-button>
          <a-button type="primary" @click="openFactorModal()">
            <template #icon><icon-plus /></template>
            新增因子
          </a-button>
        </a-space>
      </div>
    </div>

    <a-row :gutter="16" class="preview-row">
      <a-col :span="8">
        <a-card class="preview-card" :bordered="false">
          <div class="preview-label">当前总排放量（按现有因子）</div>
          <div class="preview-value current">
            {{ formatNumber(currentTotalEmission) }}
            <span class="preview-unit">t CO₂e</span>
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="preview-card" :bordered="false">
          <div class="preview-label">调整因子后预测排放量</div>
          <div class="preview-value" :class="previewDiff >= 0 ? 'increase' : 'decrease'">
            {{ formatNumber(previewTotalEmission) }}
            <span class="preview-unit">t CO₂e</span>
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="preview-card" :bordered="false">
          <div class="preview-label">变化量</div>
          <div class="preview-value" :class="previewDiff >= 0 ? 'increase' : 'decrease'">
            <icon-arrow-up v-if="previewDiff > 0" />
            <icon-arrow-down v-else-if="previewDiff < 0" />
            {{ previewDiff > 0 ? '+' : '' }}{{ formatNumber(Math.abs(previewDiff)) }}
            <span class="preview-unit">t ({{ previewDiffPercent > 0 ? '+' : '' }}{{ previewDiffPercent }}%)</span>
          </div>
          <a-alert
            v-if="hasFactorChanges"
            type="info"
            style="margin-top: 12px; padding: 6px 12px;"
            size="small"
            :show-icon="true"
          >
            因子已修改，<a @click="applyChanges" style="color:#165DFF;">点击保存更改</a>
          </a-alert>
        </a-card>
      </a-col>
    </a-row>

    <a-card :bordered="false" title="排放因子列表">
      <template #extra>
        <a-space>
          <a-input-search
            v-model="searchKeyword"
            placeholder="搜索因子名称"
            style="width: 200px;"
            @search="handleSearch"
          />
          <a-select v-model="categoryFilter" placeholder="排放源分类" style="width: 140px;" allow-clear>
            <a-option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</a-option>
          </a-select>
        </a-space>
      </template>

      <a-table
        :columns="factorColumns"
        :data="filteredFactors"
        :pagination="pagination"
        @page-change="handlePageChange"
        :row-key="record => record.id"
      >
        <template #category="{ record }">
          <a-tag :color="categoryColors[record.category] || 'blue'">{{ record.category }}</a-tag>
        </template>
        <template #factor_value="{ record }">
          <a-input-number
            :model-value="record.factor_value"
            :min="0"
            :step="getStep(record.factor_value)"
            :precision="getPrecision(record.factor_value)"
            style="width: 140px;"
            @update:model-value="(v) => handleFactorChange(record.id, 'factor_value', v)"
          />
        </template>
        <template #unit="{ record }">
          <span class="unit-cell">{{ record.unit }}</span>
        </template>
        <template #source_ref="{ record }">
          <a-tooltip :content="record.source_ref" :mini="true">
            <span class="ref-cell">{{ record.source_ref }}</span>
          </a-tooltip>
        </template>
        <template #action="{ record }">
          <a-space size="mini">
            <a-button type="text" size="small" @click="openFactorModal(record)">编辑</a-button>
            <a-button
              type="text"
              size="small"
              status="danger"
              @click="handleDelete(record)"
            >删除</a-button>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:visible="factorModalVisible"
      :title="editingFactor ? '编辑排放因子' : '新增排放因子'"
      @ok="handleFactorSubmit"
      @cancel="factorModalVisible = false"
      ok-text="保存"
      cancel-text="取消"
      :mask-closable="false"
    >
      <a-form :model="factorForm" layout="vertical" ref="factorFormRef">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item field="name" label="因子名称" :rules="[{ required: true, message: '请输入因子名称' }]">
              <a-input v-model="factorForm.name" placeholder="如：电力排放因子" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="category" label="排放源分类" :rules="[{ required: true, message: '请选择分类' }]">
              <a-select v-model="factorForm.category" placeholder="选择分类">
                <a-option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="factor_value" label="排放因子值" :rules="[{ required: true, message: '请输入排放因子值' }]">
              <a-input-number
                v-model="factorForm.factor_value"
                :min="0"
                :step="0.0001"
                :precision="4"
                style="width: 100%;"
                placeholder="单位排放量"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="unit" label="单位" :rules="[{ required: true, message: '请输入单位' }]">
              <a-input v-model="factorForm.unit" placeholder="如：kgCO₂e/kWh" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="activity_data" label="参考年活动量">
              <a-input-number
                v-model="factorForm.activity_data"
                :min="0"
                style="width: 100%;"
                placeholder="用于核算预览的活动量"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="effective_date" label="生效日期">
              <a-date-picker
                v-model="factorForm.effective_date"
                style="width: 100%;"
                value-format="YYYY-MM-DD"
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item field="source_ref" label="数据来源/引用标准">
              <a-textarea
                v-model="factorForm.source_ref"
                :auto-size="{ minRows: 2, maxRows: 4 }"
                placeholder="如：IPCC 2021指南 或 省级电网排放因子"
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item field="description" label="备注说明">
              <a-textarea
                v-model="factorForm.description"
                :auto-size="{ minRows: 2, maxRows: 3 }"
                placeholder="因子适用范围、注意事项等"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <a-modal
      v-model:visible="targetModalVisible"
      title="减排目标设置"
      @ok="handleTargetSubmit"
      @cancel="targetModalVisible = false"
      ok-text="保存目标"
      cancel-text="取消"
      :mask-closable="false"
      :width="560"
    >
      <a-form :model="targetForm" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item field="year" label="年度">
              <a-select v-model="targetForm.year">
                <a-option v-for="y in yearOptions" :key="y" :value="y">{{ y }} 年</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="target_value" label="年度排放上限目标 (t CO₂e)" :rules="[{ required: true, message: '请输入目标值' }]">
              <a-input-number
                v-model="targetForm.target_value"
                :min="0"
                style="width: 100%;"
                placeholder="年度最大允许排放量"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="baseline_year" label="基准年">
              <a-select v-model="targetForm.baseline_year">
                <a-option v-for="y in baselineOptions" :key="y" :value="y">{{ y }} 年</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="reduction_rate" label="较基准年减排率 (%)" :rules="[{ required: true, message: '请输入减排率' }]">
              <a-input-number
                v-model="targetForm.reduction_rate"
                :min="0"
                :max="100"
                :precision="2"
                style="width: 100%;"
                placeholder="如：5.0"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-alert type="info" style="margin-top: 8px;">
          <template #icon><icon-info /></template>
          基于 {{ targetForm.baseline_year }} 年基准排放量 {{ formatNumber(baselineEmission) }} t，
          目标减排 {{ targetForm.reduction_rate }}%，预计排放上限 {{ formatNumber(targetForm.target_value || computedTargetValue) }} t
        </a-alert>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import dayjs from 'dayjs'

interface EmissionFactor {
  id: number
  name: string
  category: string
  factor_value: number
  unit: string
  activity_data: number
  source_ref: string
  description: string
  effective_date: string
  updated_at: string
}

const categoryOptions = ['厂区电耗', '药剂消耗', '污泥处理', '燃料消耗', '交通运输', '其他']
const categoryColors: Record<string, string> = {
  '厂区电耗': 'arcoblue',
  '药剂消耗': 'green',
  '污泥处理': 'orangered',
  '燃料消耗': 'purple',
  '交通运输': 'red',
  '其他': 'gray'
}

const targetYear = ref(dayjs().year())
const yearOptions = computed(() => {
  const cur = dayjs().year()
  return [cur, cur + 1, cur + 2]
})
const baselineOptions = computed(() => {
  const cur = dayjs().year()
  return [cur - 1, cur - 2, cur - 3, cur - 4, cur - 5]
})

const searchKeyword = ref('')
const categoryFilter = ref('')
const hasFactorChanges = ref(false)

const originalFactors = ref<EmissionFactor[]>([])
const factorData = ref<EmissionFactor[]>([])

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const factorModalVisible = ref(false)
const editingFactor = ref<EmissionFactor | null>(null)
const factorFormRef = ref()
const factorForm = reactive<Partial<EmissionFactor>>({
  name: '',
  category: '',
  factor_value: 0,
  unit: '',
  activity_data: 0,
  source_ref: '',
  description: '',
  effective_date: dayjs().format('YYYY-MM-DD')
})

const targetModalVisible = ref(false)
const targetForm = reactive({
  year: dayjs().year(),
  target_value: 0,
  baseline_year: dayjs().year() - 1,
  reduction_rate: 5
})

const baselineEmission = ref(2050.8)

const computedTargetValue = computed(() => {
  const base = baselineEmission.value
  const rate = targetForm.reduction_rate || 0
  return base * (1 - rate / 100)
})

const filteredFactors = computed(() => {
  let list = factorData.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(f =>
      f.name.toLowerCase().includes(kw) ||
      f.category.includes(searchKeyword.value) ||
      f.description?.toLowerCase().includes(kw)
    )
  }
  if (categoryFilter.value) {
    list = list.filter(f => f.category === categoryFilter.value)
  }
  pagination.total = list.length
  const start = (pagination.current - 1) * pagination.pageSize
  return list.slice(start, start + pagination.pageSize)
})

const currentTotalEmission = computed(() => {
  return originalFactors.value.reduce((sum, f) => sum + (f.factor_value * (f.activity_data || 0) / 1000), 0)
})

const previewTotalEmission = computed(() => {
  return factorData.value.reduce((sum, f) => sum + (f.factor_value * (f.activity_data || 0) / 1000), 0)
})

const previewDiff = computed(() => {
  return Number((previewTotalEmission.value - currentTotalEmission.value).toFixed(4))
})

const previewDiffPercent = computed(() => {
  if (currentTotalEmission.value === 0) return 0
  return Number((previewDiff.value / currentTotalEmission.value * 100).toFixed(2))
})

const factorColumns = [
  { title: '序号', dataIndex: 'index', width: 60, render: (_: any, __: any, index: number) => (pagination.current - 1) * pagination.pageSize + index + 1 },
  { title: '因子名称', dataIndex: 'name', width: 160 },
  { title: '分类', slotName: 'category', width: 110 },
  { title: '排放因子值', slotName: 'factor_value', width: 170 },
  { title: '单位', slotName: 'unit', width: 140 },
  { title: '参考年活动量', dataIndex: 'activity_data', width: 130, align: 'right' as const },
  { title: '数据来源', slotName: 'source_ref', width: 180, ellipsis: true },
  { title: '更新时间', dataIndex: 'updated_at', width: 110 },
  { title: '操作', slotName: 'action', width: 120, fixed: 'right' as const }
]

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(2) + '万'
  return n.toFixed(2)
}

function getStep(v: number): number {
  if (v < 0.01) return 0.0001
  if (v < 1) return 0.001
  if (v < 10) return 0.01
  return 0.1
}

function getPrecision(v: number): number {
  if (v < 0.01) return 6
  if (v < 1) return 4
  if (v < 10) return 3
  return 2
}

function loadMockFactors() {
  const mock: EmissionFactor[] = [
    { id: 1, name: '省级电网电力', category: '厂区电耗', factor_value: 0.6101, unit: 'kgCO₂e/kWh', activity_data: 286540, source_ref: '国家电网2024排放因子', description: '华东区域电网平均排放因子', effective_date: '2024-01-01', updated_at: '2024-06-01' },
    { id: 2, name: 'PAC药剂', category: '药剂消耗', factor_value: 2.1, unit: 'kgCO₂e/kg', activity_data: 4850, source_ref: 'IPCC AR6默认值', description: '聚合氯化铝生产与运输全生命周期', effective_date: '2024-01-01', updated_at: '2024-03-15' },
    { id: 3, name: 'PAM药剂', category: '药剂消耗', factor_value: 3.8, unit: 'kgCO₂e/kg', activity_data: 1260, source_ref: 'IPCC AR6默认值', description: '聚丙烯酰胺生产排放因子', effective_date: '2024-01-01', updated_at: '2024-03-15' },
    { id: 4, name: '污泥填埋运输', category: '污泥处理', factor_value: 0.096, unit: 'kgCO₂e/t·km', activity_data: 3120, source_ref: 'GB/T 32151.10-2018', description: '重型柴油车运输单位排放', effective_date: '2024-01-01', updated_at: '2024-04-20' },
    { id: 5, name: '污泥填埋CH₄', category: '污泥处理', factor_value: 0.25, unit: 'kgCO₂e/kg干污泥', activity_data: 860000, source_ref: 'IPCC 2019 Refinement', description: '污泥填埋甲烷排放折算', effective_date: '2024-01-01', updated_at: '2024-04-20' },
    { id: 6, name: '天然气燃烧', category: '燃料消耗', factor_value: 2.1622, unit: 'kgCO₂e/m³', activity_data: 18600, source_ref: 'GB/T 32151.1-2015', description: '天然气单位热值含碳量默认值', effective_date: '2024-01-01', updated_at: '2024-02-10' },
    { id: 7, name: '柴油燃烧', category: '燃料消耗', factor_value: 3.16, unit: 'kgCO₂e/L', activity_data: 5200, source_ref: 'GB/T 32151.1-2015', description: '柴油单位体积排放因子', effective_date: '2024-01-01', updated_at: '2024-02-10' },
    { id: 8, name: '汽油车运输', category: '交通运输', factor_value: 2.68, unit: 'kgCO₂e/L', activity_data: 15800, source_ref: 'GB/T 32151.5-2015', description: '公务车辆汽油消耗排放', effective_date: '2024-01-01', updated_at: '2024-05-05' },
    { id: 9, name: '外购蒸汽', category: '其他', factor_value: 0.11, unit: 'kgCO₂e/MJ', activity_data: 48000, source_ref: '区域供热锅炉平均', description: '外采蒸汽折算排放因子', effective_date: '2024-01-01', updated_at: '2024-01-20' }
  ]
  originalFactors.value = JSON.parse(JSON.stringify(mock))
  factorData.value = JSON.parse(JSON.stringify(mock))
}

function handleFactorChange(id: number, field: keyof EmissionFactor, value: any) {
  const f = factorData.value.find(x => x.id === id)
  if (f) {
    (f as any)[field] = value
    f.updated_at = dayjs().format('YYYY-MM-DD')
    hasFactorChanges.value = true
  }
}

function openFactorModal(record?: EmissionFactor) {
  if (record) {
    editingFactor.value = record
    Object.assign(factorForm, JSON.parse(JSON.stringify(record)))
  } else {
    editingFactor.value = null
    Object.assign(factorForm, {
      name: '',
      category: '',
      factor_value: 0,
      unit: '',
      activity_data: 0,
      source_ref: '',
      description: '',
      effective_date: dayjs().format('YYYY-MM-DD')
    })
  }
  factorModalVisible.value = true
}

function handleFactorSubmit() {
  if (!factorForm.name || !factorForm.category || factorForm.factor_value === undefined || !factorForm.unit) {
    Message.warning('请填写必填项')
    return
  }
  if (editingFactor.value) {
    const idx = factorData.value.findIndex(f => f.id === editingFactor.value!.id)
    if (idx > -1) {
      factorData.value[idx] = {
        ...factorData.value[idx],
        ...factorForm,
        updated_at: dayjs().format('YYYY-MM-DD')
      } as EmissionFactor
      hasFactorChanges.value = true
    }
  } else {
    const newId = Math.max(...factorData.value.map(f => f.id), 0) + 1
    factorData.value.unshift({
      id: newId,
      name: factorForm.name!,
      category: factorForm.category!,
      factor_value: factorForm.factor_value!,
      unit: factorForm.unit!,
      activity_data: factorForm.activity_data || 0,
      source_ref: factorForm.source_ref || '',
      description: factorForm.description || '',
      effective_date: factorForm.effective_date || dayjs().format('YYYY-MM-DD'),
      updated_at: dayjs().format('YYYY-MM-DD')
    })
    hasFactorChanges.value = true
  }
  factorModalVisible.value = false
  Message.success(editingFactor.value ? '因子已更新' : '因子已添加')
}

function handleDelete(record: EmissionFactor) {
  Modal.confirm({
    title: '确认删除',
    content: `确定删除排放因子「${record.name}」吗？此操作将影响后续核算结果。`,
    okText: '确认删除',
    cancelText: '取消',
    status: 'warning',
    onOk: () => {
      const idx = factorData.value.findIndex(f => f.id === record.id)
      if (idx > -1) {
        factorData.value.splice(idx, 1)
        hasFactorChanges.value = true
        Message.success('已删除')
      }
    }
  })
}

function applyChanges() {
  originalFactors.value = JSON.parse(JSON.stringify(factorData.value))
  hasFactorChanges.value = false
  Message.success('排放因子已保存，核算结果已即时重算')
}

function handleSearch() {
  pagination.current = 1
}

function handlePageChange(page: number) {
  pagination.current = page
}

function handleYearChange() {
  targetForm.year = targetYear.value
}

function openTargetModal() {
  targetForm.year = targetYear.value
  targetForm.target_value = 1900
  targetModalVisible.value = true
}

function handleTargetSubmit() {
  if (!targetForm.target_value) {
    targetForm.target_value = Number(computedTargetValue.value.toFixed(2))
  }
  targetModalVisible.value = false
  Message.success(`减排目标已更新：${targetForm.year}年 ${formatNumber(targetForm.target_value)} t CO₂e`)
}

watch([targetForm.reduction_rate, targetForm.baseline_year], () => {
  if (!targetForm.target_value || true) {
    targetForm.target_value = Number(computedTargetValue.value.toFixed(2))
  }
})

onMounted(() => {
  loadMockFactors()
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

.preview-row {
  margin-bottom: 16px;
}

.preview-card {
  border-radius: 10px;
  background: #fff;
}

.preview-card :deep(.arco-card-body) {
  padding: 20px 24px;
}

.preview-label {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 8px;
}

.preview-value {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.preview-value.current {
  color: #165DFF;
}

.preview-value.increase {
  color: '#F53F3F';
}

.preview-value.decrease {
  color: #00B42A;
}

.preview-unit {
  font-size: 14px;
  font-weight: 500;
  color: #86909c;
}

.unit-cell {
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 12px;
  color: #4e5969;
  background: #f7f8fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.ref-cell {
  font-size: 12px;
  color: #4e5969;
}
</style>
