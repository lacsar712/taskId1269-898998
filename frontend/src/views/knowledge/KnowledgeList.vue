<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h2>运维知识库</h2>
      <p>沉淀运维经验 / 传承专业技能 / 提升团队能力</p>
    </div>

    <div class="knowledge-layout">
      <div class="sidebar">
        <a-card class="category-card" title="分类目录">
          <div class="category-list">
            <div 
              class="category-item" 
              :class="{ active: !selectedCategoryId }"
              @click="handleCategoryClick(null)"
            >
              <icon-book />
              <span>全部文章</span>
              <span class="count">{{ totalCount }}</span>
            </div>
            <div 
              v-for="cat in categories" 
              :key="cat.id"
              class="category-item"
              :class="{ active: selectedCategoryId === cat.id }"
              @click="handleCategoryClick(cat.id)"
            >
              <component :is="getCategoryIcon(cat.code)" />
              <span>{{ cat.name }}</span>
              <span class="count">{{ getCategoryCount(cat.id) }}</span>
            </div>
          </div>
        </a-card>

        <a-card class="hot-card" title="热门文章">
          <div class="hot-list">
            <div 
              v-for="(item, index) in hotArticles" 
              :key="item.id"
              class="hot-item"
              @click="goToDetail(item.id)"
            >
              <span class="rank" :class="{ top: index < 3 }">{{ index + 1 }}</span>
              <span class="title">{{ item.title }}</span>
              <span class="views">{{ item.view_count }} 阅读</span>
            </div>
          </div>
        </a-card>
      </div>

      <div class="main-content">
        <a-card class="search-card">
          <a-input 
            v-model="searchKeyword" 
            placeholder="搜索文章标题、摘要或内容..."
            size="large"
            @press-enter="handleSearch"
          >
            <template #prefix>
              <icon-search />
            </template>
          </a-input>
          <div class="search-tags">
            <span class="tag-label">热门标签：</span>
            <a-tag 
              v-for="tag in hotTags" 
              :key="tag"
              color="blue"
              class="tag-item"
              @click="handleTagClick(tag)"
            >
              {{ tag }}
            </a-tag>
          </div>
        </a-card>

        <div class="sort-bar">
          <a-space>
            <span>找到 {{ pagination.total }} 篇文章</span>
            <a-radio-group v-model="sortBy" size="small" @change="handleSortChange">
              <a-radio value="latest">最新发布</a-radio>
              <a-radio value="hot">最多浏览</a-radio>
              <a-radio value="helpful">最有帮助</a-radio>
            </a-radio-group>
          </a-space>
        </div>

        <div class="article-list" v-loading="loading">
          <a-empty v-if="!loading && articles.length === 0" description="暂无相关文章" />
          
          <a-card 
            v-for="article in articles" 
            :key="article.id"
            class="article-card"
            hoverable
            @click="goToDetail(article.id)"
          >
            <div class="article-header">
              <a-tag color="blue" class="category-tag">{{ article.category_name }}</a-tag>
              <span class="author">{{ article.author_name }}</span>
              <span class="date">{{ formatDate(article.updated_at) }}</span>
            </div>
            <h3 class="article-title">{{ article.title }}</h3>
            <p class="article-summary">{{ article.summary }}</p>
            <div class="article-footer">
              <div class="tags">
                <a-tag 
                  v-for="tag in parseTags(article.tags)" 
                  :key="tag"
                  size="small"
                >
                  {{ tag }}
                </a-tag>
              </div>
              <div class="stats">
                <span class="stat-item">
                  <icon-eye />
                  {{ article.view_count }}
                </span>
                <span class="stat-item">
                  <icon-thumb-up />
                  {{ article.helpful_count }}
                </span>
              </div>
            </div>
          </a-card>
        </div>

        <div class="pagination" v-if="pagination.total > 0">
          <a-pagination 
            v-model:current="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            @change="handlePageChange"
            show-total
            show-page-size
            :page-size-options="[10, 20, 50]"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { knowledgeApi } from '@/api'

const router = useRouter()
const loading = ref(false)
const searchKeyword = ref('')
const selectedCategoryId = ref<number | null>(null)
const sortBy = ref('latest')
const categories = ref<any[]>([])
const articles = ref<any[]>([])
const hotArticles = ref<any[]>([])
const hotTags = ref<string[]>([])
const totalCount = ref(0)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const categoryCountMap = ref<Record<number, number>>({})

const getCategoryIcon = (code: string) => {
  const iconMap: Record<string, string> = {
    'PROCESS': 'icon-settings',
    'EQUIPMENT': 'icon-computer',
    'FAULT': 'icon-exclamation-circle',
    'EMERGENCY': 'icon-safe',
    'SAFETY': 'icon-lock',
    'LAB': 'icon-experiment'
  }
  return iconMap[code] || 'icon-file'
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

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const getCategoryCount = (catId: number) => {
  return categoryCountMap.value[catId] || 0
}

const fetchCategories = async () => {
  try {
    const res: any = await knowledgeApi.getCategories()
    categories.value = res.data || res || []
  } catch (e) {
    console.error('获取分类失败', e)
  }
}

const fetchArticles = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
      sort_by: sortBy.value
    }
    if (selectedCategoryId.value) {
      params.category_id = selectedCategoryId.value
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    const res: any = await knowledgeApi.getArticles(params)
    const data = res.data || res
    articles.value = data.items || []
    pagination.total = data.total || 0
    totalCount.value = data.total || 0
  } catch (e) {
    console.error('获取文章列表失败', e)
    useMockData()
  } finally {
    loading.value = false
  }
}

const fetchHotArticles = async () => {
  try {
    const res: any = await knowledgeApi.getHotArticles(10)
    hotArticles.value = res.data || res || []
  } catch (e) {
    console.error('获取热门文章失败', e)
  }
}

const fetchTags = async () => {
  try {
    const res: any = await knowledgeApi.getTags()
    const tags = res.data || res || []
    hotTags.value = tags.slice(0, 8)
  } catch (e) {
    console.error('获取标签失败', e)
    hotTags.value = ['曝气池', '离心泵', '污泥膨胀', 'COD', 'DO', '有限空间', '鼓风机', '硝化反应']
  }
}

const useMockData = () => {
  const mockArticles = [
    { id: 1, title: '曝气池DO浓度异常升高排查与处理', summary: '本文详细介绍了曝气池溶解氧浓度异常升高的常见原因、排查步骤和处理方法，帮助运维人员快速定位并解决问题。', category_id: 1, category_name: '工艺调控', tags: '["曝气池","DO","溶解氧","工艺调控"]', author_name: '张工', view_count: 328, helpful_count: 56, updated_at: '2024-01-15T10:30:00' },
    { id: 2, title: '离心泵常见故障诊断与维修指南', summary: '总结了污水处理厂离心泵在运行中常见的故障类型、产生原因及对应的维修处理方法，适用于各类水泵的日常维护。', category_id: 2, category_name: '设备操作', tags: '["离心泵","设备维护","故障维修"]', author_name: '李工', view_count: 256, helpful_count: 42, updated_at: '2024-01-14T14:20:00' },
    { id: 3, title: '污泥膨胀应急处置预案', summary: '针对活性污泥法运行中可能出现的污泥膨胀问题，制定详细的应急响应流程和处置措施，确保工艺安全稳定运行。', category_id: 4, category_name: '应急预案', tags: '["污泥膨胀","应急预案","活性污泥"]', author_name: '王工', view_count: 412, helpful_count: 68, updated_at: '2024-01-13T09:15:00' },
    { id: 4, title: '有限空间作业安全操作规程', summary: '规范污水处理厂有限空间作业的安全管理，明确作业程序、防护要求和应急措施，防止中毒、窒息等安全事故发生。', category_id: 5, category_name: '安全规范', tags: '["有限空间","安全作业","操作规程"]', author_name: '赵工', view_count: 189, helpful_count: 35, updated_at: '2024-01-12T11:45:00' },
    { id: 5, title: 'COD测定方法及注意事项', summary: '详细介绍化学需氧量(COD)的测定原理、操作步骤、试剂配制和质量控制要求，帮助化验人员准确开展水质检测工作。', category_id: 6, category_name: '化验检测', tags: '["COD","化验检测","水质分析"]', author_name: '刘工', view_count: 145, helpful_count: 28, updated_at: '2024-01-11T16:30:00' },
    { id: 6, title: '鼓风机日常巡检与维护要点', summary: '介绍污水处理厂鼓风机的日常巡检内容、维护保养周期和常见问题处理，确保曝气系统稳定可靠运行。', category_id: 2, category_name: '设备操作', tags: '["鼓风机","设备巡检","维护保养"]', author_name: '陈工', view_count: 267, helpful_count: 45, updated_at: '2024-01-10T13:20:00' },
    { id: 7, title: '生物池硝化反应异常处理', summary: '分析生物池硝化效果下降的常见原因，提供系统性的排查思路和处理措施，保障出水氨氮达标排放。', category_id: 1, category_name: '工艺调控', tags: '["硝化反应","氨氮","生物处理","工艺调控"]', author_name: '孙工', view_count: 203, helpful_count: 38, updated_at: '2024-01-09T10:00:00' },
  ]
  
  let filtered = mockArticles
  if (selectedCategoryId.value) {
    filtered = filtered.filter(a => a.category_id === selectedCategoryId.value)
  }
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(a => 
      a.title.toLowerCase().includes(keyword) || 
      a.summary.toLowerCase().includes(keyword)
    )
  }
  
  if (sortBy.value === 'hot') {
    filtered.sort((a, b) => b.view_count - a.view_count)
  } else if (sortBy.value === 'helpful') {
    filtered.sort((a, b) => b.helpful_count - a.helpful_count)
  }
  
  const start = (pagination.page - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  articles.value = filtered.slice(start, end)
  pagination.total = filtered.length
  totalCount.value = mockArticles.length
  
  categoryCountMap.value = mockArticles.reduce((acc: Record<number, number>, article) => {
    acc[article.category_id] = (acc[article.category_id] || 0) + 1
    return acc
  }, {})
  
  hotArticles.value = [...mockArticles].sort((a, b) => b.view_count - a.view_count).slice(0, 10)
}

const handleCategoryClick = (catId: number | null) => {
  selectedCategoryId.value = catId
  pagination.page = 1
  fetchArticles()
}

const handleSearch = () => {
  pagination.page = 1
  fetchArticles()
}

const handleTagClick = (tag: string) => {
  searchKeyword.value = tag
  handleSearch()
}

const handleSortChange = () => {
  pagination.page = 1
  fetchArticles()
}

const handlePageChange = () => {
  fetchArticles()
}

const goToDetail = (id: number) => {
  router.push(`/knowledge/article/${id}`)
}

onMounted(() => {
  fetchCategories()
  fetchArticles()
  fetchHotArticles()
  fetchTags()
})
</script>

<style scoped>
.knowledge-page {
  min-height: calc(100vh - 120px);
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

.knowledge-layout {
  display: flex;
  gap: 16px;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
}

.category-card {
  margin-bottom: 16px;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #4e5969;
}

.category-item:hover {
  background: #f2f3f5;
}

.category-item.active {
  background: linear-gradient(90deg, #e8f3ff 0%, #f0f5ff 100%);
  color: #165dff;
  font-weight: 500;
}

.category-item .count {
  margin-left: auto;
  font-size: 12px;
  color: #86909c;
}

.category-item.active .count {
  color: #165dff;
}

.hot-card .hot-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  cursor: pointer;
  transition: color 0.2s;
  font-size: 13px;
  color: #4e5969;
}

.hot-item:hover {
  color: #165dff;
}

.rank {
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 4px;
  background: #f2f3f5;
  font-size: 12px;
  color: #86909c;
  flex-shrink: 0;
}

.rank.top {
  background: linear-gradient(135deg, #ff7d00 0%, #ff9a2e 100%);
  color: #fff;
}

.hot-item .title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-item .views {
  font-size: 12px;
  color: #c9cdd4;
  flex-shrink: 0;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.search-card {
  margin-bottom: 16px;
}

.search-tags {
  margin-top: 12px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-label {
  font-size: 13px;
  color: #86909c;
}

.tag-item {
  cursor: pointer;
  transition: all 0.2s;
}

.tag-item:hover {
  opacity: 0.8;
}

.sort-bar {
  margin-bottom: 12px;
  font-size: 13px;
  color: #86909c;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-card {
  cursor: pointer;
  transition: all 0.3s;
}

.article-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.article-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #86909c;
}

.category-tag {
  margin: 0;
}

.article-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.4;
}

.article-summary {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #4e5969;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #86909c;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

:deep(.arco-card-body) {
  padding: 16px;
}

:deep(.arco-card-header) {
  padding: 12px 16px;
  border-bottom: 1px solid #f2f3f5;
}

:deep(.arco-card-header-title) {
  font-size: 14px;
  font-weight: 600;
}
</style>
