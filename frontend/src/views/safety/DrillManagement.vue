<template>
  <div class="drill-container">
    <div class="page-header">
      <div>
        <h2>应急演练签到</h2>
        <p>演练管理 / 签到统计 / 记录归档</p>
      </div>
    </div>

    <a-row :gutter="16" style="margin-bottom: 16px;">
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon icon-blue"><icon-file /></div>
            <div>
              <div class="stat-value">{{ stats.total_drills || 0 }}</div>
              <div class="stat-label">演练总数</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon icon-green"><icon-play-circle /></div>
            <div>
              <div class="stat-value">{{ stats.ongoing_drills || 0 }}</div>
              <div class="stat-label">进行中</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon icon-orange"><icon-check-circle /></div>
            <div>
              <div class="stat-value">{{ stats.total_check_ins || 0 }}</div>
              <div class="stat-label">累计签到人次</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon icon-purple"><icon-calendar /></div>
            <div>
              <div class="stat-value">{{ stats.today_check_ins || 0 }}</div>
              <div class="stat-label">今日签到</div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-card v-if="!currentDetail" class="list-card">
      <div class="toolbar">
        <a-space :size="12">
          <a-input-search
            v-model="searchKeyword"
            placeholder="搜索演练名称/编号"
            style="width: 260px;"
            @search="fetchDrills"
            allow-clear
          />
          <a-select v-model="filterStatus" placeholder="状态筛选" style="width: 140px;" allow-clear @change="fetchDrills">
            <a-option value="draft">草稿</a-option>
            <a-option value="ongoing">进行中</a-option>
            <a-option value="ended">已结束</a-option>
          </a-select>
        </a-space>
        <a-button type="primary" @click="openCreateModal">
          <template #icon><icon-plus /></template>
          新建演练
        </a-button>
      </div>

      <a-table :data="drillList" :loading="listLoading" :pagination="pagination" @page-change="handlePageChange" @page-size-change="handlePageSizeChange">
        <template #columns>
          <a-table-column title="演练编号" data-index="drill_no" width="170" />
          <a-table-column title="演练名称" data-index="drill_name" ellipsis />
          <a-table-column title="类型" data-index="drill_type" width="110" />
          <a-table-column title="地点" data-index="location" width="160" ellipsis />
          <a-table-column title="演练时间" width="280">
            <template #cell="{ record }">
              <div class="time-text">{{ formatDateTime(record.start_time) }}</div>
              <div class="time-sub">至 {{ formatDateTime(record.end_time) }}</div>
            </template>
          </a-table-column>
          <a-table-column title="组织人" data-index="organizer_name" width="100" />
          <a-table-column title="状态" width="100">
            <template #cell="{ record }">
              <a-tag :color="getStatusColor(record.status)">{{ getStatusText(record.status) }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="操作" width="260" fixed="right">
            <template #cell="{ record }">
              <a-space :size="4">
                <a-button type="text" size="small" @click="viewDetail(record)">详情</a-button>
                <a-button v-if="record.status === 'draft'" type="text" size="small" @click="editDrill(record)">编辑</a-button>
                <a-button v-if="record.status === 'draft'" type="text" size="small" status="success" @click="handleStart(record)">开始</a-button>
                <a-button v-if="record.status === 'ongoing'" type="text" size="small" status="warning" @click="handleEnd(record)">结束</a-button>
                <a-popconfirm content="确认删除此演练？" position="br" @ok="handleDelete(record)">
                  <a-button type="text" size="small" status="danger">删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <a-card v-else class="detail-card">
      <div class="detail-header">
        <a-button type="text" @click="backToList" style="padding: 4px 8px;">
          <template #icon><icon-arrow-left /></template>
          返回列表
        </a-button>
        <div class="detail-actions">
          <a-space>
            <a-button v-if="currentDetail.status === 'draft'" @click="editDrill(currentDetail)">
              <template #icon><icon-edit /></template>
              编辑
            </a-button>
            <a-button v-if="currentDetail.status === 'draft'" type="primary" status="success" @click="handleStart(currentDetail)">
              <template #icon><icon-play-circle /></template>
              开始演练
            </a-button>
            <a-button v-if="currentDetail.status === 'ongoing'" type="primary" status="warning" @click="handleEnd(currentDetail)">
              <template #icon><icon-stop /></template>
              结束演练
            </a-button>
            <a-button @click="handleExport">
              <template #icon><icon-download /></template>
              导出记录
            </a-button>
          </a-space>
        </div>
      </div>

      <a-descriptions :column="2" bordered style="margin-bottom: 20px;">
        <a-descriptions-item label="演练编号">{{ currentDetail.drill_no }}</a-descriptions-item>
        <a-descriptions-item label="演练名称">{{ currentDetail.drill_name }}</a-descriptions-item>
        <a-descriptions-item label="演练类型">{{ currentDetail.drill_type || '-' }}</a-descriptions-item>
        <a-descriptions-item label="演练地点">{{ currentDetail.location || '-' }}</a-descriptions-item>
        <a-descriptions-item label="开始时间">{{ formatDateTime(currentDetail.start_time) }}</a-descriptions-item>
        <a-descriptions-item label="结束时间">{{ formatDateTime(currentDetail.end_time) }}</a-descriptions-item>
        <a-descriptions-item label="组织人">{{ currentDetail.organizer_name || '-' }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="getStatusColor(currentDetail.status)">{{ getStatusText(currentDetail.status) }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="演练描述" :span="2">{{ currentDetail.description || '暂无描述' }}</a-descriptions-item>
      </a-descriptions>

      <a-row :gutter="16" style="margin-bottom: 20px;">
        <a-col :span="8">
          <a-card class="sub-stat" :bordered="false" style="background: linear-gradient(135deg, #e6f7ff 0%, #f0f5ff 100%);">
            <div class="sub-stat-num">{{ currentDetail.expected_count || 0 }}</div>
            <div class="sub-stat-label">预期参与人数</div>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card class="sub-stat" :bordered="false" style="background: linear-gradient(135deg, #f6ffed 0%, #f0fff4 100%);">
            <div class="sub-stat-num" style="color: #52c41a;">{{ currentDetail.check_in_count || 0 }}</div>
            <div class="sub-stat-label">已签到人数</div>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card class="sub-stat" :bordered="false" style="background: linear-gradient(135deg, #fff7e6 0%, #fffbe6 100%);">
            <div class="sub-stat-num" style="color: #fa8c16;">{{ currentDetail.attendance_rate || 0 }}%</div>
            <div class="sub-stat-label">到场率</div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="16">
        <a-col :span="10">
          <a-card title="签到入口" class="code-card">
            <template #extra>
              <a-button v-if="currentDetail.status === 'ongoing'" size="small" @click="refreshCode">
                <template #icon><icon-refresh /></template>
                刷新
              </a-button>
            </template>
            <div class="code-display">
              <div class="code-label">签到码</div>
              <div class="code-value">{{ currentDetail.check_in_code || '------' }}</div>
            </div>
            <a-divider />
            <div class="link-display">
              <div class="code-label">签到链接</div>
              <div class="link-row">
                <a-input v-model="checkInLink" readonly style="flex: 1;" />
                <a-button @click="copyLink">
                  <template #icon><icon-copy /></template>
                  复制
                </a-button>
              </div>
              <div class="link-hint">将链接发送给参演人员，或生成二维码供扫描使用</div>
            </div>
          </a-card>

          <a-card title="预期参与班组" style="margin-top: 16px;">
            <a-table :data="teamStats" :bordered="false" size="small" :pagination="false">
              <template #columns>
                <a-table-column title="班组" data-index="team_name" />
                <a-table-column title="预期人数" data-index="expected_count" width="80" align="center" />
                <a-table-column title="实际签到" data-index="actual_count" width="80" align="center">
                  <template #cell="{ record }">
                    <span :style="{ color: record.actual_count >= record.expected_count ? '#52c41a' : '#f5222d' }">{{ record.actual_count }}</span>
                  </template>
                </a-table-column>
                <a-table-column title="到场率" width="90" align="center">
                  <template #cell="{ record }">
                    {{ record.expected_count ? Math.round(record.actual_count / record.expected_count * 100) : 0 }}%
                  </template>
                </a-table-column>
              </template>
            </a-table>
          </a-card>
        </a-col>

        <a-col :span="14">
          <a-card title="签到名单">
            <div class="toolbar toolbar-small">
              <a-input-search v-model="checkInKeyword" placeholder="搜索姓名" style="width: 200px;" allow-clear />
            </div>
            <a-table :data="filteredCheckIns" :pagination="checkInPagination" @page-change="(p) => checkInPagination.current = p" size="small">
              <template #columns>
                <a-table-column title="序号" type="index" width="60" />
                <a-table-column title="姓名" data-index="participant_name" width="120" />
                <a-table-column title="班组" data-index="team_name" width="130" />
                <a-table-column title="签到时间" width="170">
                  <template #cell="{ record }">{{ formatDateTime(record.check_in_time) }}</template>
                </a-table-column>
                <a-table-column title="签到方式" width="100">
                  <template #cell="{ record }">
                    <a-tag :color="record.check_in_type === 'code' ? 'blue' : 'green'">
                      {{ record.check_in_type === 'code' ? '签到码' : '链接' }}
                    </a-tag>
                  </template>
                </a-table-column>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </a-card>

    <a-modal
      v-model:visible="createVisible"
      :title="editingDrill ? '编辑演练' : '新建演练'"
      :width="680"
      @ok="handleSubmitDrill"
      ok-text="保存"
      cancel-text="取消"
    >
      <a-form ref="formRef" :model="formData" layout="vertical">
        <a-form-item label="演练名称" field="drill_name" :rules="[{ required: true, message: '请输入演练名称' }]">
          <a-input v-model="formData.drill_name" placeholder="请输入演练名称" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="演练类型" field="drill_type">
              <a-select v-model="formData.drill_type" placeholder="请选择演练类型" allow-clear>
                <a-option value="消防演练">消防演练</a-option>
                <a-option value="泄漏演练">泄漏演练</a-option>
                <a-option value="停电演练">停电演练</a-option>
                <a-option value="防汛演练">防汛演练</a-option>
                <a-option value="地震演练">地震演练</a-option>
                <a-option value="其他">其他</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="演练地点" field="location">
              <a-input v-model="formData.location" placeholder="请输入演练地点" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="开始时间" field="start_time" :rules="[{ required: true, message: '请选择开始时间' }]">
              <a-date-picker v-model="formData.start_time" show-time format="YYYY-MM-DD HH:mm" style="width: 100%;" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束时间" field="end_time" :rules="[{ required: true, message: '请选择结束时间' }]">
              <a-date-picker v-model="formData.end_time" show-time format="YYYY-MM-DD HH:mm" style="width: 100%;" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="预期参与班组">
          <a-table :data="formData.expected_teams" :bordered="true" size="small" :pagination="false">
            <template #columns>
              <a-table-column title="班组名称" width="180">
                <template #cell="{ rowIndex, record }">
                  <a-input v-model="record.team_name" placeholder="如：运行甲班" />
                </template>
              </a-table-column>
              <a-table-column title="预期人数" width="160">
                <template #cell="{ record }">
                  <a-input-number v-model="record.expected_count" :min="0" :max="999" style="width: 100%;" />
                </template>
              </a-table-column>
              <a-table-column title="操作" width="70" align="center">
                <template #cell="{ rowIndex }">
                  <a-button type="text" status="danger" size="small" @click="removeTeam(rowIndex)">删除</a-button>
                </template>
              </a-table-column>
            </template>
          </a-table>
          <a-button style="margin-top: 8px;" size="small" @click="addTeam">
            <template #icon><icon-plus /></template>
            添加班组
          </a-button>
        </a-form-item>
        <a-form-item label="演练描述" field="description">
          <a-textarea v-model="formData.description" placeholder="请输入演练描述信息" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { drillApi } from '@/api'
import dayjs from 'dayjs'

const searchKeyword = ref('')
const filterStatus = ref<string | undefined>(undefined)
const listLoading = ref(false)
const drillList = ref<any[]>([])
const stats = ref<any>({})
const currentDetail = ref<any>(null)
const checkInKeyword = ref('')
const createVisible = ref(false)
const editingDrill = ref<any>(null)
const formRef = ref()

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: true
})

const checkInPagination = reactive({
  current: 1,
  pageSize: 10
})

const formData = reactive({
  id: 0,
  drill_name: '',
  drill_type: undefined as string | undefined,
  location: '',
  start_time: undefined as any,
  end_time: undefined as any,
  expected_teams: [{ team_name: '', expected_count: 0 }],
  description: ''
})

const checkInLink = computed(() => {
  if (!currentDetail.value?.check_in_token) return ''
  return `${window.location.origin}/drill/check-in/${currentDetail.value.check_in_token}`
})

const teamStats = computed(() => {
  const teams = currentDetail.value?.expected_teams || []
  const checkIns = currentDetail.value?.check_ins || []
  return teams.map((t: any) => {
    const actual = checkIns.filter((c: any) => c.team_name === t.team_name).length
    return {
      team_name: t.team_name,
      expected_count: t.expected_count || 0,
      actual_count: actual
    }
  })
})

const filteredCheckIns = computed(() => {
  const list = currentDetail.value?.check_ins || []
  if (!checkInKeyword.value) return list
  return list.filter((c: any) =>
    c.participant_name?.includes(checkInKeyword.value) ||
    c.team_name?.includes(checkInKeyword.value)
  )
})

const fetchStats = async () => {
  try {
    const res: any = await drillApi.getStatistics()
    stats.value = res.data || res
  } catch (e) {}
}

const fetchDrills = async () => {
  listLoading.value = true
  try {
    const params: any = {
      page: pagination.current,
      page_size: pagination.pageSize
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterStatus.value) params.status = filterStatus.value
    const res: any = await drillApi.getList(params)
    const data = res.data || res
    drillList.value = data.items || []
    pagination.total = data.total || 0
  } finally {
    listLoading.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.current = page
  fetchDrills()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.current = 1
  fetchDrills()
}

const viewDetail = async (record: any) => {
  try {
    const res: any = await drillApi.getDetail(record.id)
    currentDetail.value = res.data || res
    checkInPagination.current = 1
  } catch (e: any) {
    Message.error(e.message || '获取详情失败')
  }
}

const backToList = () => {
  currentDetail.value = null
  fetchDrills()
  fetchStats()
}

const openCreateModal = () => {
  editingDrill.value = null
  Object.assign(formData, {
    id: 0,
    drill_name: '',
    drill_type: undefined,
    location: '',
    start_time: undefined,
    end_time: undefined,
    expected_teams: [{ team_name: '', expected_count: 0 }],
    description: ''
  })
  createVisible.value = true
}

const editDrill = (record: any) => {
  editingDrill.value = record
  Object.assign(formData, {
    id: record.id,
    drill_name: record.drill_name,
    drill_type: record.drill_type,
    location: record.location,
    start_time: record.start_time ? dayjs(record.start_time) : undefined,
    end_time: record.end_time ? dayjs(record.end_time) : undefined,
    expected_teams: (record.expected_teams && record.expected_teams.length)
      ? [...record.expected_teams.map((t: any) => ({ ...t }))]
      : [{ team_name: '', expected_count: 0 }],
    description: record.description || ''
  })
  createVisible.value = true
}

const addTeam = () => {
  formData.expected_teams.push({ team_name: '', expected_count: 0 })
}

const removeTeam = (index: number) => {
  formData.expected_teams.splice(index, 1)
}

const handleSubmitDrill = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  const teams = formData.expected_teams.filter((t: any) => t.team_name && t.team_name.trim())
  if (teams.length === 0) {
    Message.warning('请至少添加一个参与班组')
    return
  }
  const payload = {
    drill_name: formData.drill_name,
    drill_type: formData.drill_type,
    location: formData.location,
    start_time: formData.start_time ? dayjs(formData.start_time).format('YYYY-MM-DD HH:mm:ss') : null,
    end_time: formData.end_time ? dayjs(formData.end_time).format('YYYY-MM-DD HH:mm:ss') : null,
    expected_teams: teams,
    description: formData.description
  }
  try {
    if (editingDrill.value) {
      await drillApi.update(editingDrill.value.id, payload)
      Message.success('更新成功')
    } else {
      await drillApi.create(payload)
      Message.success('创建成功')
    }
    createVisible.value = false
    fetchDrills()
    fetchStats()
  } catch (e: any) {
    Message.error(e.message || '保存失败')
  }
}

const handleStart = (record: any) => {
  Modal.confirm({
    title: '确认开始演练？',
    content: '开始后签到入口将开启，参演人员可通过签到码或链接签到。',
    okText: '确认开始',
    cancelText: '取消',
    onOk: async () => {
      try {
        await drillApi.start(record.id)
        Message.success('演练已开始')
        if (currentDetail.value?.id === record.id) {
          viewDetail(record)
        } else {
          fetchDrills()
        }
        fetchStats()
      } catch (e: any) {
        Message.error(e.message || '操作失败')
      }
    }
  })
}

const handleEnd = (record: any) => {
  Modal.confirm({
    title: '确认结束演练？',
    content: '结束后签到入口将关闭，参演人员无法再进行签到。',
    okText: '确认结束',
    cancelText: '取消',
    status: 'warning',
    onOk: async () => {
      try {
        await drillApi.end(record.id)
        Message.success('演练已结束')
        if (currentDetail.value?.id === record.id) {
          viewDetail(record)
        } else {
          fetchDrills()
        }
        fetchStats()
      } catch (e: any) {
        Message.error(e.message || '操作失败')
      }
    }
  })
}

const handleDelete = async (record: any) => {
  try {
    await drillApi.delete(record.id)
    Message.success('删除成功')
    fetchDrills()
    fetchStats()
  } catch (e: any) {
    Message.error(e.message || '删除失败')
  }
}

const refreshCode = async () => {
  if (!currentDetail.value) return
  try {
    const res: any = await drillApi.refreshCode(currentDetail.value.id)
    const data = res.data || res
    currentDetail.value.check_in_code = data.check_in_code
    currentDetail.value.check_in_token = data.check_in_token
    Message.success('签到入口已刷新')
  } catch (e: any) {
    Message.error(e.message || '刷新失败')
  }
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(checkInLink.value)
    Message.success('链接已复制到剪贴板')
  } catch {
    Message.warning('复制失败，请手动复制')
  }
}

const handleExport = async () => {
  if (!currentDetail.value) return
  try {
    const res: any = await drillApi.export(currentDetail.value.id)
    const data = res.data || res
    const { drill_info, team_summary, check_in_records } = data

    const lines: string[] = []
    lines.push('='.repeat(50))
    lines.push('应急演练签到记录导出表')
    lines.push('='.repeat(50))
    lines.push('')
    lines.push('【演练基本信息】')
    drill_info.forEach((item: any) => lines.push(`${item.项目}：${item.值}`))
    lines.push('')
    lines.push('【各班组签到统计】')
    lines.push('班组\t预期人数\t实际签到\t到场率')
    team_summary.forEach((t: any) => {
      lines.push(`${t.班组}\t${t.预期人数}\t${t.实际签到}\t${t.到场率}`)
    })
    lines.push('')
    lines.push('【签到明细记录】')
    lines.push('序号\t姓名\t班组\t签到时间\t签到方式')
    check_in_records.forEach((r: any) => {
      lines.push(`${r.序号}\t${r.姓名}\t${r.班组}\t${r.签到时间}\t${r.签到方式}`)
    })

    const content = lines.join('\n')
    const blob = new Blob(['\ufeff' + content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${currentDetail.value.drill_name}_签到记录_${dayjs().format('YYYYMMDDHHmm')}.txt`
    a.click()
    URL.revokeObjectURL(url)
    Message.success('导出成功')
  } catch (e: any) {
    Message.error(e.message || '导出失败')
  }
}

const formatDateTime = (val: any) => {
  if (!val) return '-'
  return dayjs(val).format('YYYY-MM-DD HH:mm')
}

const getStatusText = (status: string) => ({
  draft: '草稿', ongoing: '进行中', ended: '已结束'
}[status] || status)

const getStatusColor = (status: string) => ({
  draft: 'gray', ongoing: 'green', ended: 'blue'
}[status] || 'gray')

onMounted(() => {
  fetchStats()
  fetchDrills()
})
</script>

<style scoped>
.drill-container {
  width: 100%;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #86909c;
  font-size: 13px;
}

.stat-card {
  padding: 4px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.icon-blue { background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%); }
.icon-green { background: linear-gradient(135deg, #00B42A 0%, #23C343 100%); }
.icon-orange { background: linear-gradient(135deg, #FF7D00 0%, #FF9A2E 100%); }
.icon-purple { background: linear-gradient(135deg, #722ED1 0%, #9554E0 100%); }

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #1d2129;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #86909c;
  margin-top: 2px;
}

.list-card, .detail-card, .code-card {
  border-radius: 8px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar-small {
  margin-bottom: 12px;
}

.time-text {
  font-size: 13px;
  color: #1d2129;
}

.time-sub {
  font-size: 12px;
  color: #86909c;
  margin-top: 2px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e6eb;
}

.sub-stat {
  text-align: center;
}

.sub-stat-num {
  font-size: 32px;
  font-weight: 700;
  color: #165DFF;
  line-height: 1.2;
}

.sub-stat-label {
  font-size: 13px;
  color: #4e5969;
  margin-top: 6px;
}

.code-display {
  text-align: center;
  padding: 12px 0;
}

.code-label {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 10px;
}

.code-value {
  font-size: 42px;
  font-weight: 700;
  letter-spacing: 10px;
  color: #165DFF;
  font-family: 'Courier New', monospace;
  padding: 16px 24px;
  background: linear-gradient(135deg, #e8f3ff 0%, #f0f5ff 100%);
  border-radius: 12px;
  display: inline-block;
}

.link-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.link-hint {
  font-size: 12px;
  color: #86909c;
  margin-top: 8px;
}
</style>
