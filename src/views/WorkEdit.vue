<template>
  <div class="work-edit-container">
    <div class="edit-header">
      <el-button 
        type="text" 
        @click="goBack"
        class="back-button"
      >
        <el-icon><ArrowLeft /></el-icon>
        返回作者模式
      </el-button>
      <h2>修改作品详情</h2>
    </div>
    
    <div class="edit-content">
      <el-form
        ref="editForm"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="edit-form"
      >
        <el-form-item label="作品标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入作品标题"
            size="large"
          />
        </el-form-item>
        
        <el-form-item label="作品分类" prop="category_id">
          <el-select
            v-model="form.category_id"
            placeholder="选择分类"
            size="large"
            style="width: 100%"
          >
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
            v-model="form.intro"
            type="textarea"
            :rows="6"
            placeholder="请输入作品简介..."
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="作品标签">
          <el-input
            v-model="form.tags_input"
            placeholder="请输入标签，用逗号分隔"
            @blur="parseTags"
          />
          <div class="tags-preview" v-if="form.tags.length > 0">
            <el-tag 
              v-for="tag in form.tags" 
              :key="tag"
              size="small"
              class="tag-item"
              closable
              @close="removeTag(tag)"
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
              :http-request="handleCoverUpload"
              :before-upload="beforeCoverUpload"
              :disabled="coverUploading"
            >
              <div v-if="form.cover_url" class="cover-preview">
                <img :src="form.cover_url" alt="封面预览" />
              </div>
              <div v-else class="cover-uploader-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传封面</span>
              </div>
            </el-upload>
            <div class="upload-hint">支持 JPG/PNG/GIF/WebP，大小不超过 5MB</div>
            <el-button
              v-if="form.cover_url"
              type="text"
              class="remove-cover-btn"
              @click="removeCover"
            >
              移除封面
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="作品状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio 
              :label="0"
              :disabled="initialStatus !== 0"
              :title="initialStatus !== 0 ? '已发布作品无法回退至草稿状态' : ''"
            >草稿</el-radio>
            <el-radio :label="1">连载中</el-radio>
            <el-radio :label="2">完结</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleSave"
            :loading="saving"
            size="large"
          >
            保存修改
          </el-button>
          <el-button 
            @click="goBack"
            size="large"
          >
            取消
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import { getWorkDetail, updateWork, getCategories, uploadCoverFile } from '@/api'

export default {
  name: 'WorkEdit',
  components: {
    ArrowLeft,
    Plus
  },
  data() {
    return {
      workId: null,
      saving: false,
      coverUploading: false,
      form: {
        title: '',
        category_id: '',
        intro: '',
        tags: [],
        tags_input: '',
        cover_url: '',
        status: 0
      },
      initialStatus: 0,
      categories: [],
      rules: {
        title: [
          { required: true, message: '请输入作品标题', trigger: 'blur' }
        ],
        category_id: [
          { required: true, message: '请选择作品分类', trigger: 'change' }
        ],
        intro: [
          { required: true, message: '请输入作品简介', trigger: 'blur' }
        ]
      }
    }
  },
  created() {
    this.workId = this.$route.params.workId
    this.loadWorkDetail()
    this.loadCategories()
  },
  methods: {
    goBack() {
      this.$router.push('/main/author-mode')
    },
    
    async loadWorkDetail() {
      try {
        const response = await getWorkDetail(this.workId)
        if (response.data.success) {
          const work = response.data.work
          const parsedStatus = typeof work.status === 'number'
            ? work.status
            : parseInt(work.status, 10)
          const normalizedStatus = [0, 1, 2, 3].includes(parsedStatus) ? parsedStatus : 0
          this.initialStatus = normalizedStatus
          this.form = {
            title: work.title || '',
            category_id: work.category_id || '',
            intro: work.intro || '',
            tags: work.tags || [],
            tags_input: (work.tags || []).join(', '),
            cover_url: work.cover_url || '',
            status: normalizedStatus
          }
        } else {
          this.$message.error('加载作品详情失败')
        }
      } catch (error) {
        this.$message.error('加载作品详情失败，请检查网络连接')
        console.error('Load work detail error:', error)
      }
    },
    
    async loadCategories() {
      try {
        const response = await getCategories()
        if (response.data.success) {
          this.categories = response.data.categories || []
        }
      } catch (error) {
        console.error('Load categories error:', error)
      }
    },
    
    parseTags() {
      if (this.form.tags_input) {
        this.form.tags = this.form.tags_input
          .split(',')
          .map(tag => tag.trim())
          .filter(tag => tag.length > 0)
      } else {
        this.form.tags = []
      }
    },
    
    removeTag(tag) {
      this.form.tags = this.form.tags.filter(t => t !== tag)
      this.form.tags_input = this.form.tags.join(', ')
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

    async handleCoverUpload(options) {
      const { file, onSuccess, onError } = options
      const successHandler = typeof onSuccess === 'function' ? onSuccess : () => {}
      const errorHandler = typeof onError === 'function' ? onError : () => {}

      this.coverUploading = true
      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await uploadCoverFile(formData)
        if (response.data && response.data.success) {
          this.form.cover_url = response.data.url || response.data.relative_url || ''
          successHandler(response.data, file)
          this.$message.success('封面上传成功，请记得保存修改')
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

    removeCover() {
      this.form.cover_url = ''
    },

    async handleSave() {
      try {
        await this.$refs.editForm.validate()
        this.saving = true
        
        const rawStatus = typeof this.form.status === 'number'
          ? this.form.status
          : parseInt(this.form.status, 10)
        const normalizedStatus = [0, 1, 2, 3].includes(rawStatus) ? rawStatus : this.initialStatus

        const workData = {
          ...this.form,
          tags: this.form.tags,
          status: normalizedStatus
        }
        
        const response = await updateWork(this.workId, workData)
        if (response.data.success) {
          this.$message.success('作品修改成功')
          this.goBack()
        } else {
          this.$message.error(response.data.error || '修改失败')
        }
      } catch (error) {
        this.$message.error('修改失败，请检查网络连接')
        console.error('Update work error:', error)
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.work-edit-container {
  height: 100%;
  overflow-y: auto;
}

.edit-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.back-button {
  margin-right: 20px;
  color: #7f8c8d;
  font-size: 1rem;
}

.back-button:hover {
  color: #667eea;
}

.edit-header h2 {
  color: #2c3e50;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.edit-content {
  max-width: 800px;
}

.edit-form {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.tags-preview {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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

@media (max-width: 768px) {
  .edit-content {
    max-width: 100%;
  }
  
  .edit-form {
    padding: 20px;
  }
}
</style>


