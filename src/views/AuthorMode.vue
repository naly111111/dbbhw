<template>
  <div class="author-mode-container">
    <div class="author-header">
      <h2>作者模式</h2>
      <p>管理您的作品和创作内容</p>
    </div>

    <div class="summary-cards" v-if="summary">
      <div class="summary-card">
        <div class="summary-icon total-income">
          <el-icon><Money /></el-icon>
        </div>
        <div class="summary-info">
          <span class="summary-label">总点券收益</span>
          <span class="summary-value">{{ formatNumber(summary.total_subscription_income || 0) }}</span>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon total-read">
          <el-icon><ViewIcon /></el-icon>
        </div>
        <div class="summary-info">
          <span class="summary-label">总阅读量</span>
          <span class="summary-value">{{ formatNumber(summary.total_read_count || 0) }}</span>
          <span class="summary-sub">独立读者 {{ formatNumber(summary.total_unique_readers || 0) }}</span>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon total-collect">
          <el-icon><Collection /></el-icon>
        </div>
        <div class="summary-info">
          <span class="summary-label">总收藏量</span>
          <span class="summary-value">{{ formatNumber(summary.total_collect_count || 0) }}</span>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon total-vote">
          <el-icon><Star /></el-icon>
        </div>
        <div class="summary-info">
          <span class="summary-label">总投票数</span>
          <span class="summary-value">{{ formatNumber(summary.total_vote_count || 0) }}</span>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon total-subscription">
          <el-icon><Document /></el-icon>
        </div>
        <div class="summary-info">
          <span class="summary-label">总订阅人数</span>
          <span class="summary-value">{{ formatNumber(summary.total_subscription_count || 0) }}</span>
        </div>
      </div>
    </div>

    <div class="author-content">
      <div class="works-grid">
        <div 
          v-for="work in myWorks" 
          :key="work.work_id"
          class="work-card"
          @mouseenter="showWorkActions = work.work_id"
          @mouseleave="showWorkActions = null"
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
            <h3 class="work-title">{{ work.title }}</h3>
            <p class="work-category">{{ work.category_name }}</p>
            <p class="work-intro">{{ work.intro }}</p>
            <div class="work-stats">
              <span class="stat stat-read">
                <el-icon><ViewIcon /></el-icon>
                {{ formatNumber(work.read_count || 0) }}
                <span class="stat-sub">独立 {{ formatNumber(work.unique_readers || 0) }}</span>
              </span>
              <span class="stat">
                <el-icon><Collection /></el-icon>
                {{ formatNumber(work.collect_count || 0) }}
              </span>
              <span class="stat">
                <el-icon><Star /></el-icon>
                {{ formatNumber(work.vote_count || 0) }}
              </span>
              <span class="stat">
                <el-icon><Document /></el-icon>
                {{ formatNumber(work.subscription_count || 0) }}
              </span>
              <span class="stat income">
                <el-icon><Money /></el-icon>
                {{ formatNumber(work.subscription_income || 0) }}
              </span>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div 
            v-if="showWorkActions === work.work_id" 
            class="work-actions"
          >
            <el-button 
              type="primary" 
              size="small"
              @click="viewWorkDetail(work)"
            >
              <el-icon><ViewIcon /></el-icon>
              查看详情
            </el-button>
            <el-button 
              type="primary" 
              size="small"
              @click="editWorkDetail(work)"
            >
              <el-icon><Edit /></el-icon>
              修改详情
            </el-button>
            <el-button 
              type="success" 
              size="small"
              @click="editWork(work)"
            >
              <el-icon><Document /></el-icon>
              修改作品
            </el-button>
            <el-button 
              type="info" 
              size="small"
              @click="manageComments(work)"
            >
              <el-icon><ChatDotRound /></el-icon>
              整理评论
            </el-button>
            <el-button 
              type="warning" 
              size="small"
              @click="viewWorkMetrics(work)"
            >
              <el-icon><Money /></el-icon>
              作品数据
            </el-button>
          </div>
        </div>
        
        <!-- 创建新作品卡片 -->
        <div 
          class="work-card create-work-card"
          @click="createNewWork"
        >
          <div class="create-icon">
            <el-icon><Plus /></el-icon>
          </div>
          <h3>创建新作品</h3>
          <p>开始您的创作之旅</p>
        </div>
      </div>
    </div>
    
    <!-- 创建作品对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建新作品" width="600px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef">
        <el-form-item label="作品标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入作品标题" />
        </el-form-item>
        <el-form-item label="作品分类" prop="category_id">
          <el-select v-model="createForm.category_id" placeholder="选择分类">
            <el-option 
              v-for="category in categories" 
              :key="category.category_id"
              :label="category.name"
              :value="category.category_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="作品简介" prop="intro">
          <el-input
            v-model="createForm.intro"
            type="textarea"
            :rows="4"
            placeholder="请输入作品简介..."
          />
        </el-form-item>
        <el-form-item label="作品标签">
          <el-input
            v-model="createForm.tags_input"
            placeholder="请输入标签，用逗号分隔"
            @blur="parseTags"
          />
          <div class="tags-preview" v-if="createForm.tags.length > 0">
            <el-tag 
              v-for="tag in createForm.tags" 
              :key="tag"
              size="small"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="封面图片">
          <div class="cover-upload-wrapper">
            <el-upload
              class="cover-uploader"
              :show-file-list="false"
              accept="image/*"
              :http-request="handleCreateCoverUpload"
              :before-upload="beforeCoverUpload"
              :disabled="coverUploading"
            >
              <div v-if="createForm.cover_url" class="cover-preview">
                <img :src="createForm.cover_url" alt="封面预览" />
              </div>
              <div v-else class="cover-uploader-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传封面</span>
              </div>
            </el-upload>
            <div class="upload-hint">支持 JPG/PNG/GIF/WebP，大小不超过 5MB</div>
            <el-button
              v-if="createForm.cover_url"
              type="text"
              class="remove-cover-btn"
              @click="removeCreateCover"
            >
              移除封面
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateWork">创建作品</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showMetricsDialog"
      title="作品数据概览"
      width="520px"
      :before-close="handleMetricsClose"
    >
      <div class="metrics-container" v-loading="metricsLoading">
        <div v-if="metricsData">
          <h3 class="metrics-title">{{ metricsData.title }}</h3>
          <div class="metrics-grid">
            <div class="metrics-item">
              <span class="metrics-label">阅读量</span>
              <span class="metrics-value">{{ formatNumber(metricsData.total_reads || 0) }}</span>
              <span class="metrics-sub">独立读者 {{ formatNumber(metricsData.unique_readers || 0) }}</span>
            </div>
            <div class="metrics-item">
              <span class="metrics-label">收藏量</span>
              <span class="metrics-value">{{ formatNumber(metricsData.collect_count || 0) }}</span>
            </div>
            <div class="metrics-item">
              <span class="metrics-label">订阅人数</span>
              <span class="metrics-value">{{ formatNumber(metricsData.subscription_count || 0) }}</span>
            </div>
            <div class="metrics-item">
              <span class="metrics-label">点券收益</span>
              <span class="metrics-value">{{ formatNumber(metricsData.subscription_income || 0) }}</span>
            </div>
            <div class="metrics-item">
              <span class="metrics-label">累计投票</span>
              <span class="metrics-value">{{ formatNumber(metricsData.vote_count || 0) }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showMetricsDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { 
  View as ViewIcon, Collection, Edit, Document, ChatDotRound, Plus, Money, Star 
} from '@element-plus/icons-vue'
import api, { getWorkMetrics, uploadCoverFile } from '../api'

export default {
  name: 'AuthorMode',
  components: {
    ViewIcon,
    Collection,
    Edit,
    Document,
    ChatDotRound,
    Plus,
    Money,
    Star
  },
  data() {
    return {
      myWorks: [],
      categories: [],
      showWorkActions: null,
      showCreateDialog: false,
      showMetricsDialog: false,
      metricsData: null,
      metricsLoading: false,
      coverUploading: false,
      createForm: {
        title: '',
        category_id: '',
        intro: '',
        tags: [],
        tags_input: '',
        cover_url: ''
      },
      createRules: {
        title: [
          { required: true, message: '请输入作品标题', trigger: 'blur' }
        ],
        category_id: [
          { required: true, message: '请选择作品分类', trigger: 'change' }
        ],
        intro: [
          { required: true, message: '请输入作品简介', trigger: 'blur' }
        ]
      },
      summary: null,
      defaultCover: 'https://via.placeholder.com/200x280/667eea/ffffff?text=封面'
    }
  },
  created() {
    this.loadMyWorks()
    this.loadCategories()
  },
  methods: {
    async loadMyWorks() {
      try {
        const response = await api.get('/works/my-works/')
        if (response.data.success) {
          this.myWorks = response.data.works || []
          this.summary = response.data.summary || {
            total_read_count: 0,
            total_collect_count: 0,
            total_vote_count: 0,
            total_subscription_count: 0,
            total_subscription_income: 0,
            total_income: 0
          }
        } else {
          this.$message.error('加载作品失败')
        }
      } catch (error) {
        console.error('Load my works error:', error)
        this.$message.error('加载作品失败，请检查网络连接')
      }
    },
    
    async loadCategories() {
      try {
        const response = await api.get('/categories/')
        if (response.data.success) {
          this.categories = response.data.categories || []
        } else {
          this.$message.error('加载分类失败')
        }
      } catch (error) {
        console.error('Load categories error:', error)
        this.$message.error('加载分类失败，请检查网络连接')
      }
    },
    
    createNewWork() {
      this.showCreateDialog = true
    },
    
    beforeCoverUpload(file) {
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
      if (!allowedTypes.includes(file.type)) {
        this.$message.error('仅支持 JPG/PNG/GIF/WebP 格式的图片')
        return false
      }

      const isLt5M = file.size / 1024 / 1024 < 5
      if (!isLt5M) {
        this.$message.error('封面图片大小不能超过 5MB')
        return false
      }

      return true
    },

    async handleCreateCoverUpload(options) {
      const { file, onSuccess, onError } = options
      const successHandler = typeof onSuccess === 'function' ? onSuccess : () => {}
      const errorHandler = typeof onError === 'function' ? onError : () => {}

      this.coverUploading = true
      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await uploadCoverFile(formData)
        if (response.data && response.data.success) {
          this.createForm.cover_url = response.data.url || response.data.relative_url || ''
          successHandler(response.data, file)
          this.$message.success('封面上传成功，请记得保存变更')
        } else {
          const errorMsg = (response.data && response.data.error) || '封面上传失败'
          this.$message.error(errorMsg)
          errorHandler(new Error(errorMsg))
        }
      } catch (error) {
        console.error('Upload cover error:', error)
        this.$message.error('封面上传失败，请稍后重试')
        errorHandler(error)
      } finally {
        this.coverUploading = false
      }
    },

    removeCreateCover() {
      this.createForm.cover_url = ''
    },

    async handleCreateWork() {
      try {
        await this.$refs.createFormRef.validate()
        
        const workData = {
          ...this.createForm,
          tags: this.createForm.tags
        }
        
        const response = await api.post('/works/create/', workData)
        if (response.data.success) {
          this.$message.success('作品创建成功')
          this.showCreateDialog = false
          this.resetCreateForm()
          this.loadMyWorks()
        } else {
          this.$message.error(response.data.error || '创建作品失败')
        }
      } catch (error) {
        this.$message.error('创建作品失败')
        console.error('Create work error:', error)
      }
    },
    
    resetCreateForm() {
      this.createForm = {
        title: '',
        category_id: '',
        intro: '',
        tags: [],
        tags_input: '',
        cover_url: ''
      }
    },
    
    parseTags() {
      if (this.createForm.tags_input) {
        this.createForm.tags = this.createForm.tags_input
          .split(',')
          .map(tag => tag.trim())
          .filter(tag => tag.length > 0)
      }
    },
    
    editWorkDetail(work) {
      this.$router.push(`/main/work-edit/${work.work_id}`)
    },
    
    viewWorkDetail(work) {
      this.$router.push(`/main/work-detail/${work.work_id}`)
    },

    editWork(work) {
      this.$router.push(`/main/chapter-manage/${work.work_id}`)
    },
    
    manageComments(work) {
      this.$router.push(`/main/comment-manage/${work.work_id}`)
    },

    async viewWorkMetrics(work) {
      try {
        this.showMetricsDialog = true
        this.metricsLoading = true
        const response = await getWorkMetrics(work.work_id)
        if (response.data.success) {
          this.metricsData = response.data.metrics
        } else {
          this.$message.error(response.data.error || '加载作品数据失败')
        }
      } catch (error) {
        console.error('Load work metrics error:', error)
        this.$message.error('加载作品数据失败，请稍后重试')
      } finally {
        this.metricsLoading = false
      }
    },

    handleMetricsClose(done) {
      this.showMetricsDialog = false
      if (typeof done === 'function') {
        done()
      }
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
    }
  }
}
</script>

<style scoped>
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin: 0 0 25px 0;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 18px 20px;
  border-radius: 14px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.4rem;
}

.summary-icon.total-income { background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%); }
.summary-icon.total-read { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); }
.summary-icon.total-collect { background: linear-gradient(135deg, #10b981 0%, #22d3ee 100%); }
.summary-icon.total-vote { background: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%); }
.summary-icon.total-subscription { background: linear-gradient(135deg, #ec4899 0%, #f43f5e 100%); }

.summary-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-label {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.summary-sub {
  font-size: 0.75rem;
  color: #94a3b8;
}

.summary-value {
  font-size: 1.4rem;
  font-weight: 600;
  color: #2c3e50;
}

.author-mode-container {
  height: 100%;
}

.author-header {
  text-align: center;
  margin-bottom: 30px;
}

.author-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.author-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.author-content {
  height: calc(100% - 120px);
  overflow-y: auto;
}

.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 25px;
}

.work-card {
  background: white;
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
}

.work-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.create-work-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 2px dashed #dee2e6;
  cursor: pointer;
  transition: all 0.3s ease;
}

.create-work-card:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
}

.create-icon {
  font-size: 3rem;
  color: #667eea;
  margin-bottom: 15px;
}

.create-work-card:hover .create-icon {
  color: white;
}

.create-work-card h3 {
  color: #2c3e50;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.create-work-card:hover h3 {
  color: white;
}

.create-work-card p {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 0;
}

.create-work-card:hover p {
  color: white;
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
  padding: 20px;
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

.work-category {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 0 0 10px 0;
}

.work-intro {
  color: #5a6c7d;
  font-size: 0.85rem;
  line-height: 1.4;
  margin: 0 0 15px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.work-stats {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
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

.stat-sub {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-left: 4px;
}

.stat.income {
  font-weight: 600;
  color: #f59e0b;
}

.stat.income .el-icon {
  color: #f59e0b;
}

.work-actions {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  opacity: 0;
  transition: opacity 0.3s ease;
  padding: 30px 20px;
}

.work-card:hover .work-actions {
  opacity: 1;
}

.work-actions .el-button {
  width: 160px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  padding-left: 16px;
}

.work-actions .el-button :deep(.el-icon) {
  margin-right: 0;
}

.tags-preview {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tag-item {
  margin: 0;
}

.cover-upload-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cover-uploader {
  display: inline-block;
}

.cover-uploader :deep(.el-upload) {
  border: 1px dashed #dcdfe6;
  border-radius: 12px;
  cursor: pointer;
  overflow: hidden;
  width: 160px;
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  transition: border-color 0.3s ease;
}

.cover-uploader :deep(.el-upload:hover) {
  border-color: #409eff;
}

.cover-preview {
  width: 160px;
  height: 220px;
  overflow: hidden;
  border-radius: 12px;
}

.cover-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-uploader-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 12px;
  gap: 6px;
}

.cover-uploader-placeholder .el-icon {
  font-size: 24px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.remove-cover-btn {
  align-self: flex-start;
  padding: 0;
  font-size: 12px;
}

.metrics-container {
  min-height: 160px;
}

.metrics-title {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-weight: 600;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.metrics-item {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metrics-label {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.metrics-value {
  font-size: 1.3rem;
  font-weight: 600;
  color: #2c3e50;
}

.metrics-sub {
  font-size: 0.75rem;
  color: #94a3b8;
}

@media (max-width: 768px) {
  .works-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
  }

  .summary-cards {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  }
  
  .work-cover {
    height: 150px;
  }
  
  .work-actions {
    position: static;
    background: transparent;
    opacity: 1;
    flex-direction: row;
    justify-content: space-around;
    padding: 15px;
    border-top: 1px solid #e0e0e0;
  }
  
  .work-actions .el-button {
    width: auto;
    padding: 8px 15px;
  }
}
</style>

