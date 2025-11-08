<template>
  <div class="bookshelf-container">
    <div class="bookshelf-header">
      <h2>我的书架</h2>
      <p class="subtitle">管理你的收藏和阅读记录</p>
    </div>

    <!-- 书架内容 -->
    <div class="bookshelf-content">
      <el-tabs 
        v-model="activeTab" 
        class="bookshelf-tabs"
        :stretch="true"
      >
        <el-tab-pane name="collections">
          <template #label>
            <div class="tab-icon-item tab-icon-collections">
              <el-icon><Collection /></el-icon>
              <span>收藏作品</span>
            </div>
          </template>
          <div v-if="collections.length === 0" class="empty-bookshelf">
            <el-empty description="书架空空如也">
              <el-button type="primary" @click="goToCategories">
                去作品库看看
              </el-button>
            </el-empty>
          </div>
          
          <div v-else class="books-grid">
            <div 
              v-for="work in collections" 
              :key="work.work_id"
              class="book-card"
              @click="goToReading(work.work_id)"
            >
              <div class="book-cover">
                <img :src="work.cover_url || defaultCover" :alt="work.title">
                <div class="book-status">
                  <el-tag 
                    :type="getStatusType(work.status) || 'info'"
                    size="small"
                  >
                    {{ getStatusText(work.status) }}
                  </el-tag>
                </div>
              </div>
              <div class="book-info">
                <h3 class="book-title">{{ work.title }}</h3>
                <p class="book-author">{{ work.author_name }}</p>
                <p class="book-category">{{ work.category_name }}</p>
                <div class="book-actions">
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click.stop="removeFromBookshelf(work.work_id)"
                    :icon="Delete"
                  >
                    移除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane name="history">
          <template #label>
            <div class="tab-icon-item tab-icon-history">
              <el-icon><Clock /></el-icon>
              <span>浏览记录</span>
            </div>
          </template>
          <div v-if="readingHistory.length > 0" class="history-list">
            <div 
              v-for="item in readingHistory" 
              :key="item.work_id"
              class="history-item"
              @click="goToReading(item.work_id)"
            >
              <img :src="item.cover_url || defaultCover" :alt="item.title" class="history-cover">
              <div class="history-info">
                <h4>{{ item.title }}</h4>
                <p>{{ item.author_name }}</p>
                <span class="history-time">{{ formatTime(item.last_read_time) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-record">暂无浏览记录</div>
        </el-tab-pane>

        <el-tab-pane name="subscriptions">
          <template #label>
            <div class="tab-icon-item tab-icon-subscriptions">
              <el-icon><Notebook /></el-icon>
              <span>订阅记录</span>
            </div>
          </template>
          <el-table
            v-if="subscriptionRecords.length > 0"
            :data="subscriptionRecords"
            border
            stripe
            class="record-table"
          >
            <el-table-column label="订阅时间" width="200">
              <template #default="scope">{{ formatDateTime(scope.row.sub_time) }}</template>
            </el-table-column>
            <el-table-column prop="work_title" label="作品" min-width="200" />
            <el-table-column label="章节" min-width="200">
              <template #default="scope">
                {{ scope.row.chapter_title || '整本订阅' }}
              </template>
            </el-table-column>
            <el-table-column label="消耗点券" width="140">
              <template #default="scope">
                {{ scope.row.amount || 0 }}
              </template>
            </el-table-column>
          </el-table>
          <div v-else class="empty-record">暂无订阅记录</div>
        </el-tab-pane>

        <el-tab-pane name="votes">
          <template #label>
            <div class="tab-icon-item tab-icon-votes">
              <el-icon><Tickets /></el-icon>
              <span>投票记录</span>
            </div>
          </template>
          <el-table
            v-if="voteRecords.length > 0"
            :data="voteRecords"
            border
            stripe
            class="record-table"
          >
            <el-table-column label="投票时间" width="200">
              <template #default="scope">{{ formatDateTime(scope.row.vote_time) }}</template>
            </el-table-column>
            <el-table-column prop="work_title" label="作品" min-width="200" />
            <el-table-column label="投票张数" width="140">
              <template #default="scope">
                {{ scope.row.count || 0 }}
              </template>
            </el-table-column>
            <el-table-column label="留言" min-width="240">
              <template #default="scope">
                {{ scope.row.message || '—' }}
              </template>
            </el-table-column>
          </el-table>
          <div v-else class="empty-record">暂无投票记录</div>
        </el-tab-pane>

        <el-tab-pane name="comments">
          <template #label>
            <div class="tab-icon-item tab-icon-comments">
              <el-icon><ChatDotRound /></el-icon>
              <span>评论记录</span>
            </div>
          </template>
          <el-table
            v-if="commentRecords.length > 0"
            :data="commentRecords"
            border
            stripe
            class="record-table"
            @row-click="viewCommentThread"
          >
            <el-table-column label="时间" width="200">
              <template #default="scope">{{ formatDateTime(scope.row.create_time) }}</template>
            </el-table-column>
            <el-table-column prop="work_title" label="作品" min-width="200" />
            <el-table-column label="类型" width="140">
              <template #default="scope">
                {{ scope.row.is_book_comment ? '全书评论' : '章节评论' }}
              </template>
            </el-table-column>
            <el-table-column label="是否追评" width="120">
              <template #default="scope">
                {{ scope.row.is_reply ? '是' : '否' }}
              </template>
            </el-table-column>
            <el-table-column label="章节" min-width="200">
              <template #default="scope">
                {{ scope.row.is_book_comment ? '—' : (scope.row.chapter_title || '章节已删除') }}
              </template>
            </el-table-column>
            <el-table-column prop="content" label="评论内容" min-width="240" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="scope">
                <el-button type="primary" size="small" @click.stop="viewCommentThread(scope.row)">
                  完整评论
                </el-button>
                <el-popconfirm
                  title="确认删除该评论及其追评吗？"
                  confirm-button-text="确定"
                  cancel-button-text="取消"
                  @confirm="deleteCommentRecord(scope.row, scope.$index)"
                >
                  <template #reference>
                    <el-button type="danger" size="small" @click.stop>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div v-else class="empty-record">暂无评论记录</div>
        </el-tab-pane>
      </el-tabs>
    </div>

  <el-dialog
    v-model="commentThreadDialogVisible"
    title="评论详情"
    width="520px"
    destroy-on-close
  >
    <div v-if="commentThreadLoading">
      <el-skeleton rows="4" animated />
    </div>
    <div v-else-if="commentThread" class="comment-thread">
      <div class="thread-top">
        <h4>{{ commentThread.reader_name }}</h4>
        <span class="thread-time">{{ formatDateTime(commentThread.create_time) }}</span>
        <p class="thread-content">{{ commentThread.content }}</p>
        <div class="thread-meta">
          <span>点赞：{{ commentThread.like_count || 0 }}</span>
          <span v-if="commentThread.chapter_id">章节评论</span>
          <span v-else>作品评论</span>
        </div>
      </div>
      <div class="thread-replies" v-if="commentThread.replies && commentThread.replies.length">
        <h5>全部追评</h5>
        <div 
          v-for="reply in commentThread.replies"
          :key="reply.comment_id"
          class="thread-reply"
        >
          <div class="reply-header">
            <span class="reply-author">{{ reply.reader_name }}</span>
            <span class="reply-time">{{ formatDateTime(reply.create_time) }}</span>
          </div>
          <p class="reply-content">{{ reply.content }}</p>
          <div class="reply-meta">点赞：{{ reply.like_count || 0 }}</div>
        </div>
      </div>
      <div v-else class="empty-thread">暂无追评</div>
    </div>
    <div v-else class="empty-thread">暂无评论数据</div>
    <template #footer>
      <el-button @click="commentThreadDialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</div>
</template>

<script>
import { 
  Delete, 
  Collection, 
  Clock, 
  Notebook, 
  Tickets, 
  ChatDotRound 
} from '@element-plus/icons-vue'
import { 
  getBookshelf, 
  getReadingHistory, 
  removeFromBookshelf, 
  getUserSubscriptionRecords, 
  getUserVoteRecords,
  getCommentHistory,
  deleteUserComment,
  getCommentThread
} from '../api'

export default {
  name: 'Bookshelf',
  components: {
    Delete,
    Collection,
    Clock,
    Notebook,
    Tickets,
    ChatDotRound
  },
  data() {
    return {
      collections: [],
      readingHistory: [],
      activeTab: 'collections',
      subscriptionRecords: [],
      voteRecords: [],
      commentRecords: [],
      loading: false,
      defaultCover: 'https://via.placeholder.com/200x280/667eea/ffffff?text=封面',
      commentThreadDialogVisible: false,
      commentThreadLoading: false,
      commentThread: null
    }
  },
  created() {
    this.loadBookshelf()
    this.loadReadingHistory()
    this.loadSubscriptionRecords()
    this.loadVoteRecords()
    this.loadCommentRecords()
  },
  methods: {
    async loadBookshelf() {
      try {
        this.loading = true
        const response = await getBookshelf()
        if (response.data.success) {
          this.collections = response.data.collections
        }
      } catch (error) {
        this.$message.error('加载书架失败')
        console.error('Load bookshelf error:', error)
      } finally {
        this.loading = false
      }
    },
    
    async loadReadingHistory() {
      try {
        const response = await getReadingHistory()
        if (response.data.success) {
          this.readingHistory = response.data.history
        }
      } catch (error) {
        console.error('Load reading history error:', error)
      }
    },
    
    async loadSubscriptionRecords() {
      try {
        const response = await getUserSubscriptionRecords({ page_size: 100 })
        if (response.data && response.data.success) {
          this.subscriptionRecords = response.data.records || []
        }
      } catch (error) {
        console.error('Load subscription records error:', error)
      }
    },

    async loadVoteRecords() {
      try {
        const response = await getUserVoteRecords({ page_size: 100 })
        if (response.data && response.data.success) {
          this.voteRecords = response.data.records || []
        }
      } catch (error) {
        console.error('Load vote records error:', error)
      }
    },

    async loadCommentRecords() {
      try {
        const response = await getCommentHistory({ page_size: 100 })
        if (response.data && response.data.success) {
          this.commentRecords = response.data.records || []
        }
      } catch (error) {
        console.error('Load comment records error:', error)
      }
    },
 
    goToReading(workId) {
      this.$router.push(`/main/reading/${workId}`)
    },
    
    goToCategories() {
      this.$router.push('/main/categories')
    },
    
    async removeFromBookshelf(workId) {
      try {
        await this.$confirm('确定要移除这本书吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await removeFromBookshelf(workId)
        if (response.data.success) {
          this.collections = this.collections.filter(work => work.work_id !== workId)
          this.$message.success('已移除')
        } else {
          this.$message.error(response.data.error || '移除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('移除失败')
          console.error('Remove from bookshelf error:', error)
        }
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
    
    formatTime(timeString) {
      if (!timeString) return ''
      const time = new Date(timeString)
      const now = new Date()
      const diff = now - time
      
      if (diff < 60000) { // 1分钟内
        return '刚刚'
      } else if (diff < 3600000) { // 1小时内
        return `${Math.floor(diff / 60000)}分钟前`
      } else if (diff < 86400000) { // 1天内
        return `${Math.floor(diff / 3600000)}小时前`
      } else {
        return time.toLocaleDateString()
      }
    },

    formatDateTime(timeString) {
      if (!timeString) return ''
      return new Date(timeString).toLocaleString()
    },

    async viewCommentThread(row) {
      if (!row || !row.comment_id) return
      this.commentThreadDialogVisible = true
      this.commentThreadLoading = true
      this.commentThread = null
      try {
        const response = await getCommentThread(row.comment_id)
        if (response.data && response.data.success) {
          this.commentThread = response.data.thread
        } else {
          this.$message.error(response.data?.error || '加载评论详情失败')
          this.commentThreadDialogVisible = false
        }
      } catch (error) {
        this.$message.error(error.response?.data?.error || '加载评论详情失败')
        console.error('View comment thread error:', error)
        this.commentThreadDialogVisible = false
      } finally {
        this.commentThreadLoading = false
      }
    },

    async deleteCommentRecord(record, index) {
      try {
        const response = await deleteUserComment(record.comment_id)
        if (response.data && response.data.success) {
          this.commentRecords.splice(index, 1)
          this.$message.success('评论已删除')
          await this.loadCommentRecords()
          if (this.commentThreadDialogVisible && this.commentThread && this.commentThread.comment_id === (record.parent_id || record.comment_id)) {
            this.commentThreadDialogVisible = false
            this.commentThread = null
          }
        } else {
          this.$message.error(response.data?.error || '删除失败')
        }
      } catch (error) {
        this.$message.error(error.response?.data?.error || '删除失败，请稍后重试')
        console.error('Delete comment record error:', error)
      }
    }
  }
}
</script>

<style scoped>
.bookshelf-container {
  position: relative;
  height: 100%;
}

/*
.bookshelf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.bookshelf-header h2 {
  color: #2c3e50;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}
*/
.bookshelf-header {
  text-align: center;
  margin-bottom: 30px;
}

.bookshelf-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.bookshelf-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 0;
}

.history-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s ease, transform 0.2s ease;
  background: #fff;
  border: 1px solid #f1f5f9;
}

.history-item:hover {
  background: #f0f2f5;
  transform: translateY(-2px);
}

.history-cover {
  width: 60px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}

.history-info {
  flex: 1;
}

.history-info h4 {
  color: #2c3e50;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 5px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-info p {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 0 0 5px 0;
}

.history-time {
  color: #bdc3c7;
  font-size: 0.8rem;
}

.bookshelf-content {
  transition: margin-right 0.3s ease;
}

.empty-bookshelf {
  text-align: center;
  padding: 60px 20px;
}

.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.book-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.book-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.book-cover {
  position: relative;
  height: 280px;
  overflow: hidden;
}

.book-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.book-status {
  position: absolute;
  top: 10px;
  right: 10px;
}

.book-info {
  padding: 15px;
}

.book-title {
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-author {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 0 0 5px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-category {
  color: #bdc3c7;
  font-size: 0.8rem;
  margin: 0 0 15px 0;
}

.book-actions {
  display: flex;
  justify-content: flex-end;
}

.bookshelf-tabs {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.bookshelf-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.bookshelf-tabs :deep(.el-tabs__nav) {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
  background: transparent;
  border: none;
}

.bookshelf-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.bookshelf-tabs :deep(.el-tabs__item) {
  padding: 0;
  border: none;
}

.bookshelf-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.tab-icon-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  font-weight: 600;
  transition: all 0.25s ease;
  border: 1px solid transparent;
  width: 100%;
}

.tab-icon-item span {
  font-size: 0.96rem;
}

.tab-icon-item .el-icon {
  font-size: 20px;
}

.tab-icon-collections {
  background: rgba(99, 102, 241, 0.12);
  color: #4f46e5;
}

.tab-icon-history {
  background: rgba(20, 184, 166, 0.12);
  color: #0f766e;
}

.tab-icon-subscriptions {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.tab-icon-votes {
  background: rgba(249, 115, 22, 0.14);
  color: #c2410c;
}

.tab-icon-comments {
  background: rgba(59, 130, 246, 0.14);
  color: #1d4ed8;
}

.bookshelf-tabs :deep(.el-tabs__item.is-active .tab-icon-collections) {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #fff;
  box-shadow: 0 12px 24px rgba(99, 102, 241, 0.25);
}

.bookshelf-tabs :deep(.el-tabs__item.is-active .tab-icon-history) {
  background: linear-gradient(135deg, #2dd4bf 0%, #14b8a6 100%);
  color: #fff;
  box-shadow: 0 12px 24px rgba(14, 180, 165, 0.25);
}

.bookshelf-tabs :deep(.el-tabs__item.is-active .tab-icon-subscriptions) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fff;
  box-shadow: 0 12px 24px rgba(234, 179, 8, 0.25);
}

.bookshelf-tabs :deep(.el-tabs__item.is-active .tab-icon-votes) {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  color: #fff;
  box-shadow: 0 12px 24px rgba(251, 146, 60, 0.25);
}

.bookshelf-tabs :deep(.el-tabs__item.is-active .tab-icon-comments) {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  color: #fff;
  box-shadow: 0 12px 24px rgba(59, 130, 246, 0.25);
}

.record-table {
  width: 100%;
}

.empty-record {
  text-align: center;
  padding: 40px 0;
  color: #94a3b8;
}

.comment-thread {
  max-height: 60vh;
  overflow-y: auto;
}

.thread-top {
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
  margin-bottom: 12px;
}

.thread-top h4 {
  margin: 0;
  color: #2c3e50;
}

.thread-time {
  display: block;
  color: #94a3b8;
  font-size: 0.85rem;
  margin: 6px 0;
}

.thread-content {
  color: #4b5563;
  line-height: 1.6;
}

.thread-meta {
  color: #94a3b8;
  font-size: 0.85rem;
  display: flex;
  gap: 16px;
}

.thread-replies h5 {
  margin: 12px 0;
  color: #2c3e50;
}

.thread-reply {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 10px;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 0.9rem;
}

.reply-content {
  margin: 6px 0;
  color: #4b5563;
}

.reply-meta {
  color: #94a3b8;
  font-size: 0.85rem;
}

.empty-thread {
  text-align: center;
  color: #94a3b8;
  padding: 20px 0;
}

@media (max-width: 768px) {
  .books-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
  }
  
  .book-cover {
    height: 200px;
  }
}
</style>

