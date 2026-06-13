<template>
  <div class="mobile-checkin">
    <div v-if="loading" class="loading-wrap">
      <a-spin :loading="true" size="32" tip="加载中..." />
    </div>

    <div v-else-if="!drillInfo" class="error-wrap">
      <div class="error-icon"><icon-close-circle /></div>
      <div class="error-title">签到链接无效</div>
      <div class="error-desc">请检查链接是否正确，或联系组织方获取新的签到入口</div>
    </div>

    <div v-else-if="!drillInfo.can_check_in && !checkInSuccess" class="closed-wrap">
      <div class="closed-icon"><icon-lock /></div>
      <div class="closed-title">签到入口已关闭</div>
      <div class="closed-desc">{{ drillInfo.message || '本次演练签到已结束' }}</div>
      <div class="drill-info-mini">
        <div class="info-row"><span class="label">演练名称：</span><span>{{ drillInfo.drill_name }}</span></div>
        <div class="info-row" v-if="drillInfo.location"><span class="label">演练地点：</span><span>{{ drillInfo.location }}</span></div>
      </div>
    </div>

    <template v-else-if="!checkInSuccess">
      <div class="header">
        <div class="header-bg"></div>
        <div class="header-content">
          <div class="badge">
            <icon-safe />
            应急演练签到
          </div>
          <h1 class="drill-title">{{ drillInfo.drill_name }}</h1>
          <div class="drill-meta" v-if="drillInfo.drill_type">
            <a-tag color="arcoblue">{{ drillInfo.drill_type }}</a-tag>
          </div>
        </div>
      </div>

      <div class="info-card">
        <div class="info-card-title">
          <icon-calendar />
          演练信息
        </div>
        <div class="info-list">
          <div class="info-item" v-if="drillInfo.location">
            <div class="info-icon"><icon-placeholder /></div>
            <div class="info-text">
              <div class="info-label">演练地点</div>
              <div class="info-value">{{ drillInfo.location }}</div>
            </div>
          </div>
          <div class="info-item" v-if="drillInfo.start_time">
            <div class="info-icon"><icon-clock-circle /></div>
            <div class="info-text">
              <div class="info-label">开始时间</div>
              <div class="info-value">{{ formatDateTime(drillInfo.start_time) }}</div>
            </div>
          </div>
          <div class="info-item" v-if="drillInfo.end_time">
            <div class="info-icon"><icon-time-circle /></div>
            <div class="info-text">
              <div class="info-label">结束时间</div>
              <div class="info-value">{{ formatDateTime(drillInfo.end_time) }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="form-card">
        <div class="form-card-title">
          <icon-edit />
          请填写签到信息
        </div>

        <a-form ref="formRef" :model="formData" layout="vertical" class="checkin-form">
          <a-form-item
            field="participant_name"
            :rules="[{ required: true, message: '请输入您的姓名' }]"
          >
            <template #label>
              <span class="form-label"><icon-user />&nbsp;姓名 <em>*</em></span>
            </template>
            <a-input
              v-model="formData.participant_name"
              placeholder="请输入您的真实姓名"
              size="large"
              :bordered="false"
              class="form-input"
            />
          </a-form-item>

          <a-form-item
            field="team_name"
            :rules="[{ required: true, message: '请选择或输入所在班组' }]"
          >
            <template #label>
              <span class="form-label"><icon-team />&nbsp;所在班组 <em>*</em></span>
            </template>
            <a-select
              v-if="drillInfo.teams && drillInfo.teams.length > 0"
              v-model="formData.team_name"
              placeholder="请选择您所在的班组"
              size="large"
              :bordered="false"
              allow-create
              allow-clear
              class="form-input"
            >
              <a-option
                v-for="t in drillInfo.teams"
                :key="t.team_name"
                :value="t.team_name"
              >
                {{ t.team_name }}
              </a-option>
            </a-select>
            <a-input
              v-else
              v-model="formData.team_name"
              placeholder="请输入您所在的班组"
              size="large"
              :bordered="false"
              class="form-input"
            />
          </a-form-item>

          <a-form-item field="check_in_code" v-if="!fromLink">
            <template #label>
              <span class="form-label"><icon-protect />&nbsp;签到码</span>
            </template>
            <a-input
              v-model="formData.check_in_code"
              placeholder="如通过链接进入可留空"
              size="large"
              :bordered="false"
              class="form-input"
              :max-length="6"
            />
          </a-form-item>
        </a-form>

        <a-button
          type="primary"
          long
          size="large"
          class="submit-btn"
          :loading="submitting"
          @click="handleSubmit"
        >
          <template #icon v-if="!submitting"><icon-check-circle /></template>
          {{ submitting ? '提交中...' : '确认签到' }}
        </a-button>

        <div class="tips">
          <icon-info-circle />
          <span>请确认信息准确后提交，每人仅可签到一次</span>
        </div>
      </div>

      <div class="footer">
        <div>© 污水处理厂智能管理系统</div>
        <div>安全演练 · 防患未然</div>
      </div>
    </template>

    <div v-else class="success-wrap">
      <div class="success-animation">
        <div class="checkmark-circle">
          <div class="background"></div>
          <div class="checkmark draw"></div>
        </div>
      </div>
      <div class="success-title">签到成功！</div>
      <div class="success-name">{{ formData.participant_name }}</div>
      <div class="success-team">{{ formData.team_name }}</div>

      <div class="success-info">
        <div class="info-row">
          <span class="label">演练名称</span>
          <span class="value">{{ drillInfo.drill_name }}</span>
        </div>
        <div class="info-row" v-if="drillInfo.location">
          <span class="label">演练地点</span>
          <span class="value">{{ drillInfo.location }}</span>
        </div>
        <div class="info-row">
          <span class="label">签到时间</span>
          <span class="value">{{ formatDateTime(successTime) }}</span>
        </div>
      </div>

      <div class="success-tip">
        <icon-check-circle />
        <span>请准时到达演练集合点集合</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { drillApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const loading = ref(true)
const submitting = ref(false)
const drillInfo = ref<any>(null)
const checkInSuccess = ref(false)
const successTime = ref<any>(null)
const formRef = ref()

const token = computed(() => route.params.token as string)
const fromLink = computed(() => !!token.value)

const formData = reactive({
  participant_name: '',
  team_name: '',
  check_in_code: ''
})

const formatDateTime = (val: any) => {
  if (!val) return '-'
  return dayjs(val).format('YYYY-MM-DD HH:mm')
}

const fetchDrillInfo = async () => {
  loading.value = true
  try {
    if (fromLink.value) {
      const res: any = await drillApi.getPublicDrill(token.value)
      drillInfo.value = res.data || res
    } else {
      drillInfo.value = {
        can_check_in: true,
        drill_name: '应急演练签到',
        teams: []
      }
    }
  } catch (e: any) {
    drillInfo.value = null
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  if (!fromLink.value && !formData.check_in_code.trim()) {
    Message.warning('请输入签到码')
    return
  }

  submitting.value = true
  try {
    const payload: any = {
      participant_name: formData.participant_name.trim(),
      team_name: formData.team_name.trim()
    }
    if (fromLink.value) {
      payload.drill_token = token.value
    } else if (formData.check_in_code.trim()) {
      payload.check_in_code = formData.check_in_code.trim()
    }
    await drillApi.checkIn(payload)
    successTime.value = new Date()
    checkInSuccess.value = true
  } catch (e: any) {
    Message.error(e.message || '签到失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

import { computed } from 'vue'

onMounted(() => {
  fetchDrillInfo()
})
</script>

<style scoped>
.mobile-checkin {
  min-height: 100vh;
  background: #f5f7fa;
  max-width: 480px;
  margin: 0 auto;
  position: relative;
  overflow-x: hidden;
  padding-bottom: 40px;
}

.loading-wrap, .error-wrap, .closed-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
}

.error-icon, .closed-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  margin-bottom: 20px;
}

.error-icon {
  background: #fff1f0;
  color: #f5222d;
}

.closed-icon {
  background: #fff7e6;
  color: #fa8c16;
}

.error-title, .closed-title {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 8px;
}

.error-desc, .closed-desc {
  font-size: 14px;
  color: #86909c;
  line-height: 1.6;
  max-width: 280px;
}

.drill-info-mini {
  margin-top: 24px;
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  width: 100%;
  max-width: 320px;
  text-align: left;
}

.drill-info-mini .info-row {
  display: flex;
  padding: 6px 0;
  font-size: 14px;
}

.drill-info-mini .label {
  color: #86909c;
  min-width: 80px;
}

.header {
  position: relative;
  padding: 60px 20px 40px;
  overflow: hidden;
}

.header-bg {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 220px;
  background: linear-gradient(135deg, #165DFF 0%, #0E42D2 50%, #4080FF 100%);
  border-radius: 0 0 36px 36px;
}

.header-content {
  position: relative;
  z-index: 1;
  color: #fff;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(10px);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  margin-bottom: 14px;
}

.drill-title {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.3;
}

.drill-meta :deep(.arco-tag) {
  background: rgba(255,255,255,0.18);
  border-color: rgba(255,255,255,0.3);
  color: #fff;
}

.info-card, .form-card {
  margin: 0 16px 16px;
  background: #fff;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 2px 12px rgba(0, 21, 41, 0.04);
}

.info-card-title, .form-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 12px;
  background: #f7f8fa;
  border-radius: 10px;
}

.info-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e8f3ff, #f0f5ff);
  color: #165DFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.info-text { flex: 1; }

.info-label {
  font-size: 12px;
  color: #86909c;
  margin-bottom: 3px;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
}

.checkin-form {
  margin-top: 4px;
}

.form-label {
  display: inline-flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  color: #4e5969;
}

.form-label em {
  color: #f5222d;
  font-style: normal;
  margin-left: 2px;
}

.form-input {
  background: #f7f8fa;
  border-radius: 10px;
  padding: 0 12px;
}

.submit-btn {
  margin-top: 20px;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.25);
}

.tips {
  margin-top: 14px;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: #86909c;
  padding: 10px 12px;
  background: #fffbe6;
  border-radius: 8px;
}

.tips :deep(.arco-icon) {
  margin-top: 1px;
  flex-shrink: 0;
  color: #fa8c16;
}

.footer {
  text-align: center;
  margin-top: 24px;
  padding: 16px;
  color: #c9cdd4;
  font-size: 12px;
  line-height: 1.8;
}

.success-wrap {
  min-height: 100vh;
  padding: 60px 24px;
  background: linear-gradient(180deg, #f0fff4 0%, #f5f7fa 40%);
  max-width: 480px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.success-animation {
  margin-bottom: 20px;
}

.checkmark-circle {
  width: 96px;
  height: 96px;
  position: relative;
  display: inline-block;
  vertical-align: middle;
}

.checkmark-circle .background {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00B42A 0%, #23C343 100%);
  position: absolute;
  box-shadow: 0 8px 24px rgba(0, 180, 42, 0.25);
}

.checkmark-circle .checkmark {
  border-radius: 5px;
}

.checkmark.draw::after {
  border-radius: 5px;
  animation-delay: 100ms;
  animation-duration: 500ms;
  animation-timing-function: ease;
  animation-name: checkmark;
  transform: scaleX(-1) rotate(135deg);
  transform-origin: left top;
  animation-fill-mode: forwards;
}

.checkmark::after {
  opacity: 1;
  height: 48px;
  width: 24px;
  transform-origin: left top;
  border-right: 4px solid #fff;
  border-top: 4px solid #fff;
  content: '';
  left: 22px;
  top: 48px;
  position: absolute;
}

@keyframes checkmark {
  0% { height: 0; width: 0; opacity: 1; }
  20% { height: 0; width: 24px; opacity: 1; }
  40% { height: 48px; width: 24px; opacity: 1; }
  100% { height: 48px; width: 24px; opacity: 1; }
}

.success-title {
  font-size: 26px;
  font-weight: 700;
  color: #00B42A;
  margin-bottom: 8px;
}

.success-name {
  font-size: 22px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.success-team {
  font-size: 14px;
  color: #86909c;
  margin-bottom: 28px;
}

.success-info {
  width: 100%;
  max-width: 360px;
  background: #fff;
  border-radius: 14px;
  padding: 4px 0;
  box-shadow: 0 2px 12px rgba(0, 21, 41, 0.04);
}

.success-info .info-row {
  display: flex;
  padding: 14px 20px;
  font-size: 14px;
  border-bottom: 1px solid #f2f3f5;
}

.success-info .info-row:last-child {
  border-bottom: none;
}

.success-info .label {
  color: #86909c;
  min-width: 80px;
}

.success-info .value {
  color: #1d2129;
  font-weight: 500;
  flex: 1;
  text-align: right;
}

.success-tip {
  margin-top: 24px;
  padding: 12px 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 10px;
  color: #389e0d;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 360px;
  width: 100%;
}
</style>
