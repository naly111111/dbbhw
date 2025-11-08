<template>
  <div class="search-container">
    <div class="search-header">
      <h2>搜索作品</h2>
      <p>发现更多精彩内容</p>
    </div>
    
    <div class="search-history" v-if="searchHistory.length">
      <div class="history-header">
        <el-icon class="history-icon"><Clock /></el-icon>
        <span class="history-title">最近搜索</span>
      </div>
      <div class="history-tags">
        <el-tag
          v-for="record in searchHistory"
          :key="record.keyword"
          class="history-tag"
          size="large"
          effect="plain"
          @click="handleHistoryClick(record.keyword)"
        >
          {{ record.keyword }}
        </el-tag>
      </div>
    </div>

    <div class="search-form">
      <el-form :model="searchForm" @submit.prevent="handleSearch">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关键词">
              <el-input
                v-model="searchForm.keyword"
                placeholder="输入作品名称、作者名或关键词"
                size="large"
                clearable
              >
                <template #prefix>
                  <el-icon><SearchIcon /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="分类">
              <el-select v-model="searchForm.category_id" placeholder="全部分类" size="large" clearable>
                <el-option label="全部分类" value=""></el-option>
                <el-option 
                  v-for="category in categories" 
                  :key="category.category_id"
                  :label="category.name"
                  :value="String(category.category_id)"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="作者">
              <el-input
                v-model="searchForm.author_name"
                placeholder="作者笔名"
                size="large"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="作品状态">
              <el-select v-model="searchForm.status" placeholder="全部状态" size="large">
                <el-option
                  v-for="option in statusOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="作品字数 (字)">
              <div class="word-count-range">
                <el-input
                  v-model="searchForm.word_count_min"
                  type="number"
                  placeholder="最小字数"
                  size="large"
                  clearable
                  min="0"
                />
                <span class="word-count-separator">—</span>
                <el-input
                  v-model="searchForm.word_count_max"
                  type="number"
                  placeholder="最大字数"
                  size="large"
                  clearable
                  min="0"
                />
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item class="form-actions">
          <el-button 
            type="primary" 
            size="large" 
            native-type="submit"
            @click="handleSearch"
            :loading="loading"
            class="search-button"
          >
            <el-icon><SearchIcon /></el-icon>
            搜索
          </el-button>
          <el-button 
            size="large" 
            @click="resetSearch"
            class="reset-button"
          >
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <div class="search-results" v-if="hasSearched">
      <div class="results-header">
        <h3>搜索结果</h3>
        <span class="results-count">共找到 {{ totalResults }} 个结果</span>
      </div>
      <div v-if="loading" class="results-loading">
        <el-skeleton animated :rows="4" />
      </div>

      <template v-else>
        <div v-if="results.length === 0" class="no-results">
          <el-empty description="没有找到相关作品">
            <el-button type="primary" @click="resetSearch">
              重新搜索
            </el-button>
          </el-empty>
        </div>
        
        <div v-else class="results-grid">
          <div 
            v-for="work in results" 
            :key="work.work_id"
            class="result-card"
            @click="goToWorkDetail(work.work_id)"
          >
            <div class="work-cover">
              <img :src="work.cover_url || defaultCover" :alt="work.title">
            </div>
            <div class="work-info">
              <h4 class="work-title">{{ work.title }}</h4>
              <div class="work-brief">
                <span class="work-author">{{ work.author_name || '未知作者' }}</span>
                <span class="separator">·</span>
                <span class="work-category">{{ work.category_name || '未分类' }}</span>
              </div>
              <div class="work-meta">
                <el-tag size="small" :type="getStatusTagType(work.status)">
                  {{ getStatusText(work.status) }}
                </el-tag>
                <span class="meta-item">字数：{{ formatWordCount(work.word_count) }}</span>
                <span class="meta-item">阅读：{{ formatNumber(work.read_count) }}</span>
                <span class="meta-item">收藏：{{ formatNumber(work.collect_count) }}</span>
                <span class="meta-item">投票：{{ formatNumber(work.vote_count) }}</span>
              </div>
              <p class="work-intro">{{ work.intro }}</p>
              <div class="work-meta secondary">
                <span class="meta-item">创建：{{ formatTime(work.create_time) }}</span>
                <span class="meta-item">更新：{{ formatTime(work.update_time) }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { Search as SearchIcon, Clock } from '@element-plus/icons-vue'
import { getCategories, searchWorks, getSearchHistory } from '@/api'

const STATUS_TEXT = {
  0: '草稿',
  1: '连载中',
  2: '完结',
  3: '下架'
}

const STATUS_TAG = {
  0: 'info',
  1: 'success',
  2: 'warning',
  3: 'danger'
}

export default {
  name: 'Search',
  components: {
    SearchIcon,
    Clock
  },
  data() {
    return {
      searchForm: {
        keyword: '',
        category_id: '',
        author_name: '',
        status: 'all',
        word_count_min: '',
        word_count_max: ''
      },
      categories: [],
      statusOptions: [
        { label: '全部状态', value: 'all' },
        { label: '草稿', value: '0' },
        { label: '连载中', value: '1' },
        { label: '完结', value: '2' },
        { label: '下架', value: '3' }
      ],
      results: [],
      totalResults: 0,
      loading: false,
      hasSearched: false,
      defaultCover: 'https://via.placeholder.com/120x160/667eea/ffffff?text=封面',
      currentPage: 1,
      pageSize: 20,
      searchHistory: []
    }
  },
  created() {
    this.loadCategories()
    this.loadSearchHistory()
  },
  watch: {
    '$route.query': {
      handler(newQuery) {
        this.applyQueryToForm(newQuery)
        if (this.hasActiveFilters(newQuery)) {
          this.performSearch()
        } else {
          this.loading = false
          this.hasSearched = false
          this.results = []
          this.totalResults = 0
        }
      },
      immediate: true
    }
  },
  methods: {
    async loadCategories() {
      try {
        const response = await getCategories()
        if (response.data && response.data.success) {
          this.categories = response.data.categories || []
        }
      } catch (error) {
        console.error('Load categories error:', error)
      }
    },

    async loadSearchHistory() {
      try {
        const response = await getSearchHistory({ limit: 20 })
        if (response.data && response.data.success) {
          this.searchHistory = response.data.history || []
        }
      } catch (error) {
        if (error?.response?.status !== 401) {
          console.error('Load search history error:', error)
        }
      }
    },

    applyQueryToForm(query = {}) {
      this.searchForm.keyword = query.keyword || ''
      this.searchForm.category_id = query.category_id !== undefined ? String(query.category_id) : ''
      this.searchForm.author_name = query.author_name || ''
      this.searchForm.status = query.status && query.status !== 'all' ? String(query.status) : 'all'
      this.searchForm.word_count_min = query.word_count_min !== undefined ? String(query.word_count_min) : ''
      this.searchForm.word_count_max = query.word_count_max !== undefined ? String(query.word_count_max) : ''
      this.currentPage = query.page ? Math.max(parseInt(query.page, 10) || 1, 1) : 1
      if (query.page_size) {
        const size = parseInt(query.page_size, 10)
        if (!Number.isNaN(size) && size > 0) {
          this.pageSize = Math.min(size, 100)
        }
      }
    },

    hasActiveFilters(query = {}) {
      const relevantKeys = ['keyword', 'category_id', 'author_name', 'status', 'word_count_min', 'word_count_max']
      return relevantKeys.some((key) => {
        const value = query[key]
        if (value === undefined || value === null) return false
        if (key === 'status') {
          return value !== '' && value !== 'all'
        }
        return String(value).trim() !== ''
      })
    },

    getRelevantQuery(query = {}) {
      const keys = ['keyword', 'category_id', 'author_name', 'status', 'word_count_min', 'word_count_max']
      const result = {}
      keys.forEach((key) => {
        if (query[key] !== undefined) {
          result[key] = String(query[key])
        }
      })
      return result
    },

    parseWordInput(value) {
      if (value === '' || value === null || value === undefined) return null
      const num = Number(value)
      if (!Number.isFinite(num) || num < 0) {
        return NaN
      }
      return Math.floor(num)
    },

    buildRouteQuery(minOverride, maxOverride) {
      const query = {}
      const keyword = (this.searchForm.keyword || '').trim()
      const author = (this.searchForm.author_name || '').trim()

      if (keyword) {
        query.keyword = keyword
      }

      if (this.searchForm.category_id) {
        query.category_id = this.searchForm.category_id
      }

      if (author) {
        query.author_name = author
      }

      if (this.searchForm.status && this.searchForm.status !== 'all') {
        query.status = this.searchForm.status
      }

      const min = minOverride !== undefined ? minOverride : this.parseWordInput(this.searchForm.word_count_min)
      if (min !== null && !Number.isNaN(min)) {
        query.word_count_min = String(min)
      }

      const max = maxOverride !== undefined ? maxOverride : this.parseWordInput(this.searchForm.word_count_max)
      if (max !== null && !Number.isNaN(max)) {
        query.word_count_max = String(max)
      }

      if (this.currentPage > 1) {
        query.page = String(this.currentPage)
      }

      if (this.pageSize !== 20) {
        query.page_size = String(this.pageSize)
      }

      return query
    },

    buildApiParams(min, max) {
      const params = {
        page: this.currentPage,
        page_size: this.pageSize
      }

      const keyword = (this.searchForm.keyword || '').trim()
      if (keyword) {
        params.keyword = keyword
      }

      if (this.searchForm.category_id) {
        const categoryValue = Number(this.searchForm.category_id)
        params.category_id = Number.isNaN(categoryValue) ? this.searchForm.category_id : categoryValue
      }

      const author = (this.searchForm.author_name || '').trim()
      if (author) {
        params.author_name = author
      }

      if (this.searchForm.status && this.searchForm.status !== 'all') {
        const statusValue = Number(this.searchForm.status)
        params.status = Number.isNaN(statusValue) ? this.searchForm.status : statusValue
      }

      if (min !== null && !Number.isNaN(min)) {
        params.word_count_min = min
      }

      if (max !== null && !Number.isNaN(max)) {
        params.word_count_max = max
      }

      return params
    },

    isSameQuery(newQuery, currentQuery) {
      const normalize = (obj) => {
        const entries = Object.entries(obj).map(([key, value]) => [key, String(value)])
        entries.sort((a, b) => a[0].localeCompare(b[0]))
        return JSON.stringify(entries)
      }

      return normalize(newQuery) === normalize(currentQuery)
    },

    async handleSearch() {
      const min = this.parseWordInput(this.searchForm.word_count_min)
      const max = this.parseWordInput(this.searchForm.word_count_max)

      if (Number.isNaN(min) || Number.isNaN(max)) {
        this.$message.warning('请输入有效的字数范围')
        return
      }

      if (min !== null && max !== null && min > max) {
        this.$message.warning('最小字数不能大于最大字数')
        return
      }

      this.currentPage = 1

      const routeQuery = this.buildRouteQuery(min, max)
      const currentQuery = this.getRelevantQuery(this.$route.query)

      if (Object.keys(routeQuery).length === 0) {
        if (Object.keys(currentQuery).length === 0) {
          this.resetFormFields()
          this.loading = false
          this.hasSearched = false
          this.results = []
          this.totalResults = 0
        } else {
          this.$router.replace({ path: '/main/search' })
        }
        return
      }

      if (this.isSameQuery(routeQuery, currentQuery)) {
        this.performSearch()
        return
      }

      this.$router.replace({ path: '/main/search', query: routeQuery })
    },

    async performSearch() {
      const min = this.parseWordInput(this.searchForm.word_count_min)
      const max = this.parseWordInput(this.searchForm.word_count_max)

      if (Number.isNaN(min) || Number.isNaN(max)) {
        this.$message.warning('请输入有效的字数范围')
        return
      }

      if (min !== null && max !== null && min > max) {
        this.$message.warning('最小字数不能大于最大字数')
        return
      }

      const params = this.buildApiParams(min, max)

      try {
        this.loading = true
        const response = await searchWorks(params)
        if (response.data && response.data.success) {
          this.results = response.data.results || []
          this.totalResults = response.data.total || this.results.length
          this.hasSearched = true
          this.loadSearchHistory()
        } else {
          this.results = []
          this.totalResults = 0
          this.hasSearched = true
          this.$message.error(response.data?.error || '搜索失败')
        }
      } catch (error) {
        this.results = []
        this.totalResults = 0
        this.hasSearched = true
        this.$message.error('搜索失败，请稍后重试')
        console.error('Search error:', error)
      } finally {
        this.loading = false
      }
    },

    resetFormFields() {
      this.searchForm.keyword = ''
      this.searchForm.category_id = ''
      this.searchForm.author_name = ''
      this.searchForm.status = 'all'
      this.searchForm.word_count_min = ''
      this.searchForm.word_count_max = ''
      this.currentPage = 1
      this.pageSize = 20
    },

    resetSearch() {
      this.resetFormFields()
      this.$router.replace({ path: '/main/search' })
    },

    goToWorkDetail(workId) {
      this.$router.push(`/main/work-detail/${workId}`)
    },

    handleHistoryClick(keyword) {
      if (!keyword) return
      this.searchForm.keyword = keyword
      this.searchForm.author_name = ''
      this.currentPage = 1
      this.handleSearch()
    },

    formatTime(timeString) {
      if (!timeString) return ''
      const time = new Date(timeString)
      if (Number.isNaN(time.getTime())) return ''
      return time.toLocaleDateString()
    },

    formatWordCount(value) {
      const num = Number(value) || 0
      if (num >= 10000) {
        return `${(num / 10000).toFixed(1)}万字`
      }
      return `${num}字`
    },

    getStatusText(status) {
      return STATUS_TEXT[status] || '未知状态'
    },

    getStatusTagType(status) {
      return STATUS_TAG[status] || 'info'
    },

    formatNumber(num) {
      const value = Number(num) || 0
      if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万'
      }
      return value.toString()
    }
  }
}
</script>

<style scoped>
.search-container {
  height: 100%;
}

.search-header {
  text-align: center;
  margin-bottom: 30px;
}

.search-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.search-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.search-history {
  background: white;
  border-radius: 15px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #475569;
  font-weight: 600;
}

.history-icon {
  color: #6366f1;
}

.history-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.history-tag {
  cursor: pointer;
  border-radius: 999px;
  color: #4c1d95;
  background: #ede9fe;
  border-color: #c4b5fd;
  transition: all 0.2s ease;
}

.history-tag:hover {
  background: #c7d2fe;
  border-color: #818cf8;
  color: #312e81;
}

.search-form {
  background: white;
  border-radius: 15px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.word-count-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.word-count-range .el-input {
  flex: 1;
}

.word-count-separator {
  color: #94a3b8;
  font-size: 1.1rem;
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.search-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 12px 30px;
  margin-right: 15px;
}

.reset-button {
  border-radius: 8px;
  padding: 12px 30px;
}

.search-results {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.results-header h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0;
}

.results-count {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.results-loading {
  padding: 40px 0;
}

.no-results {
  text-align: center;
  padding: 60px 20px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.result-card {
  display: flex;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.result-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  background: white;
}

.work-cover {
  width: 80px;
  height: 110px;
  margin-right: 20px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.work-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.work-info {
  flex: 1;
}

.work-title {
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.work-brief {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.work-author {
  color: inherit;
  margin: 0;
}

.separator {
  color: #cbd5e1;
}

.work-category {
  color: inherit;
}

.work-intro {
  color: #5a6c7d;
  font-size: 0.85rem;
  line-height: 1.4;
  margin: 0 0 10px 0;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.work-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.work-meta.secondary {
  margin-top: 6px;
}

.meta-item {
  font-size: 0.8rem;
  color: #94a3b8;
}

.work-meta.secondary .meta-item {
  color: #a0aec0;
}

@media (max-width: 768px) {
  .search-form {
    padding: 20px;
  }
  
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .result-card {
    flex-direction: column;
    text-align: center;
  }
  
  .work-cover {
    width: 100%;
    height: 200px;
    margin-right: 0;
    margin-bottom: 15px;
  }
}
</style>

