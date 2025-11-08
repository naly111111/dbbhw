<template>
  <div class="chapter-manage-container">
    <div class="manage-header">
      <el-button 
        type="text" 
        @click="goBack"
        class="back-button"
      >
        <el-icon><ArrowLeft /></el-icon>
        返回作者模式
      </el-button>
      <h2>{{ workTitle }} - 章节管理</h2>
      <el-button 
        type="primary" 
        @click="createChapter"
        class="create-btn"
      >
        <el-icon><Plus /></el-icon>
        新建章节
      </el-button>
    </div>
    
    <div class="manage-content">
      <div v-if="chapters.length === 0" class="empty-chapters">
        <el-empty description="暂无章节">
          <el-button type="primary" @click="createChapter">
            创建第一个章节
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="chapters-list">
        <div 
          v-for="chapter in chapters" 
          :key="chapter.chapter_id"
          class="chapter-item"
        >
          <div class="chapter-info">
            <h3 class="chapter-title">{{ chapter.title }}</h3>
            <p class="chapter-meta">
              字数: {{ chapter.word_count || 0 }} |
              类型: {{ chapter.is_free ? '免费章节' : ('付费章节（' + (chapter.cost || 0) + ' 点券）') }} |
              发布时间: {{ formatTime(chapter.publish_time) }} |
              状态: {{ getStatusText(chapter.status) }}
            </p>
          </div>
          
          <div class="chapter-actions">
            <el-button 
              type="primary" 
              size="small"
              @click="editChapter(chapter)"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              type="success" 
              size="small"
              @click="publishChapter(chapter)"
              v-if="chapter.status === 0"
            >
              <el-icon><Upload /></el-icon>
              发布
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="deleteChapter(chapter)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 创建/编辑章节对话框 -->
    <el-dialog 
      v-model="showChapterDialog" 
      :title="isEdit ? '编辑章节' : '创建章节'"
      width="800px"
    >
      <el-form :model="chapterForm" :rules="chapterRules" ref="chapterFormRef">
        <el-form-item label="章节标题" prop="title">
          <el-input v-model="chapterForm.title" placeholder="请输入章节标题" />
        </el-form-item>
        
        <el-form-item label="章节内容" prop="content">
          <el-input
            v-model="chapterForm.content"
            type="textarea"
            :rows="15"
            placeholder="请输入章节内容..."
          />
        </el-form-item>
        
        <el-form-item label="章节简介">
          <el-input
            v-model="chapterForm.intro"
            type="textarea"
            :rows="3"
            placeholder="请输入章节简介（可选）..."
          />
        </el-form-item>

        <el-form-item label="章节类型">
          <el-radio-group v-model="chapterForm.is_free">
            <el-radio-button :label="true">免费章节</el-radio-button>
            <el-radio-button :label="false">付费章节</el-radio-button>
          </el-radio-group>
          <p class="cost-hint" v-if="!chapterForm.is_free">
            当前字数 {{ currentWordCount }} 字，预计需要 {{ estimatedCost }} 点券（1 点券 = 200 字）
          </p>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showChapterDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSaveChapter"
          :loading="saving"
        >
          {{ isEdit ? '保存修改' : '创建章节' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ArrowLeft, Plus, Edit, Upload, Delete } from '@element-plus/icons-vue'
import { getChapters, createChapter, updateChapter, deleteChapter as deleteChapterApi } from '@/api'

export default {
  name: 'ChapterManage',
  components: {
    ArrowLeft,
    Plus,
    Edit,
    Upload,
    Delete
  },
  data() {
    return {
      workId: null,
      workTitle: '',
      chapters: [],
      showChapterDialog: false,
      isEdit: false,
      saving: false,
      chapterForm: {
        title: '',
        content: '',
        intro: '',
        is_free: true // Default to free
      },
      chapterRules: {
        title: [
          { required: true, message: '请输入章节标题', trigger: 'blur' }
        ],
        content: [
          { required: true, message: '请输入章节内容', trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    currentWordCount() {
      const content = this.chapterForm && this.chapterForm.content ? this.chapterForm.content : ''
      return content.trim().length
    },
    estimatedCost() {
      if (this.currentWordCount <= 0) {
        return 0
      }
      return Math.max(1, Math.ceil(this.currentWordCount / 200))
    }
  },
  created() {
    this.workId = this.$route.params.workId
    this.loadChapters()
  },
  methods: {
    goBack() {
      this.$router.push('/main/author-mode')
    },
    
    async loadChapters() {
      try {
        const response = await getChapters(this.workId)
        if (response.data.success) {
          this.chapters = response.data.chapters || []
          this.workTitle = response.data.work_title || '未知作品'
        } else {
          this.$message.error('加载章节失败')
        }
      } catch (error) {
        this.$message.error('加载章节失败，请检查网络连接')
        console.error('Load chapters error:', error)
      }
    },
    
    createChapter() {
      this.isEdit = false
      this.chapterForm = {
        title: '',
        content: '',
        intro: '',
        is_free: true
      }
      this.showChapterDialog = true
    },
    
    editChapter(chapter) {
      this.isEdit = true
      this.chapterForm = {
        title: chapter.title,
        content: chapter.content,
        intro: chapter.intro || '',
        is_free: chapter.is_free
      }
      this.currentChapterId = chapter.chapter_id
      this.showChapterDialog = true
    },
    
    async handleSaveChapter() {
      try {
        await this.$refs.chapterFormRef.validate()
        this.saving = true
        
        const chapterData = {
          title: this.chapterForm.title,
          content: this.chapterForm.content,
          intro: this.chapterForm.intro,
          is_free: this.chapterForm.is_free
        }
        
        let response
        if (this.isEdit) {
          response = await updateChapter(this.workId, this.currentChapterId, chapterData)
        } else {
          response = await createChapter(this.workId, chapterData)
        }
        
        if (response.data.success) {
          this.$message.success(this.isEdit ? '章节修改成功' : '章节创建成功')
          this.showChapterDialog = false
          this.loadChapters()
        } else {
          this.$message.error(response.data.error || '操作失败')
        }
      } catch (error) {
        this.$message.error('操作失败，请检查网络连接')
        console.error('Save chapter error:', error)
      } finally {
        this.saving = false
      }
    },
    
    async publishChapter(chapter) {
      try {
        await this.$confirm('确定要发布这个章节吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await updateChapter(this.workId, chapter.chapter_id, {
          title: chapter.title,
          content: chapter.content,
          intro: chapter.intro,
          is_free: chapter.is_free,
          status: 1
        })
        
        if (response.data.success) {
          this.$message.success('章节发布成功')
          this.loadChapters()
        } else {
          this.$message.error(response.data.error || '发布失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('发布失败')
          console.error('Publish chapter error:', error)
        }
      }
    },
    
    async deleteChapter(chapter) {
      try {
        await this.$confirm('确定要删除这个章节吗？删除后无法恢复！', '警告', {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await deleteChapterApi(this.workId, chapter.chapter_id)
        if (response.data.success) {
          this.$message.success('章节删除成功')
          this.loadChapters()
        } else {
          this.$message.error(response.data.error || '删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('删除失败')
          console.error('Delete chapter error:', error)
        }
      }
    },
    
    getStatusText(status) {
      const texts = {
        0: '草稿',
        1: '已发布',
        2: '已下架'
      }
      return texts[status] || '未知'
    },
    
    formatTime(timeString) {
      if (!timeString) return '未发布'
      return new Date(timeString).toLocaleString()
    }
  }
}
</script>

<style scoped>
.chapter-manage-container {
  height: 100%;
  overflow-y: auto;
}

.manage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.back-button {
  color: #7f8c8d;
  font-size: 1rem;
}

.back-button:hover {
  color: #667eea;
}

.manage-header h2 {
  color: #2c3e50;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  flex: 1;
  margin-left: 20px;
}

.create-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.empty-chapters {
  text-align: center;
  padding: 60px 20px;
}

.chapters-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.chapter-item {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.chapter-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.chapter-info {
  flex: 1;
}

.chapter-title {
  color: #2c3e50;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.chapter-meta {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 0;
}

.chapter-actions {
  display: flex;
  gap: 10px;
}

.chapter-actions .el-button {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cost-hint {
  margin-top: 8px;
  color: #7f8c8d;
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .manage-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .manage-header h2 {
    margin-left: 0;
  }
  
  .chapter-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .chapter-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>


