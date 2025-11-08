<template>
  <div class="comment-manage-container">
    <div class="manage-header">
      <el-button 
        type="text" 
        @click="goBack"
        class="back-button"
      >
        <el-icon><ArrowLeft /></el-icon>
        返回作者模式
      </el-button>
      <h2>{{ workTitle }} - 评论管理</h2>
      <div class="header-actions">
        <el-select v-model="statusFilter" placeholder="筛选状态" @change="loadComments">
          <el-option label="全部" value="" />
          <el-option label="待审核" value="0" />
          <el-option label="已通过" value="1" />
          <el-option label="已拒绝" value="2" />
        </el-select>
      </div>
    </div>
    
    <div class="manage-content">
      <div v-if="comments.length === 0" class="empty-comments">
        <el-empty description="暂无评论" />
      </div>
      
      <div v-else class="comments-list">
        <div 
          v-for="comment in comments" 
          :key="comment.comment_id"
          class="comment-item"
          :class="{ 'pending': comment.status === 0 }"
        >
          <div class="comment-header">
            <div class="user-info">
              <el-avatar :size="40" :src="comment.user_avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-details">
                <h4 class="username">{{ comment.username }}</h4>
                <span class="comment-time">{{ formatTime(comment.create_time) }}</span>
              </div>
            </div>
            <div class="comment-status">
              <el-tag 
                :type="getStatusType(comment.status) || 'info'"
                size="small"
              >
                {{ getStatusText(comment.status) }}
              </el-tag>
            </div>
          </div>
          
          <div class="comment-content">
            <p>{{ comment.content }}</p>
          </div>
          
          <div class="comment-actions" v-if="comment.status === 0">
            <el-button 
              type="success" 
              size="small"
              @click="approveComment(comment)"
            >
              <el-icon><Check /></el-icon>
              通过
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="rejectComment(comment)"
            >
              <el-icon><Close /></el-icon>
              拒绝
            </el-button>
          </div>
          
          <div class="comment-actions" v-else>
            <el-button 
              type="info" 
              size="small"
              @click="deleteComment(comment)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div class="pagination-container" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, jumper"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ArrowLeft, User, Check, Close, Delete } from '@element-plus/icons-vue'
import { getComments, updateComment, deleteComment as deleteCommentApi } from '@/api'

export default {
  name: 'CommentManage',
  components: {
    ArrowLeft,
    User,
    Check,
    Close,
    Delete
  },
  data() {
    return {
      workId: null,
      workTitle: '',
      comments: [],
      statusFilter: '',
      currentPage: 1,
      pageSize: 10,
      total: 0,
      loading: false
    }
  },
  created() {
    this.workId = this.$route.params.workId
    this.loadComments()
  },
  methods: {
    goBack() {
      this.$router.push('/main/author-mode')
    },
    
    async loadComments() {
      try {
        this.loading = true
        const params = {
          page: this.currentPage,
          page_size: this.pageSize
        }
        if (this.statusFilter) {
          params.status = this.statusFilter
        }
        
        const response = await getComments(this.workId, params)
        if (response.data.success) {
          this.comments = response.data.comments || []
          this.total = response.data.total || 0
          this.workTitle = response.data.work_title || '未知作品'
        } else {
          this.$message.error('加载评论失败')
        }
      } catch (error) {
        this.$message.error('加载评论失败，请检查网络连接')
        console.error('Load comments error:', error)
      } finally {
        this.loading = false
      }
    },
    
    async approveComment(comment) {
      try {
        const response = await updateComment(this.workId, comment.comment_id, {
          status: 1
        })
        
        if (response.data.success) {
          this.$message.success('评论已通过')
          this.loadComments()
        } else {
          this.$message.error(response.data.error || '操作失败')
        }
      } catch (error) {
        this.$message.error('操作失败，请检查网络连接')
        console.error('Approve comment error:', error)
      }
    },
    
    async rejectComment(comment) {
      try {
        await this.$confirm('确定要拒绝这个评论吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await updateComment(this.workId, comment.comment_id, {
          status: 2
        })
        
        if (response.data.success) {
          this.$message.success('评论已拒绝')
          this.loadComments()
        } else {
          this.$message.error(response.data.error || '操作失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('操作失败')
          console.error('Reject comment error:', error)
        }
      }
    },
    
    async deleteComment(comment) {
      try {
        await this.$confirm('确定要删除这个评论吗？删除后无法恢复！', '警告', {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await deleteCommentApi(this.workId, comment.comment_id)
        if (response.data.success) {
          this.$message.success('评论删除成功')
          this.loadComments()
        } else {
          this.$message.error(response.data.error || '删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('删除失败')
          console.error('Delete comment error:', error)
        }
      }
    },
    
    handlePageChange(page) {
      this.currentPage = page
      this.loadComments()
    },
    
    getStatusType(status) {
      const types = {
        0: 'warning',  // 待审核
        1: 'success',  // 已通过
        2: 'danger'    // 已拒绝
      }
      return types[status] || 'info'
    },
    
    getStatusText(status) {
      const texts = {
        0: '待审核',
        1: '已通过',
        2: '已拒绝'
      }
      return texts[status] || '未知'
    },
    
    formatTime(timeString) {
      if (!timeString) return ''
      return new Date(timeString).toLocaleString()
    }
  }
}
</script>

<style scoped>
.comment-manage-container {
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

.header-actions {
  display: flex;
  gap: 15px;
}

.empty-comments {
  text-align: center;
  padding: 60px 20px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.comment-item {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.comment-item.pending {
  border-left: 4px solid #e6a23c;
}

.comment-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.username {
  color: #2c3e50;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.comment-time {
  color: #7f8c8d;
  font-size: 0.85rem;
}

.comment-content {
  margin-bottom: 15px;
}

.comment-content p {
  color: #5a6c7d;
  line-height: 1.6;
  margin: 0;
}

.comment-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
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
  
  .comment-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .comment-actions {
    justify-content: flex-start;
  }
}
</style>
