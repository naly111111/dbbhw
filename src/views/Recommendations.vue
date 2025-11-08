<template>
  <div class="recommendations-container">
    <div class="recommendations-header">
      <h2>为你推荐</h2>
      <p class="subtitle">
        {{ isPersonalized ? '基于你的阅读偏好，为你精选优质作品' : '当前热门作品推荐，完成阅读或收藏后即可获得专属推荐' }}
      </p>
    </div>
    
    <div class="recommendations-content">
      <!-- 推荐分类 -->
      <div class="recommendation-sections">
        <div class="section">
          <div class="section-header">
            <h3>
              <el-icon><Star /></el-icon>
              {{ isPersonalized ? '最喜欢的类型' : '精选热门作品' }}
            </h3>
            <p>
              {{ favoriteSectionSubtitle }}
            </p>
            <div 
              v-if="hasPreferenceMeta"
              class="preference-meta"
            >
              <div class="meta-row meta-row-inline">
                <span class="meta-label">偏好类别</span>
                <template v-if="preferenceMeta.top_categories && preferenceMeta.top_categories.length">
                  <el-tag
                    v-for="category in preferenceMeta.top_categories"
                    :key="category.category_id || category.name"
                    size="small"
                    class="meta-tag"
                  >
                    {{ category.name || '未分类' }}
                  </el-tag>
                </template>
                <span
                  v-if="preferenceMeta.top_tags && preferenceMeta.top_tags.length"
                  class="meta-label meta-label-secondary"
                >偏好标签</span>
                <template v-if="preferenceMeta.top_tags && preferenceMeta.top_tags.length">
                  <el-tag
                    v-for="tag in preferenceMeta.top_tags"
                    :key="`pref-tag-${tag}`"
                    size="small"
                    class="meta-tag meta-tag-secondary"
                    type="info"
                  >
                    {{ tag }}
                  </el-tag>
                </template>
              </div>
            </div>
          </div>
          <div 
            v-if="favoriteTypeWorks && favoriteTypeWorks.length" 
            class="works-grid"
          >
            <div 
              v-for="(work, index) in favoriteTypeWorks" 
              :key="work.work_id || index"
              class="work-card"
              @click="handleWorkClick(work, 'favorite_type', index)"
            >
              <div class="work-cover">
                <img :src="work.cover_url || defaultCover" :alt="work.title">
              </div>
              <div class="work-info">
                <h4 class="work-title">{{ work.title }}</h4>
                <p class="work-author">{{ work.author_name }}</p>
                <p v-if="work.category_name" class="work-category">#{{ work.category_name }}</p>
                <div v-if="work.tags && work.tags.length" class="work-tagline">
                  <el-tag
                    v-for="tag in work.tags"
                    :key="`${work.work_id}-${tag}`"
                    size="small"
                    class="work-tagline-tag"
                    type="info"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
                <p class="work-intro">{{ work.intro }}</p>
                <div class="work-stats">
                  <span class="stat">
                    <el-icon><View /></el-icon>
                    {{ formatNumber(work.read_count) }}
                  </span>
                  <span class="stat">
                    <el-icon><Star /></el-icon>
                    {{ work.rating || '暂无评分' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <el-empty
            v-else
            class="section-empty"
            :description="favoriteTypeEmptyDescription"
            image-size="120"
          />
        </div>
        
        <div class="section">
          <div class="section-header">
            <h3>
              <el-icon><TrendCharts /></el-icon>
              {{ isPersonalized ? '最近搜索相似' : '热门新作推荐' }}
            </h3>
            <p>
              {{ searchSectionSubtitle }}
            </p>
          </div>
          <div 
            v-if="searchSimilarWorks && searchSimilarWorks.length"
            class="works-grid"
          >
            <div 
              v-for="(work, index) in searchSimilarWorks" 
              :key="work.work_id || index"
              class="work-card"
              @click="handleWorkClick(work, 'search_similar', index)"
            >
              <div class="work-cover">
                <img :src="work.cover_url || defaultCover" :alt="work.title">
                <div 
                  v-if="work.tags && work.tags.length" 
                  class="work-tags"
                >
                  <el-tag 
                    v-for="tag in work.tags" 
                    :key="tag"
                    size="small"
                    class="work-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
              <div class="work-info">
                <h4 class="work-title">{{ work.title }}</h4>
                <p class="work-author">{{ work.author_name }}</p>
                <p v-if="work.category_name" class="work-category">#{{ work.category_name }}</p>
                <p class="work-intro">{{ work.intro }}</p>
                <div class="work-stats">
                  <span class="stat">
                    <el-icon><View /></el-icon>
                    {{ formatNumber(work.read_count) }}
                  </span>
                  <span class="stat">
                    <el-icon><Star /></el-icon>
                    {{ work.rating || '暂无评分' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <el-empty
            v-else
            class="section-empty"
            :description="searchEmptyDescription"
            image-size="120"
          />
        </div>
        
        <div class="section">
          <div class="section-header">
            <h3>
              <el-icon><Trophy /></el-icon>
              {{ isPersonalized ? '喜欢类型上榜' : '热门榜单作品' }}
            </h3>
            <p>
              {{ rankSectionSubtitle }}
            </p>
            <div
              v-if="preferenceMeta.popular_categories && preferenceMeta.popular_categories.length"
              class="preference-meta"
            >
              <div class="meta-row">
                <span class="meta-label">热门类别</span>
                <el-tag
                  v-for="category in preferenceMeta.popular_categories"
                  :key="category.category_id || category.name"
                  size="small"
                  class="meta-tag"
                  type="warning"
                >
                  {{ category.name || '未分类' }}
                </el-tag>
              </div>
            </div>
          </div>
          <div 
            v-if="favoriteRankWorks && favoriteRankWorks.length"
            class="works-grid"
          >
            <div 
              v-for="(work, index) in favoriteRankWorks" 
              :key="work.work_id || index"
              class="work-card"
              @click="handleWorkClick(work, 'favorite_rank', index)"
            >
              <div class="work-cover">
                <img :src="work.cover_url || defaultCover" :alt="work.title">
                <div 
                  v-if="work.tags && work.tags.length"
                  class="work-tags"
                >
                  <el-tag 
                    v-for="tag in work.tags" 
                    :key="tag"
                    size="small"
                    class="work-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
              <div class="work-info">
                <h4 class="work-title">{{ work.title }}</h4>
                <p class="work-author">{{ work.author_name }}</p>
                <p v-if="work.category_name" class="work-category">#{{ work.category_name }}</p>
                <p class="work-intro">{{ work.intro }}</p>
                <div class="work-stats">
                  <span class="stat">
                    <el-icon><View /></el-icon>
                    {{ formatNumber(work.read_count) }}
                  </span>
                  <span class="stat">
                    <el-icon><Star /></el-icon>
                    {{ work.rating || '暂无评分' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <el-empty
            v-else
            class="section-empty"
            :description="rankEmptyDescription"
            image-size="120"
          />
        </div>
      </div>
      
      <!-- 刷新推荐按钮 -->
      <div class="refresh-section">
        <el-button 
          type="primary" 
          size="large"
          @click="refreshRecommendations"
          :loading="refreshing"
          class="refresh-btn"
        >
          <el-icon><Refresh /></el-icon>
          刷新推荐
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  Star, TrendCharts, Trophy, View as ViewIcon, Refresh 
} from '@element-plus/icons-vue'
import { getRecommendations, sendRecommendationFeedback } from '../api'

export default {
  name: 'Recommendations',
  components: {
    Star,
    TrendCharts,
    Trophy,
    ViewIcon,
    Refresh
  },
  data() {
    return {
      favoriteTypeWorks: [],
      searchSimilarWorks: [],
      favoriteRankWorks: [],
      preferenceMeta: {
        top_categories: [],
        top_tags: [],
        popular_categories: [],
        is_personalized: false,
        has_search_history: false
      },
      refreshing: false,
      defaultCover: 'https://via.placeholder.com/200x280/667eea/ffffff?text=封面'
    }
  },
  created() {
    this.loadRecommendations()
  },
  computed: {
    isPersonalized() {
      return !!(this.preferenceMeta && this.preferenceMeta.is_personalized)
    },
    hasPreferenceMeta() {
      if (!this.isPersonalized) return false
      const meta = this.preferenceMeta || {}
      const hasCategories = Array.isArray(meta.top_categories) && meta.top_categories.length > 0
      const hasTags = Array.isArray(meta.top_tags) && meta.top_tags.length > 0
      return hasCategories || hasTags
    },
    favoriteSectionSubtitle() {
      if (this.isPersonalized) {
        return '根据你的阅读、收藏、投票与订阅记录推荐更精准的作品'
      }
      return '暂无足够行为数据，完成阅读、收藏或订阅后即可获得个性化推荐'
    },
    searchSectionSubtitle() {
      const hasHistory = !!(this.preferenceMeta && this.preferenceMeta.has_search_history)
      if (hasHistory) {
        return '基于你的搜索历史推荐相关作品'
      }
      return '暂无搜索记录，搜索你感兴趣的关键词即可生成推荐'
    },
    rankSectionSubtitle() {
      const popularList = this.preferenceMeta && Array.isArray(this.preferenceMeta.popular_categories)
        ? this.preferenceMeta.popular_categories
        : []
      const hasPersonalRank = this.isPersonalized && popularList.length > 0
      if (hasPersonalRank) {
        return '根据你偏好的类型挑选榜单热门作品'
      }
      return '精选当前榜单热度作品'
    },
    favoriteTypeEmptyDescription() {
      if (this.isPersonalized) {
        return '暂未找到匹配偏好标签的作品，试试刷新或关注更多标签'
      }
      return '暂无偏好数据，完成阅读、收藏、投票或订阅后即可生成推荐'
    },
    searchEmptyDescription() {
      const hasHistory = !!(this.preferenceMeta && this.preferenceMeta.has_search_history)
      if (hasHistory) {
        return '暂未找到与最近搜索相匹配的作品，换个关键词再试试'
      }
      return '暂无搜索记录，搜索你感兴趣的内容后即可获得推荐'
    },
    rankEmptyDescription() {
      return '暂无榜单推荐，请稍后再试或刷新列表'
    }
  },
  methods: {
    async loadRecommendations() {
      this.refreshing = true
      try {
        const response = await getRecommendations()
        const data = response?.data || {}

        this.favoriteTypeWorks = data.favorite_type_works || []
        this.searchSimilarWorks = data.search_similar_works || []
        this.favoriteRankWorks = data.favorite_rank_works || []
        const defaultMeta = {
          top_categories: [],
          top_tags: [],
          popular_categories: [],
          is_personalized: false,
          has_search_history: false
        }
        this.preferenceMeta = Object.assign(defaultMeta, data.meta || {})

        if (!data.success) {
          const message = data.message || data.error
          if (message) {
            this.$message.warning(message)
          }
          return false
        }

        return true
      } catch (error) {
        this.favoriteTypeWorks = []
        this.searchSimilarWorks = []
        this.favoriteRankWorks = []
        this.preferenceMeta = {
          top_categories: [],
          top_tags: [],
          popular_categories: [],
          is_personalized: false,
          has_search_history: false
        }
        this.$message.error('加载推荐失败')
        console.error('Load recommendations error:', error)
        return false
      } finally {
        this.refreshing = false
      }
    },
    
    async refreshRecommendations() {
      const success = await this.loadRecommendations()
      if (success) {
        this.$message.success('推荐已刷新')
      }
    },

    handleWorkClick(work, slot, position = 0) {
      if (!work || !work.work_id) return
      this.reportRecommendationFeedback(work.work_id, 'click', { slot, position })
      this.$router.push({
        path: `/main/work-detail/${work.work_id}`,
        query: {
          source: 'recommendation',
          slot,
          position
        }
      })
    },

    reportRecommendationFeedback(workId, event, extra = {}) {
      if (!workId) return

      const payload = {
        work_id: workId,
        event,
        source: 'recommendation'
      }

      if (extra.slot !== undefined && extra.slot !== null) {
        payload.slot = extra.slot
      }
      if (typeof extra.position === 'number') {
        payload.position = extra.position
      }

      const metadata = {}
      if (extra.slot !== undefined && extra.slot !== null) {
        metadata.section = extra.slot
      }
      if (typeof extra.position === 'number') {
        metadata.position = extra.position
      }

      const sectionList = this.getSectionList(extra.slot)
      if (Array.isArray(sectionList) && sectionList.length > 0) {
        metadata.list_length = sectionList.length
      }

      if (extra.additional && typeof extra.additional === 'object') {
        Object.assign(metadata, extra.additional)
      }

      if (Object.keys(metadata).length > 0) {
        payload.metadata = metadata
      }

      sendRecommendationFeedback(payload).catch(error => {
        console.warn('发送推荐反馈失败:', error)
      })
    },

    getSectionList(slot) {
      switch (slot) {
        case 'favorite_type':
          return this.favoriteTypeWorks || []
        case 'search_similar':
          return this.searchSimilarWorks || []
        case 'favorite_rank':
          return this.favoriteRankWorks || []
        default:
          return []
      }
    },

    formatNumber(num) {
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      }
      return num.toString()
    }
  }
}
</script>

<style scoped>
.recommendations-container {
  height: 100%;
}

.recommendations-header {
  text-align: center;
  margin-bottom: 30px;
}

.recommendations-header h2 {
  color: #2c3e50;
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.subtitle {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.recommendations-content {
  height: calc(100% - 120px);
  overflow-y: auto;
}

.recommendation-sections {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.section {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.section-header {
  margin-bottom: 25px;
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.section-header h3 .el-icon {
  color: #667eea;
}

.section-header p {
  color: #7f8c8d;
  margin: 0;
  font-size: 0.95rem;
}

.preference-meta {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-row-inline {
  column-gap: 8px;
}

.meta-row-secondary {
  margin-top: 4px;
}

.meta-label {
  font-size: 0.8rem;
  color: #5a6c7d;
  font-weight: 600;
}

.meta-label-secondary {
  margin-left: 12px;
}

.meta-tag {
  border-radius: 999px;
}

.meta-tag-secondary {
  border-color: rgba(14, 165, 233, 0.3);
  color: #0369a1;
  background: rgba(14, 165, 233, 0.12);
}

.work-tagline {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.work-tagline-tag {
  border-radius: 999px;
}

.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
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

.work-tags {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.work-tag {
  background: rgba(102, 126, 234, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.35);
  color: #475569;
  font-size: 0.7rem;
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
  margin: 0 0 8px 0;
}

.work-category {
  color: #667eea;
  font-size: 0.75rem;
  margin: 0 0 8px 0;
}

.work-intro {
  color: #5a6c7d;
  font-size: 0.85rem;
  line-height: 1.4;
  margin: 0 0 12px 0;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.work-stats {
  display: flex;
  gap: 15px;
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

.refresh-section {
  text-align: center;
  margin-top: 40px;
  padding: 30px;
}

.refresh-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 25px;
  padding: 12px 30px;
  font-size: 1.1rem;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.section-empty {
  padding: 40px 0;
}

@media (max-width: 768px) {
  .recommendations-header h2 {
    font-size: 1.5rem;
  }
  
  .section {
    padding: 20px;
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

