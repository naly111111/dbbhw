<template>
  <div class="categories-container">
    <div class="categories-header">
      <h2>作品库</h2>
      <p>探索海量优质作品</p>
    </div>
    
    <div class="categories-content">
      <!-- 分类筛选 -->
      <div class="category-filters">
        <div class="filter-section">
          <h3>作品分类</h3>
          <div class="category-tags">
            <el-tag 
              v-for="category in categories" 
              :key="category.category_id"
              :type="selectedCategory === category.category_id ? 'primary' : ''"
              @click="selectCategory(category.category_id)"
              class="category-tag"
            >
              {{ category.name }}
            </el-tag>
          </div>
        </div>
        
        <div class="filter-section">
          <h3>作品状态</h3>
          <div class="status-tags">
            <el-tag 
              v-for="status in statusOptions" 
              :key="status.value"
              :type="selectedStatus === status.value ? 'primary' : ''"
              @click="selectStatus(status.value)"
              class="status-tag"
            >
              {{ status.label }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <!-- 作品列表 -->
      <div class="works-section">
        <div class="section-header">
          <h3>{{ getSectionTitle() }}</h3>
          <div class="sort-options">
            <el-select v-model="sortBy" @change="loadWorks" placeholder="排序方式">
              <el-option label="最新创建" value="create_time"></el-option>
              <el-option label="最近更新" value="update_time"></el-option>
              <el-option label="阅读量" value="read_count"></el-option>
              <el-option label="收藏数" value="collect_count"></el-option>
            </el-select>
          </div>
        </div>
        
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="6" animated />
        </div>
        
        <div v-else-if="works.length === 0" class="empty-works">
          <el-empty description="暂无作品">
            <el-button type="primary" @click="resetFilters">
              查看全部作品
            </el-button>
          </el-empty>
        </div>
        
        <div v-else class="works-grid">
          <div 
            v-for="work in works" 
            :key="work.work_id"
            class="work-card"
            @click="goToWorkDetail(work.work_id)"
          >
            <div class="work-cover">
              <img :src="work.cover_url || defaultCover" :alt="work.title">
              <div class="work-status">
                <el-tag 
                  :type="getStatusType(work.status) || 'info'"
                  size="small"
                >
                  {{ getStatusText(work.status) }}
                </el-tag>
              </div>
            </div>
            <div class="work-info">
              <h4 class="work-title">{{ work.title }}</h4>
              <p class="work-author">{{ work.author_name }}</p>
              <p class="work-category">{{ work.category_name }}</p>
              <p class="work-intro">{{ work.intro }}</p>
              <div class="work-stats">
                <span class="stat">
                  <el-icon><View /></el-icon>
                  {{ formatNumber(work.read_count || 0) }}
                </span>
                <span class="stat">
                  <el-icon><Star /></el-icon>
                  {{ formatNumber(work.collect_count || 0) }}
                </span>
              </div>
              <div class="work-meta">
                <span class="create-time">{{ formatTime(work.create_time) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-container" v-if="works.length > 0">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="totalCount"
            @current-change="handlePageChange"
            layout="prev, pager, next, total"
            class="pagination"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { View as ViewIcon, Star } from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'Categories',
  components: {
    ViewIcon,
    Star
  },
  data() {
    return {
      categories: [],
      works: [],
      selectedCategory: '',
      selectedStatus: '',
      sortBy: 'create_time',
      currentPage: 1,
      pageSize: 12,
      totalCount: 0,
      loading: false,
      defaultCover: 'https://via.placeholder.com/200x280/667eea/ffffff?text=封面',
      statusOptions: [
        { label: '全部', value: '' },
        { label: '连载中', value: '1' },
        { label: '已完结', value: '2' }
      ]
    }
  },
  created() {
    this.loadCategories()
    this.loadWorks()
  },
  methods: {
    async loadCategories() {
      try {
        // 模拟分类数据
        this.categories = [
          { category_id: 1, name: '武侠' },
          { category_id: 2, name: '玄幻' },
          { category_id: 3, name: '言情' },
          { category_id: 4, name: '都市' },
          { category_id: 5, name: '历史' },
          { category_id: 6, name: '科幻' },
          { category_id: 7, name: '游戏' },
          { category_id: 8, name: '悬疑' }
        ]
      } catch (error) {
        console.error('Load categories error:', error)
      }
    },
    
    async loadWorks() {
      try {
        this.loading = true
        
        const params = {
          page: this.currentPage,
          page_size: this.pageSize,
          category_id: this.selectedCategory,
          status: this.selectedStatus,
          sort_by: this.sortBy
        }
        
        const response = await api.get('/works/', { params })
        if (response.data.success) {
          const works = Array.isArray(response.data.works) ? response.data.works : []
          this.works = works.map(work => ({
            ...work,
            cover_url: work.cover_url || '',
            intro: work.intro || '',
            author_name: work.author_name || '未知作者',
            category_name: work.category_name || '未分类',
            read_count: Number(work.read_count ?? 0),
            collect_count: Number(work.collect_count ?? 0),
            vote_count: Number(work.vote_count ?? 0)
          }))
          this.totalCount = typeof response.data.total === 'number' ? response.data.total : this.works.length
        }
      } catch (error) {
        this.$message.error('加载作品失败')
        console.error('Load works error:', error)
      } finally {
        this.loading = false
      }
    },
    
    selectCategory(categoryId) {
      this.selectedCategory = this.selectedCategory === categoryId ? '' : categoryId
      this.currentPage = 1
      this.loadWorks()
    },
    
    selectStatus(status) {
      this.selectedStatus = this.selectedStatus === status ? '' : status
      this.currentPage = 1
      this.loadWorks()
    },
    
    handlePageChange(page) {
      this.currentPage = page
      this.loadWorks()
    },
    
    resetFilters() {
      this.selectedCategory = ''
      this.selectedStatus = ''
      this.currentPage = 1
      this.loadWorks()
    },
    
    getSectionTitle() {
      let title = '全部作品'
      
      if (this.selectedCategory) {
        const category = this.categories.find(c => c.category_id === this.selectedCategory)
        if (category) {
          title = category.name + '作品'
        }
      }
      
      if (this.selectedStatus) {
        const status = this.statusOptions.find(s => s.value === this.selectedStatus)
        if (status) {
          title = status.label + title
        }
      }
      
      return title
    },
    
    goToWorkDetail(workId) {
      this.$router.push(`/main/work-detail/${workId}`)
    },
    
    getStatusType(status) {
      const types = {
        0: 'info',    // 草稿
        1: 'success', // 连载中
        2: 'warning', // 完结
        3: 'danger'   // 下架
      }
      return types[status] || 'info'
    },
    
    getStatusText(status) {
      const texts = {
        0: '草稿',
        1: '连载中',
        2: '完结',
        3: '下架'
      }
      return texts[status] || '未知'
    },
    
    formatNumber(num) {
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      }
      return num.toString()
    },
    
    formatTime(timeString) {
      if (!timeString) return ''
      const time = new Date(timeString)
      return time.toLocaleDateString()
    }
  }
}
</script>

<style scoped>
.categories-container {
  height: 100%;
}

.categories-header {
  text-align: center;
  margin-bottom: 30px;
}

.categories-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.categories-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.categories-content {
  display: flex;
  gap: 30px;
  height: calc(100% - 120px);
}

.category-filters {
  width: 250px;
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  height: fit-content;
}

.filter-section {
  margin-bottom: 30px;
}

.filter-section h3 {
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.category-tags,
.status-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.category-tag,
.status-tag {
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-tag:hover,
.status-tag:hover {
  transform: translateY(-2px);
}

.works-section {
  flex: 1;
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.section-header h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0;
}

.loading-container {
  padding: 20px;
}

.empty-works {
  text-align: center;
  padding: 60px 20px;
}

.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.work-card {
  background: #f8f9fa;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.work-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.work-cover {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.work-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.work-status {
  position: absolute;
  top: 10px;
  right: 10px;
}

.work-info {
  padding: 15px;
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

.work-author {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 0 0 5px 0;
}

.work-category {
  color: #bdc3c7;
  font-size: 0.8rem;
  margin: 0 0 10px 0;
}

.work-intro {
  color: #5a6c7d;
  font-size: 0.85rem;
  line-height: 1.4;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.work-stats {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #7f8c8d;
  font-size: 0.85rem;
}

.stat .el-icon {
  color: #667eea;
}

.work-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.create-time {
  color: #bdc3c7;
  font-size: 0.8rem;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.pagination {
  margin: 0;
}

@media (max-width: 768px) {
  .categories-content {
    flex-direction: column;
    gap: 20px;
  }
  
  .category-filters {
    width: 100%;
  }
  
  .works-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
  }
  
  .work-cover {
    height: 150px;
  }
}
</style>

