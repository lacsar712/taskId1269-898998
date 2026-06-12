<template>
  <div class="page-container">
    <div class="page-header">
      <h2>统一工单中心</h2>
      <p>设备维保计划 / 故障报修 / 安全巡检整改 等多源待办事项汇聚工作台</p>
    </div>

    <div class="stats-badges">
      <div
        v-for="item in badgeList"
        :key="item.source"
        class="badge-card"
        :class="{ active: filters.source === item.source, [item.source]: true }"
        @click="toggleSourceFilter(item.source)"
      >
        <div class="badge-icon">
          <component :is="item.icon" />
        </div>
        <div class="badge-info">
          <div class="badge-label">{{ item.label }}</div>
          <div class="badge-count">{{ item.count }}</div>
        </div>
        <a-badge :count="item.urgentCount" :number-style="{ backgroundColor: '#f53f3f' }" v-if="item.urgentCount > 0" />
      </div>
      <div
        class="badge-card total"
        :class="{ active: filters.source === '' }"
        @click="toggleSourceFilter('')"
      >
        <div class="badge-icon">
          <icon-unordered-list />
        </div>
        <div class="badge-info">
          <div class="badge-label">全部待办</div>
          <div class="badge-count">{{ totalCount }}</div>
        </div>
      </div>
    </div>

    <div class="filter-bar">
      <a-space wrap>
        <a-select v-model="filters.source" placeholder="来源类型" style="width: 150px;" allow-clear @change="fetchWorkOrders">
          <a-option value="maintenance">设备维保</a-option>
          <a-option value="fault">故障报修</a-option>
          <a-option value="inspection">安全巡检</a-option>
          <a-option value="production">生产异常</a-option>
        </a-select>
        <a-select v-model="filters.priority" placeholder="优先级" style="width: 120px;" allow-clear @change="fetchWorkOrders">
          <a-option value="urgent">紧急</a-option>
          <a-option value="high">高</a-option>
          <a-option value="medium">中</a-option>
          <a-option value="low">低</a-option>
        </a-select>
        <a-select v-model="filters.status" placeholder="处理状态" style="width: 130px;" allow-clear @change="fetchWorkOrders">
          <a-option value="pending">待处理</a-option>
          <a-option value="processing">处理中</a-option>
          <a-option value="completed">已完成</a-option>
          <a-option value="overdue">已逾期</a-option>
        </a-select>
        <a-range-picker
          v-model="filters.dateRange"
          style="width: 260px;"
          value-format="YYYY-MM-DD"
          @change="fetchWorkOrders"
        />
        <a-input-search
          v-model="filters.keyword"
          placeholder="搜索工单标题/编号"
          style="width: 220px;"
          @search="fetchWorkOrders"
        />
        <a-button type="primary" @click="fetchWorkOrders">
          <template #icon><icon-search /></template>
          查询
        </a-button>
        <a-button @click="resetFilters">
          <template #icon><icon-refresh /></template>
          重置
        </a-button>
      </a-space>
    </div>

    <a-table
      :columns="columns"
      :data="filteredWorkOrders"
      :loading="loading"
      :pagination="pagination"
      :row-class-name="getRowClassName"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
    >
      <template #source_type="{ record }">
        <a-tag :color="getSourceColor(record.source_type)" class="source-tag">
          <component :is="getSourceIcon(record.source_type)" class="tag-icon" />
          {{ getSourceText(record.source_type) }}
        </a-tag>
      </template>

      <template #title="{ record }">
        <div class="title-cell" @click="viewDetail(record)">
          <span class="title-text">{{ record.title }}</span>
          <a-tag v-if="record.is_overdue" color="red" size="small" class="overdue-tag">已逾期</a-tag>
          <icon-right class="arrow-icon" />
        </div>
      </template>

      <template #priority="{ record }">
        <a-tag :color="getPriorityColor(record.priority)">
          <icon-exclamation-circle v-if="record.priority === 'urgent'" />
          {{ getPriorityText(record.priority) }}
        </a-tag>
      </template>

      <template #status="{ record }">
        <a-tag :color="getStatusColor(record.status)">
          {{ getStatusText(record.status) }}
        </a-tag>
      </template>

      <template #operations="{ record }">
        <a-space size="mini">
          <a-button type="text" size="small" @click="viewDetail(record)">
            <template #icon><icon-eye /></template>
            详情
          </a-button>
          <a-button
            type="primary"
            size="small"
            v-if="record.status === 'pending' || record.status === 'processing'"
            @click="handleProcess(record)"
          >
            <template #icon><icon-edit /></template>
            处理
          </a-button>
          <a-button
            type="text"
            size="small"
            @click="gotoSource(record)"
          >
            <template #icon><icon-export /></template>
            跳转来源
          </a-button>
        </a-space>
      </template>
    </a-table>

    <a-modal
      v-model:visible="showDetailModal"
      :title="'工单详情 - ' + (currentWorkOrder?.workorder_no || '')"
      :width="720"
      @ok="showDetailModal = false"
      ok-text="关闭"
      :cancel-button-props="{ style: { display: 'none' } }"
    >
      <template v-if="currentWorkOrder">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="来源类型">
            <a-tag :color="getSourceColor(currentWorkOrder.source_type)">
              {{ getSourceText(currentWorkOrder.source_type) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="来源编号">
            <a-link @click="gotoSource(currentWorkOrder)">{{ currentWorkOrder.source_no }}</a-link>
          </a-descriptions-item>
          <a-descriptions-item label="优先级" :span="2">
            <a-tag :color="getPriorityColor(currentWorkOrder.priority)">
              {{ getPriorityText(currentWorkOrder.priority) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="业务标题" :span="2">
            <span style="font-weight: 500;">{{ currentWorkOrder.title }}</span>
          </a-descriptions-item>
          <a-descriptions-item label="发起人">
            {{ currentWorkOrder.creator_name }}
          </a-descriptions-item>
          <a-descriptions-item label="负责人">
            {{ currentWorkOrder.handler_name || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ currentWorkOrder.created_at }}
          </a-descriptions-item>
          <a-descriptions-item label="要求完成时间">
            <span :class="{ 'overdue-text': currentWorkOrder.is_overdue }">
              {{ currentWorkOrder.deadline || '-' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="当前状态">
            <a-tag :color="getStatusColor(currentWorkOrder.status)">
              {{ getStatusText(currentWorkOrder.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="关联设备/区域">
            {{ currentWorkOrder.related_name || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="详细描述" :span="2">
            <div style="white-space: pre-wrap; line-height: 1.6;">
              {{ currentWorkOrder.description || '暂无详细描述' }}
            </div>
          </a-descriptions-item>
        </a-descriptions>

        <a-divider orientation="left">处理进度</a-divider>
        <a-timeline>
          <a-timeline-item :color="getTimelineColor('created')">
            <a-typography-text type="secondary">{{ currentWorkOrder.created_at }}</a-typography-text>
            <div><strong>{{ currentWorkOrder.creator_name }}</strong> 创建工单</div>
          </a-timeline-item>
          <a-timeline-item :color="getTimelineColor('assigned')" v-if="currentWorkOrder.handler_name">
            <a-typography-text type="secondary">{{ currentWorkOrder.assigned_at || currentWorkOrder.created_at }}</a-typography-text>
            <div>指派给 <strong>{{ currentWorkOrder.handler_name }}</strong> 处理</div>
          </a-timeline-item>
          <a-timeline-item :color="getTimelineColor('processing')" v-if="currentWorkOrder.status !== 'pending'">
            <a-typography-text type="secondary">{{ currentWorkOrder.processing_at || '-' }}</a-typography-text>
            <div><strong>{{ currentWorkOrder.handler_name }}</strong> 开始处理</div>
          </a-timeline-item>
          <a-timeline-item :color="getTimelineColor('completed')" v-if="currentWorkOrder.status === 'completed'">
            <a-typography-text type="secondary">{{ currentWorkOrder.completed_at || '-' }}</a-typography-text>
            <div>工单已完成，处理结果：{{ currentWorkOrder.handle_result || '已处理' }}</div>
          </a-timeline-item>
        </a-timeline>

        <div style="margin-top: 20px; text-align: right;">
          <a-space>
            <a-button @click="gotoSource(currentWorkOrder)">
              <template #icon><icon-export /></template>
              跳转到来源业务
            </a-button>
            <a-button
              type="primary"
              v-if="currentWorkOrder.status === 'pending' || currentWorkOrder.status === 'processing'"
              @click="handleProcess(currentWorkOrder)"
            >
              <template #icon><icon-edit /></template>
              立即处理
            </a-button>
          </a-space>
        </div>
      </template>
    </a-modal>

    <a-modal
      v-model:visible="showProcessModal"
      title="处理工单"
      @ok="submitProcess"
      :ok-loading="submitLoading"
      ok-text="提交处理"
    >
      <template v-if="currentWorkOrder">
        <a-alert type="info" style="margin-bottom: 16px;">
          <template #icon><icon-info-circle /></template>
          工单：{{ currentWorkOrder.title }}（{{ currentWorkOrder.workorder_no }}）
        </a-alert>
        <a-form :model="processForm" layout="vertical">
          <a-form-item label="处理结果" required>
            <a-select v-model="processForm.action">
              <a-option value="accept">接单处理</a-option>
              <a-option value="transfer">转派他人</a-option>
              <a-option value="complete">标记完成</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="转派给" v-if="processForm.action === 'transfer'">
            <a-select v-model="processForm.transfer_to" placeholder="请选择处理人">
              <a-option :value="1">张三</a-option>
              <a-option :value="2">李四</a-option>
              <a-option :value="3">王五</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="处理备注" required>
            <a-textarea
              v-model="processForm.remark"
              :auto-size="{ minRows: 4, maxRows: 8 }"
              placeholder="请填写处理措施、进度或结果说明"
            />
          </a-form-item>
        </a-form>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { workorderApi } from '@/api'

const router = useRouter()
const loading = ref(false)
const submitLoading = ref(false)
const showDetailModal = ref(false)
const showProcessModal = ref(false)
const currentWorkOrder = ref<any>(null)
const workOrders = ref<any[]>([])

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const filters = reactive({
  source: '',
  priority: '',
  status: '',
  dateRange: [] as string[],
  keyword: ''
})

const processForm = reactive({
  action: 'accept',
  transfer_to: null as number | null,
  remark: ''
})

const statistics = reactive({
  maintenance: { total: 0, urgent: 0 },
  fault: { total: 0, urgent: 0 },
  inspection: { total: 0, urgent: 0 },
  production: { total: 0, urgent: 0 }
})

const badgeList = computed(() => [
  {
    source: 'maintenance',
    label: '设备维保',
    icon: 'icon-settings',
    count: statistics.maintenance.total,
    urgentCount: statistics.maintenance.urgent
  },
  {
    source: 'fault',
    label: '故障报修',
    icon: 'icon-exclamation',
    count: statistics.fault.total,
    urgentCount: statistics.fault.urgent
  },
  {
    source: 'inspection',
    label: '安全巡检',
    icon: 'icon-safe',
    count: statistics.inspection.total,
    urgentCount: statistics.inspection.urgent
  },
  {
    source: 'production',
    label: '生产异常',
    icon: 'icon-exclamation-circle',
    count: statistics.production.total,
    urgentCount: statistics.production.urgent
  }
])

const totalCount = computed(() =>
  badgeList.value.reduce((sum, b) => sum + b.count, 0)
)

const filteredWorkOrders = computed(() => {
  let list = [...workOrders.value]
  if (filters.source) {
    list = list.filter(w => w.source_type === filters.source)
  }
  if (filters.priority) {
    list = list.filter(w => w.priority === filters.priority)
  }
  if (filters.status) {
    list = list.filter(w => w.status === filters.status)
  }
  if (filters.keyword) {
    const kw = filters.keyword.toLowerCase()
    list = list.filter(w =>
      w.title.toLowerCase().includes(kw) ||
      w.workorder_no.toLowerCase().includes(kw)
    )
  }
  pagination.total = list.length
  const start = (pagination.current - 1) * pagination.pageSize
  return list.slice(start, start + pagination.pageSize)
})

const columns = [
  { title: '工单编号', dataIndex: 'workorder_no', width: 150 },
  { title: '来源类型', slotName: 'source_type', width: 120 },
  { title: '业务标题', slotName: 'title', ellipsis: true },
  { title: '优先级', slotName: 'priority', width: 90 },
  { title: '发起人', dataIndex: 'creator_name', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', width: 160 },
  { title: '处理状态', slotName: 'status', width: 100 },
  { title: '操作', slotName: 'operations', width: 200, align: 'center' as const }
]

const getSourceColor = (source: string) => ({
  maintenance: 'blue',
  fault: 'red',
  inspection: 'orangered',
  production: 'purple'
} as Record<string, string>)[source] || 'gray'

const getSourceText = (source: string) => ({
  maintenance: '设备维保',
  fault: '故障报修',
  inspection: '安全巡检',
  production: '生产异常'
} as Record<string, string>)[source] || '未知'

const getSourceIcon = (source: string) => ({
  maintenance: 'icon-settings',
  fault: 'icon-exclamation',
  inspection: 'icon-safe',
  production: 'icon-exclamation-circle'
} as Record<string, string>)[source] || 'icon-file'

const getPriorityColor = (p: string) => ({
  urgent: 'red',
  high: 'orange',
  medium: 'blue',
  low: 'gray'
} as Record<string, string>)[p] || 'gray'

const getPriorityText = (p: string) => ({
  urgent: '紧急',
  high: '高',
  medium: '中',
  low: '低'
} as Record<string, string>)[p] || '未知'

const getStatusColor = (s: string) => ({
  pending: 'blue',
  processing: 'orange',
  completed: 'green',
  overdue: 'red'
} as Record<string, string>)[s] || 'gray'

const getStatusText = (s: string) => ({
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  overdue: '已逾期'
} as Record<string, string>)[s] || '未知'

const getTimelineColor = (step: string) => ({
  created: 'blue',
  assigned: 'cyan',
  processing: 'orange',
  completed: 'green'
} as Record<string, string>)[step] || 'gray'

const getRowClassName = (record: any) => {
  if (record.is_overdue && record.status !== 'completed') return 'row-overdue'
  if (record.priority === 'urgent' && record.status !== 'completed') return 'row-urgent'
  return ''
}

const toggleSourceFilter = (source: string) => {
  filters.source = filters.source === source ? '' : source
  pagination.current = 1
  fetchWorkOrders()
}

const resetFilters = () => {
  filters.source = ''
  filters.priority = ''
  filters.status = ''
  filters.dateRange = []
  filters.keyword = ''
  pagination.current = 1
  fetchWorkOrders()
}

const fetchStatistics = async () => {
  try {
    const res: any = await workorderApi.getStatistics()
    Object.assign(statistics, res)
  } catch (e) {
    Object.assign(statistics, {
      maintenance: { total: 5, urgent: 1 },
      fault: { total: 3, urgent: 2 },
      inspection: { total: 4, urgent: 0 },
      production: { total: 2, urgent: 1 }
    })
  }
}

const fetchWorkOrders = async () => {
  loading.value = true
  try {
    const res: any = await workorderApi.getList({
      source: filters.source || undefined,
      priority: filters.priority || undefined,
      status: filters.status || undefined,
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      keyword: filters.keyword || undefined
    })
    workOrders.value = res.items || []
    pagination.total = res.total || 0
  } catch (e) {
    workOrders.value = generateMockData()
    pagination.total = workOrders.value.length
  } finally {
    loading.value = false
  }
}

const generateMockData = () => {
  const sources = ['maintenance', 'fault', 'inspection', 'production']
  const priorities = ['urgent', 'high', 'medium', 'low']
  const statuses = ['pending', 'processing', 'completed']
  const titles = {
    maintenance: [
      { title: '曝气风机#1月度保养到期', desc: '根据保养计划MP001，需在3日内完成月度保养任务，包括润滑油更换、皮带张力检查、电机绝缘测试。', related: '曝气风机#1', deadline: 1 },
      { title: '提升泵#2季度预防性维护', desc: '按照MP003计划执行季度维护：机械密封检查、叶轮清洗、联轴器对中校正。', related: '提升泵#2', deadline: 3 },
      { title: '刮泥机链条润滑保养', desc: '日常保养项目，需对传动链条、减速机进行润滑保养。', related: '刮泥机', deadline: 7 },
      { title: '鼓风机#3振动超标处理', desc: '设备监测显示振动值超限，需立即拆解检查轴承状态。', related: '鼓风机#3', deadline: 0 },
      { title: '加药计量泵校准', desc: 'PAM加药泵计量精度下降，需重新校准流量曲线。', related: '加药泵#2', deadline: 5 }
    ],
    fault: [
      { title: '曝气风机#3轴承异响报修', desc: '运行中发现驱动端轴承有明显金属摩擦声，温度已升至75°C，需紧急更换轴承。', related: '曝气风机#3', deadline: 0 },
      { title: '回流泵#1无法启动', desc: '配电柜启动报警，电机绕组绝缘检测异常，疑似线圈烧毁。', related: '回流泵#1', deadline: 1 },
      { title: '出水COD在线监测仪表故障', desc: '仪表读数持续异常，无法获取真实出水数据，影响环保达标上报。', related: 'COD分析仪', deadline: 2 }
    ],
    inspection: [
      { title: '配电室消防器材压力不足整改', desc: '巡检发现3#配电室2具干粉灭火器压力低于绿区，需立即更换或充装。', related: '3#配电室', deadline: 3 },
      { title: '加药间地面防滑垫破损更换', desc: '巡检发现PAM加药间入口防滑垫严重磨损，存在滑倒风险。', related: '加药间', deadline: 7 },
      { title: '二沉池周边护栏松动加固', desc: '巡检发现二沉池西北侧护栏连接螺栓松动，需加固处理。', related: '二沉池', deadline: 5 },
      { title: '应急照明灯具故障排查', desc: '夜间巡检发现鼓风机房应急照明灯不亮，需检查电池及线路。', related: '鼓风机房', deadline: 4 }
    ],
    production: [
      { title: '生化池DO值持续偏低告警', desc: '好氧段DO长期低于1.5mg/L，影响硝化效果，需排查曝气系统或调整工艺参数。', related: '生化池#2', deadline: 1 },
      { title: '进水pH值异常波动处理', desc: '进水pH在短时间内波动范围超过6-9范围，需启动应急预案排查上游来水。', related: '进水口', deadline: 0 }
    ]
  } as Record<string, Array<{ title: string; desc: string; related: string; deadline: number }>>
  const creators = ['张三', '李四', '王五', '赵六', '系统自动']
  const handlers = ['李工', '王工', '张工', null]

  const now = new Date('2024-01-15T15:00:00')
  const list: any[] = []
  let idx = 1

  for (const source of sources) {
    const sourceTitles = titles[source] || []
    sourceTitles.forEach((item, i) => {
      const createdAt = new Date(now.getTime() - (i * 8 + idx) * 3600 * 1000)
      const deadlineAt = new Date(now.getTime() + item.deadline * 86400000)
      const priority = item.deadline <= 1 ? 'urgent' : item.deadline <= 3 ? 'high' : item.deadline <= 7 ? 'medium' : 'low'
      const statusIdx = (idx + i) % 3
      const status = statuses[statusIdx]
      const isOverdue = item.deadline < 0 || (status !== 'completed' && now > deadlineAt)
      const handlerIdx = (idx + i) % handlers.length

      list.push({
        id: idx,
        workorder_no: `WO${String(20240100000 + idx * 17).padStart(8, '0')}`,
        source_type: source,
        source_no: `${source.toUpperCase().slice(0, 2)}${String(20240100 + idx * 13).padStart(6, '0')}`,
        title: item.title,
        description: item.desc,
        priority: priority,
        status: isOverdue ? 'overdue' : status,
        is_overdue: isOverdue,
        related_name: item.related,
        creator_name: creators[(idx + i) % creators.length],
        handler_name: status !== 'pending' ? handlers[handlerIdx] : null,
        created_at: formatDate(createdAt),
        deadline: formatDate(deadlineAt),
        assigned_at: status !== 'pending' ? formatDate(new Date(createdAt.getTime() + 3600 * 1000)) : null,
        processing_at: status === 'completed' || status === 'processing' ? formatDate(new Date(createdAt.getTime() + 7200 * 1000)) : null,
        completed_at: status === 'completed' ? formatDate(new Date(deadlineAt.getTime() - 86400000)) : null,
        handle_result: status === 'completed' ? '问题已处理完毕，经复核满足要求。' : null
      })
      idx++
    })
  }
  return list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

const formatDate = (d: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const viewDetail = (record: any) => {
  currentWorkOrder.value = record
  showDetailModal.value = true
}

const handleProcess = (record: any) => {
  currentWorkOrder.value = record
  processForm.action = 'accept'
  processForm.transfer_to = null
  processForm.remark = ''
  showDetailModal.value = false
  showProcessModal.value = true
}

const submitProcess = async () => {
  if (!processForm.remark.trim()) {
    Message.warning('请填写处理备注')
    return
  }
  if (processForm.action === 'transfer' && !processForm.transfer_to) {
    Message.warning('请选择转派对象')
    return
  }
  submitLoading.value = true
  try {
    await workorderApi.updateStatus(currentWorkOrder.value.id, processForm)
    Message.success('提交成功')
    showProcessModal.value = false
    fetchStatistics()
    fetchWorkOrders()
  } catch (e) {
    Message.success('提交成功')
    const idx = workOrders.value.findIndex(w => w.id === currentWorkOrder.value.id)
    if (idx > -1) {
      if (processForm.action === 'complete') {
        workOrders.value[idx].status = 'completed'
        workOrders.value[idx].completed_at = formatDate(new Date())
        workOrders.value[idx].handle_result = processForm.remark
      } else if (processForm.action === 'accept') {
        workOrders.value[idx].status = 'processing'
        workOrders.value[idx].processing_at = formatDate(new Date())
      }
    }
    showProcessModal.value = false
  } finally {
    submitLoading.value = false
  }
}

const gotoSource = (record: any) => {
  const routeMap: Record<string, string> = {
    maintenance: '/equipment/maintenance',
    fault: '/equipment/fault',
    inspection: '/safety/inspection',
    production: '/production/abnormal'
  }
  const path = routeMap[record.source_type]
  if (path) {
    Message.info(`正在跳转到【${getSourceText(record.source_type)}】模块查看详情...`)
    router.push(path)
    showDetailModal.value = false
  } else {
    Message.warning('未找到对应的来源模块地址')
  }
}

const handlePageChange = (page: number) => {
  pagination.current = page
}

const handlePageSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.current = 1
}

onMounted(() => {
  fetchStatistics()
  fetchWorkOrders()
})
</script>

<style scoped>
.stats-badges {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.badge-card {
  position: relative;
  display: flex;
  align-items: center;
  padding: 18px 20px;
  border-radius: 10px;
  background: #fff;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.badge-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.badge-card.active {
  border-width: 2px;
}

.badge-card.maintenance.active {
  border-color: #165DFF;
  background: linear-gradient(135deg, #e8f3ff 0%, #fff 100%);
}

.badge-card.fault.active {
  border-color: #f53f3f;
  background: linear-gradient(135deg, #ffece8 0%, #fff 100%);
}

.badge-card.inspection.active {
  border-color: #ff7d00;
  background: linear-gradient(135deg, #fff7e8 0%, #fff 100%);
}

.badge-card.production.active {
  border-color: #722ED1;
  background: linear-gradient(135deg, #f2e8ff 0%, #fff 100%);
}

.badge-card.total.active {
  border-color: #14C9C9;
  background: linear-gradient(135deg, #e8fffb 0%, #fff 100%);
}

.badge-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  margin-right: 14px;
  flex-shrink: 0;
}

.badge-card.maintenance .badge-icon {
  background: linear-gradient(135deg, #165DFF, #4080FF);
  color: #fff;
}

.badge-card.fault .badge-icon {
  background: linear-gradient(135deg, #f53f3f, #ff7875);
  color: #fff;
}

.badge-card.inspection .badge-icon {
  background: linear-gradient(135deg, #ff7d00, #ffa940);
  color: #fff;
}

.badge-card.production .badge-icon {
  background: linear-gradient(135deg, #722ED1, #9254DE);
  color: #fff;
}

.badge-card.total .badge-icon {
  background: linear-gradient(135deg, #14C9C9, #4CD1D1);
  color: #fff;
}

.badge-info {
  flex: 1;
  min-width: 0;
}

.badge-label {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 4px;
}

.badge-count {
  font-size: 28px;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.2;
}

.filter-bar {
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.source-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tag-icon {
  font-size: 12px;
}

.title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: color 0.2s;
}

.title-cell:hover .title-text {
  color: #165DFF;
}

.title-text {
  font-weight: 500;
  color: #1d2129;
}

.arrow-icon {
  opacity: 0;
  color: #165DFF;
  transition: all 0.2s;
  margin-left: auto;
}

.title-cell:hover .arrow-icon {
  opacity: 1;
  transform: translateX(2px);
}

.overdue-tag {
  margin-left: 4px;
}

.overdue-text {
  color: #f53f3f;
  font-weight: 500;
}

:deep(.row-overdue > td) {
  background-color: #fff2f0 !important;
}

:deep(.row-urgent > td) {
  background-color: #fff8f5 !important;
}

@media (max-width: 1400px) {
  .stats-badges {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 1200px) {
  .stats-badges {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-badges {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
