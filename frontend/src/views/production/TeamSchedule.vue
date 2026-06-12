<template>
  <div class="page-container">
    <div class="page-header">
      <h2>班组排班表</h2>
      <p>周视图排班管理 / 班次调整 / 工时统计</p>
    </div>

    <a-card>
      <template #title>
        <a-space>
          <span>排班管理</span>
        </a-space>
      </template>

      <div class="toolbar">
        <a-space :size="16" wrap>
          <a-form layout="inline">
            <a-form-item label="选择班组">
              <a-select v-model="selectedTeamId" style="width: 200px" @change="handleTeamChange">
                <a-option v-for="team in teams" :key="team.id" :value="team.id">
                  {{ team.name }}
                </a-option>
              </a-select>
            </a-form-item>
            <a-form-item label="选择周次">
              <a-date-picker
                v-model="weekStartDate"
                style="width: 200px"
                :picker="'week'"
                format="YYYY年第ww周"
                @change="handleWeekChange"
              />
            </a-form-item>
          </a-form>

          <a-space>
            <a-button type="primary" @click="prevWeek">
              <template #icon><icon-left /></template>
              上一周
            </a-button>
            <a-button @click="nextWeek">
              下一周
              <template #icon><icon-right /></template>
            </a-button>
          </a-space>

          <a-divider direction="vertical" />

          <a-space>
            <a-button @click="showBatchModal = true">
              <template #icon><icon-plus /></template>
              批量排班
            </a-button>
            <a-button @click="showCopyModal = true">
              <template #icon><icon-copy /></template>
              整周复制
            </a-button>
            <a-button @click="loadScheduleMatrix">
              <template #icon><icon-refresh /></template>
              刷新
            </a-button>
          </a-space>
        </a-space>
      </div>

      <div class="legend-bar">
        <a-space :size="24">
          <span class="legend-item">
            <span class="legend-dot morning"></span>
            早班
          </span>
          <span class="legend-item">
            <span class="legend-dot afternoon"></span>
            中班
          </span>
          <span class="legend-item">
            <span class="legend-dot night"></span>
            晚班
          </span>
          <span class="legend-item">
            <span class="legend-dot rest"></span>
            休班
          </span>
          <span class="legend-item">
            <span class="legend-dot empty"></span>
            待安排
          </span>
        </a-space>
      </div>

      <div class="schedule-matrix-wrapper" v-loading="loading">
        <table class="schedule-matrix">
          <thead>
            <tr>
              <th class="col-name">姓名</th>
              <th v-for="date in weekDates" :key="date.dateStr" class="col-date">
                <div class="date-header">
                  <div class="date-weekday">{{ date.weekday }}</div>
                  <div class="date-day">{{ date.monthDay }}</div>
                  <div v-if="date.isToday" class="today-badge">今天</div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in scheduleUsers" :key="user.user_id" class="user-row">
              <td class="col-name">
                <div class="user-cell" @click="showUserStats(user)">
                  <a-avatar :size="32" style="background-color: #14C9C9;">
                    {{ user.real_name?.charAt(0) || user.username?.charAt(0) }}
                  </a-avatar>
                  <div class="user-info">
                    <span class="user-name">{{ user.real_name || user.username }}</span>
                    <span class="user-position" v-if="user.position">{{ user.position }}</span>
                  </div>
                  <icon-right class="arrow-icon" />
                </div>
              </td>
              <td
                v-for="date in weekDates"
                :key="date.dateStr"
                class="shift-cell"
                :class="{ 
                  'is-empty': !user.schedules[date.dateStr],
                  'is-today': date.isToday
                }"
                @click="handleCellClick(user, date)"
              >
                <div
                  v-if="user.schedules[date.dateStr]"
                  class="shift-tag"
                  :class="user.schedules[date.dateStr].shift_type"
                >
                  {{ getShiftLabel(user.schedules[date.dateStr].shift_type) }}
                </div>
                <div v-else class="empty-placeholder">
                  <icon-plus :size="16" />
                  <span>待安排</span>
                </div>
              </td>
            </tr>
            <tr v-if="scheduleUsers.length === 0" class="empty-row">
              <td :colspan="weekDates.length + 1" class="empty-tip">
                <a-empty description="暂无班组成员，请先添加成员" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </a-card>

    <a-modal
      v-model:visible="shiftModalVisible"
      title="调整排班"
      @ok="handleShiftSave"
      @cancel="shiftModalVisible = false"
      width="400px"
    >
      <a-form :model="shiftForm" layout="vertical">
        <a-form-item label="人员">
          <a-input :value="currentUser?.real_name || currentUser?.username" disabled />
        </a-form-item>
        <a-form-item label="日期">
          <a-input :value="currentDateStr" disabled />
        </a-form-item>
        <a-form-item label="班次类型">
          <a-radio-group v-model="shiftForm.shift_type" direction="horizontal">
            <a-radio value="morning">早班</a-radio>
            <a-radio value="afternoon">中班</a-radio>
            <a-radio value="night">晚班</a-radio>
            <a-radio value="rest">休班</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model="shiftForm.remark" placeholder="请输入备注（可选）" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:visible="batchModalVisible"
      title="批量排班"
      @ok="handleBatchSave"
      @cancel="batchModalVisible = false"
      width="480px"
    >
      <a-form :model="batchForm" layout="vertical">
        <a-form-item label="选择日期">
          <a-range-picker v-model="batchForm.date_range" style="width: 100%" />
        </a-form-item>
        <a-form-item label="选择人员">
          <a-transfer
            v-model="batchForm.user_ids"
            :data="transferData"
            :titles="['可选人员', '已选人员']"
            :list-style="{ width: '180px', height: '240px' }"
          />
        </a-form-item>
        <a-form-item label="班次类型">
          <a-radio-group v-model="batchForm.shift_type" direction="horizontal">
            <a-radio value="morning">早班</a-radio>
            <a-radio value="afternoon">中班</a-radio>
            <a-radio value="night">晚班</a-radio>
            <a-radio value="rest">休班</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model="batchForm.remark" placeholder="请输入备注（可选）" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:visible="copyModalVisible"
      title="整周复制"
      @ok="handleCopyWeek"
      @cancel="copyModalVisible = false"
      width="420px"
    >
      <a-form :model="copyForm" layout="vertical">
        <a-form-item label="源周（复制哪一周的排班）">
          <a-date-picker
            v-model="copyForm.source_week_start"
            style="width: 100%"
            :picker="'week'"
            format="YYYY年第ww周"
          />
        </a-form-item>
        <a-form-item label="目标周（粘贴到哪一周）">
          <a-date-picker
            v-model="copyForm.target_week_start"
            style="width: 100%"
            :picker="'week'"
            format="YYYY年第ww周"
          />
        </a-form-item>
        <a-alert type="info" content="将源周所有排班数据复制到目标周，已有的排班将被覆盖。" />
      </a-form>
    </a-modal>

    <a-modal
      v-model:visible="statsModalVisible"
      title="当月班次统计"
      :footer="null"
      width="520px"
    >
      <div class="stats-header">
        <a-avatar :size="48" style="background-color: #14C9C9;">
          {{ statsUser?.real_name?.charAt(0) || statsUser?.username?.charAt(0) }}
        </a-avatar>
        <div class="stats-user-info">
          <h3>{{ statsUser?.real_name || statsUser?.username }}</h3>
          <p>{{ statsUser?.position || '运行班组' }}</p>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-item morning">
          <div class="stat-value">{{ userStats.morning_count }}</div>
          <div class="stat-label">早班</div>
        </div>
        <div class="stat-item afternoon">
          <div class="stat-value">{{ userStats.afternoon_count }}</div>
          <div class="stat-label">中班</div>
        </div>
        <div class="stat-item night">
          <div class="stat-value">{{ userStats.night_count }}</div>
          <div class="stat-label">晚班</div>
        </div>
        <div class="stat-item rest">
          <div class="stat-value">{{ userStats.rest_count }}</div>
          <div class="stat-label">休班</div>
        </div>
      </div>

      <a-divider />

      <div class="stats-summary">
        <div class="summary-item">
          <span class="summary-label">总出勤天数</span>
          <span class="summary-value">{{ userStats.total_days }} 天</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">总工时合计</span>
          <span class="summary-value highlight">{{ userStats.total_work_hours }} 小时</span>
        </div>
      </div>

      <div class="stats-month">
        <span>统计月份：{{ currentMonth }}</span>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import dayjs from 'dayjs'
import isoWeek from 'dayjs/plugin/isoWeek'
import { scheduleApi, userApi } from '@/api'

dayjs.extend(isoWeek)

const teams = ref<any[]>([])
const selectedTeamId = ref<number | null>(null)
const weekStartDate = ref(dayjs().startOf('isoWeek').toDate())
const loading = ref(false)
const scheduleUsers = ref<any[]>([])
const showBatchModal = ref(false)
const showCopyModal = ref(false)

const shiftModalVisible = ref(false)
const currentUser = ref<any>(null)
const currentDateStr = ref('')
const shiftForm = ref({
  shift_type: 'morning',
  remark: ''
})

const batchModalVisible = computed({
  get: () => showBatchModal.value,
  set: (val: boolean) => { showBatchModal.value = val }
})
const batchForm = ref({
  date_range: [],
  user_ids: [] as number[],
  shift_type: 'morning',
  remark: ''
})
const transferData = ref<any[]>([])

const copyModalVisible = computed({
  get: () => showCopyModal.value,
  set: (val: boolean) => { showCopyModal.value = val }
})
const copyForm = ref({
  source_week_start: null,
  target_week_start: null
})

const statsModalVisible = ref(false)
const statsUser = ref<any>(null)
const userStats = ref({
  morning_count: 0,
  afternoon_count: 0,
  night_count: 0,
  rest_count: 0,
  total_work_hours: 0,
  total_days: 0
})
const currentMonth = computed(() => dayjs().format('YYYY年MM月'))

const weekDates = computed(() => {
  const dates = []
  const start = dayjs(weekStartDate.value).startOf('isoWeek')
  const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  for (let i = 0; i < 7; i++) {
    const d = start.add(i, 'day')
    dates.push({
      dateStr: d.format('YYYY-MM-DD'),
      weekday: weekdayNames[i],
      monthDay: d.format('MM/DD'),
      isToday: d.isSame(dayjs(), 'day')
    })
  }
  return dates
})

const shiftLabelMap: Record<string, string> = {
  morning: '早班',
  afternoon: '中班',
  night: '晚班',
  rest: '休班'
}

function getShiftLabel(type: string) {
  return shiftLabelMap[type] || type
}

async function loadTeams() {
  try {
    const res: any = await scheduleApi.getTeams({ is_active: 1 })
    teams.value = res.data || res || []
    if (teams.value.length > 0 && !selectedTeamId.value) {
      selectedTeamId.value = teams.value[0].id
    }
  } catch (e) {
    console.error('加载班组失败', e)
  }
}

async function loadScheduleMatrix() {
  if (!selectedTeamId.value) return
  loading.value = true
  try {
    const weekStart = dayjs(weekStartDate.value).startOf('isoWeek').format('YYYY-MM-DD')
    const res: any = await scheduleApi.getScheduleMatrix(selectedTeamId.value, weekStart)
    const data = res.data || res
    scheduleUsers.value = data.users || []
    
    transferData.value = scheduleUsers.value.map((u: any) => ({
      key: u.user_id,
      value: u.user_id,
      label: u.real_name || u.username
    }))
  } catch (e: any) {
    Message.error('加载排班数据失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function handleTeamChange() {
  loadScheduleMatrix()
}

function handleWeekChange() {
  loadScheduleMatrix()
}

function prevWeek() {
  weekStartDate.value = dayjs(weekStartDate.value).subtract(1, 'week').toDate()
  loadScheduleMatrix()
}

function nextWeek() {
  weekStartDate.value = dayjs(weekStartDate.value).add(1, 'week').toDate()
  loadScheduleMatrix()
}

function handleCellClick(user: any, date: any) {
  currentUser.value = user
  currentDateStr.value = date.dateStr
  const schedule = user.schedules[date.dateStr]
  if (schedule) {
    shiftForm.value = {
      shift_type: schedule.shift_type,
      remark: schedule.remark || ''
    }
  } else {
    shiftForm.value = {
      shift_type: 'morning',
      remark: ''
    }
  }
  shiftModalVisible.value = true
}

async function handleShiftSave() {
  if (!currentUser.value || !currentDateStr.value || !selectedTeamId.value) return
  try {
    const data = {
      team_id: selectedTeamId.value,
      user_id: currentUser.value.user_id,
      shift_date: currentDateStr.value,
      shift_type: shiftForm.value.shift_type,
      remark: shiftForm.value.remark
    }
    await scheduleApi.createShift(data)
    Message.success('排班保存成功')
    shiftModalVisible.value = false
    loadScheduleMatrix()
  } catch (e: any) {
    Message.error('保存失败：' + (e.message || '未知错误'))
  }
}

async function handleBatchSave() {
  if (!selectedTeamId.value || !batchForm.value.date_range || batchForm.value.date_range.length < 2) {
    Message.warning('请选择日期范围和人员')
    return
  }
  if (batchForm.value.user_ids.length === 0) {
    Message.warning('请选择至少一名人员')
    return
  }
  try {
    const start = dayjs(batchForm.value.date_range[0])
    const end = dayjs(batchForm.value.date_range[1])
    const dates: string[] = []
    let d = start
    while (d.isBefore(end) || d.isSame(end, 'day')) {
      dates.push(d.format('YYYY-MM-DD'))
      d = d.add(1, 'day')
    }
    
    for (const date of dates) {
      await scheduleApi.batchCreateShift({
        team_id: selectedTeamId.value,
        user_ids: batchForm.value.user_ids,
        shift_date: date,
        shift_type: batchForm.value.shift_type,
        remark: batchForm.value.remark
      })
    }
    
    Message.success(`批量排班成功，共${dates.length}天`)
    showBatchModal.value = false
    loadScheduleMatrix()
  } catch (e: any) {
    Message.error('批量排班失败：' + (e.message || '未知错误'))
  }
}

async function handleCopyWeek() {
  if (!selectedTeamId.value || !copyForm.value.source_week_start || !copyForm.value.target_week_start) {
    Message.warning('请选择源周和目标周')
    return
  }
  try {
    const sourceWeek = dayjs(copyForm.value.source_week_start as any).startOf('isoWeek').format('YYYY-MM-DD')
    const targetWeek = dayjs(copyForm.value.target_week_start as any).startOf('isoWeek').format('YYYY-MM-DD')
    
    await scheduleApi.copyWeekSchedule({
      team_id: selectedTeamId.value,
      source_week_start: sourceWeek,
      target_week_start: targetWeek
    })
    Message.success('整周复制成功')
    showCopyModal.value = false
    loadScheduleMatrix()
  } catch (e: any) {
    Message.error('复制失败：' + (e.message || '未知错误'))
  }
}

async function showUserStats(user: any) {
  statsUser.value = user
  statsModalVisible.value = true
  try {
    const month = dayjs().format('YYYY-MM-DD')
    const res: any = await scheduleApi.getUserMonthlyStats(user.user_id, month)
    userStats.value = res.data || res
  } catch (e: any) {
    console.error('加载用户统计失败', e)
  }
}

onMounted(() => {
  loadTeams().then(() => {
    loadScheduleMatrix()
  })
})
</script>

<style scoped>
.toolbar {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e6eb;
}

.legend-bar {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f7f8fa;
  border-radius: 6px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #4e5969;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
}

.legend-dot.morning {
  background: #14C9C9;
}

.legend-dot.afternoon {
  background: #FF7D00;
}

.legend-dot.night {
  background: #722ED1;
}

.legend-dot.rest {
  background: #00B42A;
}

.legend-dot.empty {
  background: #fff;
  border: 1px dashed #c9cdd4;
}

.schedule-matrix-wrapper {
  overflow-x: auto;
}

.schedule-matrix {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  overflow: hidden;
}

.schedule-matrix th {
  background: #f7f8fa;
  padding: 0;
  font-weight: 500;
  color: #4e5969;
  border-bottom: 1px solid #e5e6eb;
  border-right: 1px solid #e5e6eb;
}

.schedule-matrix th:last-child {
  border-right: none;
}

.schedule-matrix td {
  padding: 0;
  border-bottom: 1px solid #e5e6eb;
  border-right: 1px solid #e5e6eb;
}

.schedule-matrix td:last-child {
  border-right: none;
}

.schedule-matrix tbody tr:last-child td {
  border-bottom: none;
}

.col-name {
  width: 180px;
  min-width: 180px;
  position: sticky;
  left: 0;
  z-index: 2;
  background: #f7f8fa;
}

.col-date {
  width: 120px;
  min-width: 120px;
  text-align: center;
}

.date-header {
  padding: 12px 8px;
  position: relative;
}

.date-weekday {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 4px;
}

.date-day {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.today-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #165DFF;
  color: #fff;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
}

.user-row:hover .col-name {
  background: #e8f3ff;
}

.user-row:hover .shift-cell {
  background: #f7faff;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.user-cell:hover {
  background: #e8f3ff;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
}

.user-position {
  display: block;
  font-size: 12px;
  color: #86909c;
  margin-top: 2px;
}

.arrow-icon {
  color: #c9cdd4;
  font-size: 12px;
}

.shift-cell {
  text-align: center;
  padding: 12px 8px;
  cursor: pointer;
  transition: background 0.2s;
  height: 60px;
  vertical-align: middle;
}

.shift-cell.is-today {
  background: #f0f5ff;
}

.shift-cell.is-empty {
  background: #fafbfc;
}

.shift-cell:hover {
  background: #e8f3ff !important;
}

.shift-tag {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  min-width: 60px;
}

.shift-tag.morning {
  background: #e8fffa;
  color: #14C9C9;
}

.shift-tag.afternoon {
  background: #fff7e8;
  color: #FF7D00;
}

.shift-tag.night {
  background: #f3e8ff;
  color: #722ED1;
}

.shift-tag.rest {
  background: #e8ffea;
  color: #00B42A;
}

.empty-placeholder {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #c9cdd4;
  font-size: 12px;
}

.empty-placeholder .arco-icon {
  opacity: 0.5;
}

.empty-tip {
  padding: 40px;
  text-align: center;
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e6eb;
}

.stats-user-info h3 {
  font-size: 18px;
  color: #1d2129;
  margin: 0;
}

.stats-user-info p {
  font-size: 13px;
  color: #86909c;
  margin: 4px 0 0 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 16px 8px;
  border-radius: 8px;
  background: #f7f8fa;
}

.stat-item.morning {
  background: #e8fffa;
}

.stat-item.morning .stat-value {
  color: #14C9C9;
}

.stat-item.afternoon {
  background: #fff7e8;
}

.stat-item.afternoon .stat-value {
  color: #FF7D00;
}

.stat-item.night {
  background: #f3e8ff;
}

.stat-item.night .stat-value {
  color: #722ED1;
}

.stat-item.rest {
  background: #e8ffea;
}

.stat-item.rest .stat-value {
  color: #00B42A;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #4e5969;
}

.stats-summary {
  display: flex;
  justify-content: space-around;
  padding: 8px 0;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 13px;
  color: #86909c;
  display: block;
  margin-bottom: 6px;
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
}

.summary-value.highlight {
  color: #165DFF;
}

.stats-month {
  text-align: center;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #e5e6eb;
  font-size: 12px;
  color: #86909c;
}
</style>
