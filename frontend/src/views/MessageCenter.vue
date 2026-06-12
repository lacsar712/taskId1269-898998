<template>
  <div class="message-center">
    <a-card :bordered="false">
      <template #title>
        <div class="page-title">
          <icon-notification :size="24" style="margin-right: 8px; color: #165dff;" />
          <span>消息中心</span>
          <a-tag v-if="unreadCount > 0" color="red" style="margin-left: 12px;">
            {{ unreadCount }} 条未读
          </a-tag>
        </div>
      </template>
      <template #extra>
        <a-space>
          <a-button
            type="primary"
            @click="handleMarkAllRead"
            :loading="markingAllRead"
            :disabled="unreadCount === 0"
          >
            <template #icon><icon-check /></template>
            一键全部已读
          </a-button>
        </a-space>
      </template>

      <div class="filter-section">
        <a-space :size="16" wrap>
          <a-radio-group v-model="filterStatus" type="button" size="default">
            <a-radio value="all">全部消息</a-radio>
            <a-radio value="unread">未读消息</a-radio>
            <a-radio value="read">已读消息</a-radio>
          </a-radio-group>

          <a-select
            v-model="filterType"
            :style="{ width: '160px' }"
            placeholder="消息类型"
            allow-clear
          >
            <a-option value="alarm">告警推送</a-option>
            <a-option value="approval">审批提醒</a-option>
            <a-option value="workorder">工单指派</a-option>
            <a-option value="announcement">系统公告</a-option>
          </a-select>

          <a-range-picker
            v-model="dateRange"
            :style="{ width: '280px' }"
            placeholder="开始日期"
            allow-clear
          />

          <a-button type="outline" @click="handleSearch">
            <template #icon><icon-search /></template>
            搜索
          </a-button>

          <a-button @click="handleReset">
            <template #icon><icon-refresh /></template>
            重置
          </a-button>
        </a-space>
      </div>

      <div class="message-stats">
        <a-row :gutter="16">
          <a-col :span="6">
            <div class="stat-card" :class="{ active: filterType === undefined && filterStatus === 'all' }" @click="filterByType()">
              <div class="stat-icon all">
                <icon-notification :size="28" />
              </div>
              <div class="stat-info">
                <div class="stat-count">{{ stats.total }}</div>
                <div class="stat-label">全部消息</div>
              </div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-card" :class="{ active: filterType === 'alarm' }" @click="filterByType('alarm')">
              <div class="stat-icon alarm">
                <icon-exclamation :size="28" />
              </div>
              <div class="stat-info">
                <div class="stat-count">{{ stats.alarm }}</div>
                <div class="stat-label">告警推送</div>
              </div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-card" :class="{ active: filterType === 'approval' }" @click="filterByType('approval')">
              <div class="stat-icon approval">
                <icon-safety :size="28" />
              </div>
              <div class="stat-info">
                <div class="stat-count">{{ stats.approval }}</div>
                <div class="stat-label">审批提醒</div>
              </div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-card" :class="{ active: filterType === 'workorder' }" @click="filterByType('workorder')">
              <div class="stat-icon workorder">
                <icon-unordered-list :size="28" />
              </div>
              <div class="stat-info">
                <div class="stat-count">{{ stats.workorder }}</div>
                <div class="stat-label">工单指派</div>
              </div>
            </div>
          </a-col>
        </a-row>
      </div>

      <div class="message-list-section">
        <div v-if="loading" class="loading-wrapper">
          <a-spin :size="'large'" />
        </div>
        <div v-else-if="messages.length === 0" class="empty-wrapper">
          <a-empty :description="'暂无消息数据'" :img-size="120" />
        </div>
        <div v-else class="message-list">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-card"
            :class="{ 'is-read': msg.is_read }"
            @click="handleMessageClick(msg)"
          >
            <div class="message-left">
              <div class="message-icon" :class="`type-${msg.message_type}`">
                <component :is="getMessageIcon(msg.message_type)" :size="22" />
              </div>
            </div>
            <div class="message-body">
              <div class="message-header">
                <h3 class="message-title">
                  {{ msg.title }}
                  <a-tag
                    v-if="!msg.is_read"
                    color="red"
                    :size="'small'"
                    style="margin-left: 10px;"
                  >
                    未读
                  </a-tag>
                  <a-tag :color="getPriorityColor(msg.priority)" :size="'small'" style="margin-left: 8px;">
                    {{ getPriorityLabel(msg.priority) }}
                  </a-tag>
                </h3>
                <div class="message-time">
                  <icon-clock :size="14" style="margin-right: 4px;" />
                  {{ formatFullTime(msg.created_at) }}
                </div>
              </div>
              <div class="message-content-text">
                {{ msg.content || msg.summary }}
              </div>
              <div class="message-footer">
                <a-space :size="16">
                  <span>
                    <icon-user :size="14" style="margin-right: 4px;" />
                    {{ msg.sender_name || '系统' }}
                  </span>
                  <span v-if="msg.related_type">
                    <icon-tag :size="14" style="margin-right: 4px;" />
                    {{ getTypeLabel(msg.message_type) }}
                  </span>
                </a-space>
                <div v-if="msg.related_url" class="message-action">
                  <a-link>
                    查看详情
                    <icon-right :size="14" style="margin-left: 4px;" />
                  </a-link>
                </div>
              </div>
            </div>
            <div v-if="!msg.is_read" class="unread-indicator"></div>
          </div>
        </div>

        <div v-if="total > 0" class="pagination-wrapper">
          <a-pagination
            v-model:current="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="total"
            :show-total="true"
            :show-page-size="true"
            :page-size-options="[10, 20, 50, 100]"
            @change="handlePageChange"
          />
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { messageApi } from '@/api'
import dayjs from 'dayjs'

const router = useRouter()

interface MessageItem {
  id: number
  title: string
  content?: string
  summary?: string
  message_type: string
  priority: string
  sender_name?: string
  related_type?: string
  related_id?: number
  related_url?: string
  is_read: boolean
  read_at?: string
  created_at: string
}

const messages = ref<MessageItem[]>([])
const loading = ref(false)
const markingAllRead = ref(false)
const unreadCount = ref(0)

const filterStatus = ref('all')
const filterType = ref<string | undefined>(undefined)
const dateRange = ref<[Date, Date] | []>([])

const pagination = reactive({
  page: 1,
  page_size: 10
})

const total = ref(0)

const stats = reactive({
  total: 0,
  alarm: 0,
  approval: 0,
  workorder: 0,
  announcement: 0
})

const getMessageIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    alarm: 'icon-exclamation',
    approval: 'icon-safety',
    workorder: 'icon-unordered-list',
    announcement: 'icon-notification'
  }
  return iconMap[type] || 'icon-notification'
}

const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    alarm: '告警推送',
    approval: '审批提醒',
    workorder: '工单指派',
    announcement: '系统公告'
  }
  return labelMap[type] || type
}

const getPriorityColor = (priority: string) => {
  const colorMap: Record<string, string> = {
    low: 'gray',
    medium: 'blue',
    high: 'orange',
    urgent: 'red'
  }
  return colorMap[priority] || 'blue'
}

const getPriorityLabel = (priority: string) => {
  const labelMap: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return labelMap[priority] || '中'
}

const formatFullTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const fetchMessages = async () => {
  try {
    loading.value = true
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (filterStatus.value === 'unread') {
      params.is_read = false
    } else if (filterStatus.value === 'read') {
      params.is_read = true
    }

    if (filterType.value) {
      params.message_type = filterType.value
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dayjs(dateRange.value[0]).format('YYYY-MM-DD')
      params.end_date = dayjs(dateRange.value[1]).format('YYYY-MM-DD')
    }

    const res = await messageApi.getList(params)
    messages.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (error) {
    Message.error('获取消息列表失败')
  } finally {
    loading.value = false
  }
}

const fetchUnreadCount = async () => {
  try {
    const res = await messageApi.getUnreadCount()
    unreadCount.value = res.data?.total || 0
    stats.alarm = res.data?.by_type?.alarm || 0
    stats.approval = res.data?.by_type?.approval || 0
    stats.workorder = res.data?.by_type?.workorder || 0
    stats.announcement = res.data?.by_type?.announcement || 0
    stats.total = unreadCount.value
  } catch (error) {
    console.error('获取未读计数失败:', error)
  }
}

const handleMessageClick = async (msg: MessageItem) => {
  if (!msg.is_read) {
    try {
      await messageApi.markRead(msg.id)
      msg.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      if (msg.message_type === 'alarm') stats.alarm = Math.max(0, stats.alarm - 1)
      if (msg.message_type === 'approval') stats.approval = Math.max(0, stats.approval - 1)
      if (msg.message_type === 'workorder') stats.workorder = Math.max(0, stats.workorder - 1)
      if (msg.message_type === 'announcement') stats.announcement = Math.max(0, stats.announcement - 1)
      stats.total = unreadCount.value
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }

  if (msg.related_url) {
    router.push(msg.related_url)
  }
}

const handleMarkAllRead = async () => {
  try {
    markingAllRead.value = true
    const res = await messageApi.markAllRead(filterType.value)
    Message.success(res.data?.message || '操作成功')
    messages.value.forEach(m => m.is_read = true)
    unreadCount.value = 0
    stats.alarm = 0
    stats.approval = 0
    stats.workorder = 0
    stats.announcement = 0
    stats.total = 0
  } catch (error) {
    Message.error('操作失败')
  } finally {
    markingAllRead.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchMessages()
}

const handleReset = () => {
  filterStatus.value = 'all'
  filterType.value = undefined
  dateRange.value = []
  pagination.page = 1
  fetchMessages()
}

const handlePageChange = () => {
  fetchMessages()
}

const filterByType = (type?: string) => {
  filterType.value = type
  pagination.page = 1
  fetchMessages()
}

watch([filterStatus, filterType, dateRange], () => {
  // 可以在这里添加自动搜索逻辑
})

onMounted(() => {
  fetchMessages()
  fetchUnreadCount()
})
</script>

<style scoped>
.message-center {
  padding: 0;
}

.page-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}

.filter-section {
  padding: 16px 0;
  border-bottom: 1px solid #e5e6eb;
  margin-bottom: 20px;
}

.message-stats {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #f7f8fa 0%, #f0f5ff 100%);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-card.active {
  border-color: #165dff;
  background: linear-gradient(135deg, #e8f3ff 0%, #e0e7ff 100%);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-right: 16px;
}

.stat-icon.all {
  background: linear-gradient(135deg, #165dff 0%, #0e42d2 100%);
}

.stat-icon.alarm {
  background: linear-gradient(135deg, #ff4d4f 0%, #f5222d 100%);
}

.stat-icon.approval {
  background: linear-gradient(135deg, #14c9c9 0%, #0ea5a5 100%);
}

.stat-icon.workorder {
  background: linear-gradient(135deg, #ff7d00 0%, #e56a00 100%);
}

.stat-info {
  flex: 1;
}

.stat-count {
  font-size: 28px;
  font-weight: 700;
  color: #1d2129;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #86909c;
  margin-top: 4px;
}

.message-list-section {
  min-height: 400px;
}

.loading-wrapper,
.empty-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-card {
  display: flex;
  padding: 20px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.message-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #165dff;
}

.message-card.is-read {
  background: #f7f8fa;
}

.message-left {
  margin-right: 16px;
}

.message-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.type-alarm {
  background: linear-gradient(135deg, #ff4d4f 0%, #f5222d 100%);
}

.type-approval {
  background: linear-gradient(135deg, #165dff 0%, #0e42d2 100%);
}

.type-workorder {
  background: linear-gradient(135deg, #14c9c9 0%, #0ea5a5 100%);
}

.type-announcement {
  background: linear-gradient(135deg, #ff7d00 0%, #e56a00 100%);
}

.message-body {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.message-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
  display: flex;
  align-items: center;
}

.message-card.is-read .message-title {
  font-weight: 500;
  color: #4e5969;
}

.message-time {
  font-size: 13px;
  color: #86909c;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-left: 16px;
}

.message-content-text {
  font-size: 14px;
  color: #4e5969;
  line-height: 1.6;
  margin-bottom: 12px;
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #86909c;
}

.message-action {
  color: #165dff;
}

.unread-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #ff4d4f;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
