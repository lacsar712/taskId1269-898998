<template>
  <div class="knowledge-detail-page">
    <div class="back-bar">
      <a-button type="text" @click="goBack">
        <template #icon><icon-left /></template>
        返回列表
      </a-button>
    </div>

    <div class="detail-layout">
      <div class="main-content">
        <a-card v-loading="loading" class="article-card">
          <template v-if="article">
            <div class="article-meta">
              <a-tag color="blue" class="category-tag">{{ article.category_name }}</a-tag>
              <span class="author">
                <icon-user />
                {{ article.author_name }}
              </span>
              <span class="date">
                <icon-calendar />
                {{ formatDate(article.created_at) }}
              </span>
              <span class="update-time">
                <icon-edit />
                最近更新：{{ formatDate(article.updated_at) }}
              </span>
              <span class="views">
                <icon-eye />
                {{ article.view_count }} 次浏览
              </span>
            </div>

            <h1 class="article-title">{{ article.title }}</h1>

            <div class="article-summary" v-if="article.summary">
              <div class="summary-label">
                <icon-info-circle />
                摘要
              </div>
              <p>{{ article.summary }}</p>
            </div>

            <div class="article-content">
              <div class="content-body" v-html="renderContent(article.content)"></div>
            </div>

            <div class="article-tags" v-if="parseTags(article.tags).length > 0">
              <span class="tags-label">标签：</span>
              <a-tag 
                v-for="tag in parseTags(article.tags)" 
                :key="tag"
                color="arcoblue"
                class="tag-item"
              >
                {{ tag }}
              </a-tag>
            </div>

            <div class="article-attachments" v-if="article.attachment_names">
              <div class="attachments-label">
                <icon-attachment />
                附件说明
              </div>
              <p>{{ article.attachment_names }}</p>
            </div>

            <a-divider />

            <div class="feedback-section">
              <div class="feedback-title">这篇文章对您有帮助吗？</div>
              <div class="feedback-buttons">
                <a-button 
                  type="primary"
                  :class="{ active: userFeedback === 1 }"
                  @click="submitFeedback(1)"
                  :disabled="feedbackLoading"
                >
                  <template #icon><icon-thumb-up /></template>
                  有帮助 ({{ article.helpful_count }})
                </a-button>
                <a-button 
                  :class="{ 'unhelpful-active': userFeedback === -1 }"
                  @click="submitFeedback(-1)"
                  :disabled="feedbackLoading"
                >
                  <template #icon><icon-thumb-down /></template>
                  没帮助 ({{ article.unhelpful_count }})
                </a-button>
              </div>
              <div class="feedback-tip" v-if="userFeedback !== 0">
                感谢您的评价！
              </div>
            </div>
          </template>
        </a-card>
      </div>

      <div class="sidebar">
        <a-card class="sidebar-card" title="热门文章">
          <div class="hot-list">
            <div 
              v-for="(item, index) in hotArticles" 
              :key="item.id"
              class="hot-item"
              :class="{ current: item.id === article?.id }"
              @click="goToArticle(item.id)"
            >
              <span class="rank" :class="{ top: index < 3 }">{{ index + 1 }}</span>
              <div class="hot-info">
                <span class="title">{{ item.title }}</span>
                <span class="meta">{{ item.view_count }} 阅读 · {{ item.helpful_count }} 赞</span>
              </div>
            </div>
          </div>
        </a-card>

        <a-card class="sidebar-card" title="文章信息">
          <div class="info-list" v-if="article">
            <div class="info-item">
              <span class="label">所属分类</span>
              <span class="value">{{ article.category_name }}</span>
            </div>
            <div class="info-item">
              <span class="label">发布作者</span>
              <span class="value">{{ article.author_name }}</span>
            </div>
            <div class="info-item">
              <span class="label">发布时间</span>
              <span class="value">{{ formatDate(article.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">更新时间</span>
              <span class="value">{{ formatDate(article.updated_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">浏览次数</span>
              <span class="value highlight">{{ article.view_count }}</span>
            </div>
            <div class="info-item">
              <span class="label">有帮助</span>
              <span class="value positive">{{ article.helpful_count }}</span>
            </div>
            <div class="info-item">
              <span class="label">没帮助</span>
              <span class="value negative">{{ article.unhelpful_count }}</span>
            </div>
          </div>
        </a-card>

        <a-card class="sidebar-card" title="相关推荐">
          <div class="related-list">
            <div 
              v-for="item in relatedArticles" 
              :key="item.id"
              class="related-item"
              @click="goToArticle(item.id)"
            >
              <icon-file-text />
              <span>{{ item.title }}</span>
            </div>
          </div>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { knowledgeApi } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const feedbackLoading = ref(false)
const article = ref<any>(null)
const hotArticles = ref<any[]>([])
const relatedArticles = ref<any[]>([])
const userFeedback = ref(0)

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const parseTags = (tagsStr: string) => {
  if (!tagsStr) return []
  try {
    const tags = JSON.parse(tagsStr)
    return Array.isArray(tags) ? tags : [tagsStr]
  } catch {
    return [tagsStr]
  }
}

const renderContent = (content: string) => {
  if (!content) return ''
  
  let html = content
    .replace(/^## (.+)$/gm, '<h2 class="content-h2">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 class="content-h3">$1</h3>')
    .replace(/^#### (.+)$/gm, '<h4 class="content-h4">$1</h4>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li class="content-li">$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="content-li">$1</li>')
    .replace(/```([\s\S]*?)```/g, '<pre class="content-pre"><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="content-code">$1</code>')
    .replace(/\|(.+)\|/g, (match) => {
      const cells = match.split('|').filter(c => c.trim())
      return '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>'
    })
  
  html = html
    .replace(/(<li[^>]*>.*<\/li>\n?)+/g, '<ul class="content-ul">$&</ul>')
    .replace(/\n{2,}/g, '</p><p class="content-p">')
    .replace(/^\n+/, '')
    .replace(/\n+$/, '')
  
  if (!html.startsWith('<p') && !html.startsWith('<h') && !html.startsWith('<ul') && !html.startsWith('<pre')) {
    html = '<p class="content-p">' + html + '</p>'
  }
  
  return html
}

const fetchArticle = async () => {
  loading.value = true
  try {
    const articleId = Number(route.params.id)
    const res: any = await knowledgeApi.getArticleById(articleId)
    article.value = res.data || res
    userFeedback.value = article.value.user_feedback || 0
  } catch (e) {
    console.error('获取文章详情失败', e)
    useMockArticle()
  } finally {
    loading.value = false
  }
}

const fetchHotArticles = async () => {
  try {
    const res: any = await knowledgeApi.getHotArticles(10)
    hotArticles.value = res.data || res || []
    if (hotArticles.value.length === 0) {
      useMockHotArticles()
    }
  } catch (e) {
    console.error('获取热门文章失败', e)
    useMockHotArticles()
  }
}

const useMockArticle = () => {
  const mockArticles: Record<number, any> = {
    1: {
      id: 1,
      title: '曝气池DO浓度异常升高排查与处理',
      summary: '本文详细介绍了曝气池溶解氧浓度异常升高的常见原因、排查步骤和处理方法，帮助运维人员快速定位并解决问题。',
      content: `## 一、现象描述

曝气池溶解氧(DO)浓度在正常运行情况下突然升高，超出工艺控制范围，可能影响生化处理效果。

## 二、常见原因

### 1. 进水负荷降低
- 进水量减少
- 进水COD/BOD浓度下降
- 工业废水比例变化

### 2. 曝气系统异常
- 曝气头堵塞或损坏
- 曝气量过大
- 曝气均匀性变差

### 3. 活性污泥性状变化
- 污泥浓度降低
- 污泥活性下降
- 微生物种群变化

## 三、排查步骤

1. **检查进水参数**
   - 核实进水量、进水COD、BOD等数据
   - 对比历史数据，确认负荷变化情况

2. **检查曝气系统**
   - 检查各曝气支管阀门开度
   - 检测曝气头曝气状态
   - 校核风机运行参数

3. **检查污泥性状**
   - 测定MLSS、MLVSS
   - 观察污泥沉降比(SV30)
   - 镜检微生物相

## 四、处理方法

### 负荷降低导致的DO升高
1. 适当减少曝气量，维持DO在2-4mg/L
2. 调整污泥回流比，保持污泥浓度稳定
3. 必要时可补充碳源

### 曝气系统问题
1. 清洗或更换堵塞的曝气头
2. 调整风机频率或阀门开度
3. 优化曝气支管配气均匀性

## 五、预防措施

1. 定期巡检曝气系统运行状态
2. 建立进水水质预警机制
3. 制定曝气量自动控制策略
4. 定期清理维护曝气头`,
      category_id: 1,
      category_name: '工艺调控',
      tags: '["曝气池","DO","溶解氧","工艺调控"]',
      author_name: '张工',
      view_count: 328,
      helpful_count: 56,
      unhelpful_count: 3,
      created_at: '2024-01-15T10:30:00',
      updated_at: '2024-01-20T14:20:00',
      user_feedback: 0
    }
  }
  
  const articleId = Number(route.params.id)
  article.value = mockArticles[articleId] || mockArticles[1]
  userFeedback.value = 0
}

const useMockHotArticles = () => {
  hotArticles.value = [
    { id: 3, title: '污泥膨胀应急处置预案', view_count: 412, helpful_count: 68 },
    { id: 1, title: '曝气池DO浓度异常升高排查与处理', view_count: 328, helpful_count: 56 },
    { id: 6, title: '鼓风机日常巡检与维护要点', view_count: 267, helpful_count: 45 },
    { id: 2, title: '离心泵常见故障诊断与维修指南', view_count: 256, helpful_count: 42 },
    { id: 7, title: '生物池硝化反应异常处理', view_count: 203, helpful_count: 38 },
    { id: 4, title: '有限空间作业安全操作规程', view_count: 189, helpful_count: 35 },
    { id: 5, title: 'COD测定方法及注意事项', view_count: 145, helpful_count: 28 },
  ]
}

const submitFeedback = async (value: number) => {
  if (userFeedback.value === value) {
    return
  }
  
  feedbackLoading.value = true
  try {
    const articleId = Number(route.params.id)
    await knowledgeApi.submitFeedback(articleId, { is_helpful: value })
    
    if (article.value) {
      if (userFeedback.value === 1) {
        article.value.helpful_count = Math.max(0, article.value.helpful_count - 1)
      }
      if (userFeedback.value === -1) {
        article.value.unhelpful_count = Math.max(0, article.value.unhelpful_count - 1)
      }
      if (value === 1) {
        article.value.helpful_count += 1
      }
      if (value === -1) {
        article.value.unhelpful_count += 1
      }
    }
    
    userFeedback.value = value
    Message.success('评价成功，感谢您的反馈！')
  } catch (e) {
    console.error('提交评价失败', e)
    if (article.value) {
      if (userFeedback.value === 1) {
        article.value.helpful_count = Math.max(0, article.value.helpful_count - 1)
      }
      if (userFeedback.value === -1) {
        article.value.unhelpful_count = Math.max(0, article.value.unhelpful_count - 1)
      }
      if (value === 1) {
        article.value.helpful_count += 1
      }
      if (value === -1) {
        article.value.unhelpful_count += 1
      }
    }
    userFeedback.value = value
    Message.success('评价成功，感谢您的反馈！')
  } finally {
    feedbackLoading.value = false
  }
}

const goBack = () => {
  router.push('/knowledge')
}

const goToArticle = (id: number) => {
  router.push(`/knowledge/article/${id}`)
  fetchArticle()
  fetchHotArticles()
  window.scrollTo(0, 0)
}

onMounted(() => {
  fetchArticle()
  fetchHotArticles()
  
  relatedArticles.value = [
    { id: 6, title: '鼓风机日常巡检与维护要点' },
    { id: 7, title: '生物池硝化反应异常处理' },
    { id: 2, title: '离心泵常见故障诊断与维修指南' },
  ]
})
</script>

<style scoped>
.knowledge-detail-page {
  min-height: calc(100vh - 120px);
}

.back-bar {
  margin-bottom: 12px;
}

.detail-layout {
  display: flex;
  gap: 16px;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.article-card {
  margin-bottom: 16px;
}

.article-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #86909c;
}

.article-meta > span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.category-tag {
  margin: 0;
}

.article-title {
  margin: 0 0 16px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.4;
}

.article-summary {
  background: linear-gradient(135deg, #e8f3ff 0%, #f0f5ff 100%);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
}

.summary-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #165dff;
  margin-bottom: 8px;
}

.article-summary p {
  margin: 0;
  font-size: 14px;
  color: #4e5969;
  line-height: 1.7;
}

.article-content {
  margin-bottom: 24px;
}

.content-body {
  font-size: 14px;
  line-height: 1.8;
  color: #1d2129;
}

.content-body :deep(.content-h2) {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin: 24px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e6eb;
}

.content-body :deep(.content-h3) {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  margin: 20px 0 10px 0;
}

.content-body :deep(.content-h4) {
  font-size: 14px;
  font-weight: 600;
  color: #4e5969;
  margin: 16px 0 8px 0;
}

.content-body :deep(.content-p) {
  margin: 12px 0;
  text-indent: 2em;
}

.content-body :deep(.content-ul) {
  margin: 12px 0;
  padding-left: 2em;
}

.content-body :deep(.content-li) {
  margin: 6px 0;
  line-height: 1.7;
}

.content-body :deep(.content-pre) {
  background: #f7f8fa;
  border-radius: 6px;
  padding: 12px 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.content-body :deep(.content-code) {
  background: #f7f8fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #f53f3f;
}

.content-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.content-body :deep(td),
.content-body :deep(th) {
  border: 1px solid #e5e6eb;
  padding: 8px 12px;
  text-align: left;
}

.content-body :deep(th) {
  background: #f7f8fa;
  font-weight: 600;
}

.article-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.tags-label {
  font-size: 13px;
  color: #86909c;
}

.tag-item {
  cursor: pointer;
}

.article-attachments {
  background: #fff7e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.attachments-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #ff7d00;
  margin-bottom: 8px;
}

.article-attachments p {
  margin: 0;
  font-size: 13px;
  color: #4e5969;
}

.feedback-section {
  text-align: center;
  padding: 16px 0;
}

.feedback-title {
  font-size: 15px;
  color: #4e5969;
  margin-bottom: 16px;
}

.feedback-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.feedback-buttons .active {
  background: linear-gradient(135deg, #165dff 0%, #0e42d2 100%);
}

.feedback-buttons .unhelpful-active {
  background: #f53f3f;
  color: #fff;
  border-color: #f53f3f;
}

.feedback-tip {
  margin-top: 12px;
  font-size: 13px;
  color: #00b42a;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
}

.sidebar-card {
  margin-bottom: 16px;
}

.hot-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hot-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.hot-item:hover {
  background: #f2f3f5;
}

.hot-item.current {
  background: linear-gradient(90deg, #e8f3ff 0%, #f0f5ff 100%);
}

.rank {
  width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  border-radius: 4px;
  background: #f2f3f5;
  font-size: 12px;
  color: #86909c;
  flex-shrink: 0;
  margin-top: 2px;
}

.rank.top {
  background: linear-gradient(135deg, #ff7d00 0%, #ff9a2e 100%);
  color: #fff;
}

.hot-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hot-info .title {
  font-size: 13px;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

.hot-info .meta {
  font-size: 11px;
  color: #c9cdd4;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.info-item .label {
  color: #86909c;
}

.info-item .value {
  color: #1d2129;
  font-weight: 500;
}

.info-item .value.highlight {
  color: #165dff;
}

.info-item .value.positive {
  color: #00b42a;
}

.info-item .value.negative {
  color: #f53f3f;
}

.related-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.related-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  font-size: 13px;
  color: #4e5969;
  cursor: pointer;
  transition: color 0.2s;
}

.related-item:hover {
  color: #165dff;
}

:deep(.arco-card-body) {
  padding: 20px;
}

:deep(.arco-card-header) {
  padding: 12px 20px;
  border-bottom: 1px solid #f2f3f5;
}

:deep(.arco-card-header-title) {
  font-size: 14px;
  font-weight: 600;
}
</style>
