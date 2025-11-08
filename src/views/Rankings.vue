<template>
  <div class="rankings-container">
    <div class="rankings-header">
      <h2>排行榜</h2>
      <!--<p>精选热门作品</p>-->
      <div class="ranking-filters">
        <el-select v-model="selectedCategory" placeholder="选择分类" @change="loadRankings">
          <el-option label="全部分类" value=""></el-option>
          <el-option 
            v-for="category in categories" 
            :key="category.category_id"
            :label="category.name"
            :value="category.category_id"
          />
        </el-select>
        
        <el-select v-model="selectedType" placeholder="选择榜单类型" @change="loadRankings">
          <el-option label="阅读榜" value="read"></el-option>
          <el-option label="投票榜" value="vote"></el-option>
          <el-option label="订阅榜" value="subscribe"></el-option>
        </el-select>
        
        <el-select v-model="selectedPeriod" placeholder="选择周期" @change="loadRankings">
          <el-option label="日榜" value="day"></el-option>
          <el-option label="周榜" value="week"></el-option>
          <el-option label="月榜" value="month"></el-option>
          <el-option label="总榜" value="total"></el-option>
        </el-select>
      </div>
    </div>
    
    <div class="rankings-content" v-loading="loading">
      <div class="ranking-cards">
        <div 
          v-for="(work, index) in rankings" 
          :key="work.work_id"
          class="ranking-card"
          :class="{ 'top-three': index < 3 }"
          @click="goToWorkDetail(work.work_id)"
        >
          <div class="ranking-number">
            <span v-if="index < 3" class="medal">
              <el-icon v-if="index === 0"><Trophy /></el-icon>
              <el-icon v-else-if="index === 1"><Medal /></el-icon>
              <el-icon v-else><Trophy /></el-icon>
            </span>
            <span v-else class="number">{{ index + 1 }}</span>
          </div>
          
          <div class="work-cover">
            <img :src="work.cover_url || defaultCover" :alt="work.title">
          </div>
          
          <div class="work-info">
            <h3 class="work-title">{{ work.title }}</h3>
            <p class="work-author">{{ work.author_name }}</p>
            <div class="work-stats">
              <span class="stat-item">
                <el-icon><View /></el-icon>
                {{ formatNumber(work.score) }}
              </span>
              <span class="stat-label">{{ getStatLabel() }}</span>
            </div>
          </div>
          
          <div class="ranking-trend">
            <el-icon v-if="index < 3" class="trend-up">
              <TrendCharts />
            </el-icon>
          </div>
        </div>
      </div>
      
      <div v-if="rankings.length === 0" class="empty-rankings">
        <el-empty description="暂无排行榜数据">
          <el-button type="primary" @click="loadRankings">
            刷新榜单
          </el-button>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  Trophy, Medal, View as ViewIcon, TrendCharts 
} from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'Rankings',
  components: {
    Trophy,
    Medal,
    ViewIcon,
    TrendCharts
  },
  data() {
    return {
      rankings: [],
      categories: [],
      selectedCategory: '',
      selectedType: 'read',
      selectedPeriod: 'week',
      loading: false,
      defaultCover: 'https://via.placeholder.com/120x160/667eea/ffffff?text=封面'
    }
  },
  created() {
    this.loadCategories()
    this.loadRankings()
  },
  methods: {
    async loadCategories() {
      try {
        const response = await api.get('/categories/')
        if (response.data.success) {
          this.categories = response.data.categories || []
        }
      } catch (error) {
        console.error('Load categories error:', error)
      }
    },
    
    async loadRankings() {
      try {
        this.loading = true
        const params = {
          type: this.selectedType,
          period: this.selectedPeriod
        }
        
        if (this.selectedCategory) {
          params.category_id = this.selectedCategory
        }
        
        const response = await api.get('/rankings/', { params })
        this.rankings = response.data.success ? (response.data.rankings || []) : []
      } catch (error) {
        this.$message.error('加载排行榜失败')
        console.error('Load rankings error:', error)
      } finally {
        this.loading = false
      }
    },
    
    goToWorkDetail(workId) {
      this.$router.push(`/main/work-detail/${workId}`)
    },
    
    getStatLabel() {
      const labels = {
        'read': '阅读量',
        'vote': '投票数',
        'subscribe': '订阅数'
      }
      return labels[this.selectedType] || '阅读量'
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
.rankings-container {
  height: 100%;
}

.rankings-header {
  text-align: center;
  margin-bottom: 30px;
}

.rankings-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.rankings-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.ranking-filters {
  
  display: center;
  gap: 15px;
  flex-wrap: wrap;
}

.ranking-filters .el-select {
  width: 150px;
}

.rankings-content {
  height: calc(100% - 100px);
  overflow-y: auto;
}

.ranking-cards {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.ranking-card {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
}

.ranking-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.ranking-card.top-three {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ranking-card.top-three .work-title,
.ranking-card.top-three .work-author {
  color: white;
}

.ranking-number {
  width: 60px;
  text-align: center;
  font-size: 1.5rem;
  font-weight: bold;
  margin-right: 20px;
}

.medal {
  font-size: 2rem;
}

.medal .el-icon {
  color: #ffd700;
}

.number {
  color: #7f8c8d;
}

.work-cover {
  width: 80px;
  height: 110px;
  margin-right: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
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
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.work-author {
  color: #7f8c8d;
  font-size: 1rem;
  margin: 0 0 10px 0;
}

.work-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 1.1rem;
  font-weight: 600;
  color: #667eea;
}

.stat-label {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.ranking-trend {
  margin-left: 20px;
}

.trend-up {
  color: #67c23a;
  font-size: 1.5rem;
}

.empty-rankings {
  text-align: center;
  padding: 60px 20px;
}

@media (max-width: 768px) {
  .rankings-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .ranking-filters {
    width: 100%;
    justify-content: space-between;
  }
  
  .ranking-filters .el-select {
    flex: 1;
    min-width: 100px;
  }
  
  .ranking-card {
    padding: 15px;
  }
  
  .ranking-number {
    width: 40px;
    margin-right: 15px;
    font-size: 1.2rem;
  }
  
  .work-cover {
    width: 60px;
    height: 80px;
    margin-right: 15px;
  }
  
  .work-title {
    font-size: 1rem;
  }
  
  .work-author {
    font-size: 0.9rem;
  }
}
</style>

