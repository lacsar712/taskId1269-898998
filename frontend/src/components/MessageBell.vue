<template>
  <a-dropdown trigger="click" @visible-change="handleDropdownVisibleChange">
    <div class="message-bell" style="cursor: pointer; color: #fff; position: relative;">
      <icon-notification :size="22" />
      <a-badge
        v-if="unreadCount > 0"
        :count="unreadCount > 99 ? '99+' : unreadCount"
        :dot="false"
        :max-count="99"
        style="position: absolute; top: -6px; right: -10px;"
      />
    </div>
    <template #content>
      <div class="message-dropdown" @click.stop>
        <div class="dropdown-header">
          <span class="header-title">消息通知</span>
          <a-space>
            <a-link
              v-if="unreadCount > 0"
              @click="handleMarkAllRead"
              :loading="markingAllRead"
            >
              全部已读
            </a-link>
            <a-link @click="goToMessageCenter">查看全部</a-link>
          </a-space>
        </div>
        <a-tabs v-model:activeKey="activeTab" type="card" size="small">
          <a-tab-pane key="all" title="全部">
            <div class="message-list">
              <div
                v-for="msg in filteredMessages"
                :key="msg.id"
                class="message-item"
                :class="{ 'is-read': msg.is_read }"
                @click="handleMessageClick(msg)"
              >
                <div class="message-icon" :class="`type-${msg.message_type}`">
                  <component :is="getMessageIcon(msg.message_type)" :size="18" />
                </div>
                <div class="message-content">
                  <div class="message-title-row">
                    <span class="message-title">{{ msg.title }}</span>
                    <a-tag
                      v-if="!msg.is_read"
                      color="red"
                      :size="'mini'"
                      style="margin-left: 8px;"
                    >
                      未读
                    </a-tag>
                  </div>
                  <div class="message-summary">{{ msg.summary || msg.content }}</div>
                  <div class="message-meta">
                    <span>{{ msg.sender_name || '系统' }}</span>
                    <span class="message-time">{{ formatTime(msg.created_at) }}</span>
                  </div>
                </div>
                <div v-if="!msg.is_read" class="unread-dot"></div>
              </div>
              <div v-if="loading" class="loading-container">
                <a-spin :size="'small'" />
              </div>
              <div v-else-if="filteredMessages.length === 0" class="empty-container">
                <a-empty :description="'暂无消息'" :img-size="60" />
              </div>
            </div>
          </a-tab-pane>
          <a-tab-pane key="unread" title="未读">
            <div class="message-list">
              <div
                v-for="msg in unreadMessages"
                :key="msg.id"
                class="message-item"
                @click="handleMessageClick(msg)"
              >
                <div class="message-icon" :class="`type-${msg.message_type}`">
                  <component :is="getMessageIcon(msg.message_type)" :size="18" />
                </div>
                <div class="message-content">
                  <div class="message-title-row">
                    <span class="message-title">{{ msg.title }}</span>
                    <a-tag color="red" :size="'mini'" style="margin-left: 8px;">未读</a-tag>
                  </div>
                  <div class="message-summary">{{ msg.summary || msg.content }}</div>
                  <div class="message-meta">
                    <span>{{ msg.sender_name || '系统' }}</span>
                    <span class="message-time">{{ formatTime(msg.created_at) }}</span>
                  </div>
                </div>
                <div class="unread-dot"></div>
              </div>
              <div v-if="loading" class="loading-container">
                <a-spin :size="'small'" />
              </div>
              <div v-else-if="unreadMessages.length === 0" class="empty-container">
                <a-empty :description="'暂无未读消息'" :img-size="60" />
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </template>
  </a-dropdown>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message, MessagePlugin } from '@arco-design/web-vue'
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
const unreadCount = ref(0)
const loading = ref(false)
const markingAllRead = ref(false)
const activeTab = ref('all')

let pollTimer: number | null = null

const filteredMessages = computed(() => messages.value)
const unreadMessages = computed(() => messages.value.filter(m => !m.is_read))

const getMessageIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    alarm: 'icon-exclamation',
    approval: 'icon-safety',
    workorder: 'icon-unordered-list',
    announcement: 'icon-notification'
  }
  return iconMap[type] || 'icon-notification'
}

const formatTime = (time: string) => {
  const now = dayjs()
  const msgTime = dayjs(time)
  const diffMinutes = now.diff(msgTime, 'minute')
  const diffHours = now.diff(msgTime, 'hour')
  const diffDays = now.diff(msgTime, 'day')

  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return msgTime.format('MM-DD HH:mm')
}

const fetchMessages = async () => {
  try {
    loading.value = true
    const res = await messageApi.getRecent(10)
    messages.value = res.data || []
  } catch (error) {
    console.error('获取消息失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchUnreadCount = async () => {
  try {
    const res = await messageApi.getUnreadCount()
    unreadCount.value = res.data?.total || 0
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
    const res = await messageApi.markAllRead()
    Message.success(res.data?.message || '操作成功')
    messages.value.forEach(m => m.is_read = true)
    unreadCount.value = 0
  } catch (error) {
    Message.error('操作失败')
  } finally {
    markingAllRead.value = false
  }
}

const goToMessageCenter = () => {
  router.push('/message-center')
}

const handleDropdownVisibleChange = (visible: boolean) => {
  if (visible) {
    fetchMessages()
  }
}

const startPolling = () => {
  pollTimer = window.setInterval(() => {
    fetchUnreadCount()
  }, 30000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(() => {
  fetchUnreadCount()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

defineExpose({
  refresh: fetchUnreadCount
})
</script>

<style scoped>
.message-bell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.message-bell:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.message-dropdown {
  width: 380px;
  max-height: 500px;
  overflow: hidden;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e6eb;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.message-list {
  max-height: 380px;
  overflow-y: auto;
}

.message-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  border-bottom: 1px solid #f2f3f5;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.message-item:hover {
  background-color: #f7f8fa;
}

.message-item.is-read {
  opacity: 0.7;
}

.message-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
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

.message-content {
  flex: 1;
  min-width: 0;
}

.message-title-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.message-title {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-item.is-read .message-title {
  font-weight: normal;
}

.message-summary {
  font-size: 13px;
  color: #86909c;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 4px;
}

.message-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #c9cdd4;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #ff4d4f;
  flex-shrink: 0;
  margin-left: 8px;
  align-self: flex-start;
  margin-top: 6px;
}

.loading-container,
.empty-container {
  padding: 40px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

:deep(.arco-tabs-tab) {
  padding: 8px 20px;
}

:deep(.arco-tabs-content) {
  padding: 0;
}

:deep(.arco-dropdown-popup) {
  padding: 0;
  overflow: hidden;
}
</style>
