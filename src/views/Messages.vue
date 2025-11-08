<template>
  <div class="messages-container">
    <div class="messages-header">
      <h2>消息通知</h2>
      <p>查看您的所有消息和通知</p>
    </div>
    
    <div class="messages-content">
      <div class="messages-sidebar">
        <div class="message-filters">
          <h3>消息分类</h3>
          <div class="filter-list">
            <div 
              v-for="filter in messageFilters" 
              :key="filter.type"
              class="filter-item"
              :class="{ active: selectedFilter === filter.type }"
              @click="selectFilter(filter.type)"
            >
              <el-icon :class="filter.icon"></el-icon>
              <span>{{ filter.label }}</span>
              <el-badge 
                v-if="filter.count > 0" 
                :value="filter.count" 
                class="filter-badge"
              />
            </div>
          </div>
        </div>
        
        <div class="message-actions">
          <el-button 
            type="primary" 
            @click="markAllAsRead"
            :disabled="unreadCount === 0"
          >
            <el-icon><Check /></el-icon>
            全部已读
          </el-button>
          <el-button @click="clearAllMessages">
            <el-icon><Delete /></el-icon>
            清空消息
          </el-button>
        </div>
      </div>
      
      <div class="messages-main">
        <div class="message-list" v-if="messages.length > 0">
          <div 
            v-for="message in messages" 
            :key="message.message_id"
            class="message-item"
            :class="{ unread: !message.is_read }"
            @click="readMessage(message)"
          >
            <div class="message-avatar">
              <el-avatar :size="40">
                <el-icon><Message /></el-icon>
              </el-avatar>
            </div>
            
            <div class="message-content">
              <div class="message-header">
                <h4 class="message-title">{{ getMessageTitle(message) }}</h4>
                <span class="message-time">{{ formatTime(message.send_time) }}</span>
              </div>
              
              <p class="message-text">{{ message.content }}</p>
              
              <div class="message-meta">
                <el-tag 
                  :type="getMessageTypeColor(message.message_type)"
                  size="small"
                >
                  {{ getMessageTypeText(message.message_type) }}
                </el-tag>
                <span v-if="!message.is_read" class="unread-indicator">未读</span>
              </div>
            </div>
            
            <div class="message-actions">
              <el-button 
                type="text" 
                @click.stop="deleteMessage(message.message_id)"
                class="delete-btn"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        
        <div v-else class="empty-messages">
          <el-empty description="暂无消息">
            <el-button type="primary" @click="refreshMessages">
              刷新消息
            </el-button>
          </el-empty>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-container" v-if="messages.length > 0">
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
import { 
  Check, Delete, Message, Bell, Star, ChatDotRound, 
  Trophy, User, Setting 
} from '@element-plus/icons-vue'
import { getMessages, markMessageRead, markAllMessagesRead, deleteMessage } from '../api'

export default {
  name: 'Messages',
  components: {
    Check,
    Delete,
    Message,
    Bell,
    Star,
    ChatDotRound,
    Trophy,
    User,
    Setting
  },
  data() {
    return {
      messages: [],
      selectedFilter: '',
      currentPage: 1,
      pageSize: 20,
      totalCount: 0,
      unreadCount: 0,
      unreadTypeCounts: {},
      messageFilters: [
        { type: '', label: '全部消息', icon: 'Message', count: 0 },
        { type: '101', label: '订阅通知', icon: 'Bell', count: 0 },
        { type: '102', label: '投票通知', icon: 'Star', count: 0 },
        { type: '103', label: '评论回复', icon: 'ChatDotRound', count: 0 },
        { type: '201', label: '签约通知', icon: 'Trophy', count: 0 },
        { type: '202', label: '审核结果', icon: 'Check', count: 0 },
        { type: '301', label: '作品更新', icon: 'Bell', count: 0 },
        { type: '501', label: '系统通知', icon: 'Setting', count: 0 }
      ]
    }
  },
  created() {
    this.loadMessages()
  },
  methods: {
    async loadMessages() {
      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize
        }
        
        if (this.selectedFilter) {
          params.type = this.selectedFilter
        }
        
        const response = await getMessages(params)
        if (response.data.success) {
          const { messages = [], total, unread_count: unreadCount, type_counts: typeCounts } = response.data
          this.messages = messages
          this.totalCount = typeof total === 'number' ? total : this.messages.length
          this.setUnreadState(unreadCount, typeCounts)
        }
      } catch (error) {
        this.$message.error('加载消息失败')
        console.error('Load messages error:', error)
      }
    },
    
    selectFilter(type) {
      this.selectedFilter = type
      this.currentPage = 1
      this.loadMessages()
    },
    
    async readMessage(message) {
      if (!message.is_read) {
        try {
          await markMessageRead(message.message_id)
          message.is_read = 1
          this.adjustUnreadForMessage(message.message_type, -1)
        } catch (error) {
          console.error('Mark message as read error:', error)
        }
      }
    },
    
    async deleteMessage(messageId) {
      try {
        await this.$confirm('确定要删除这条消息吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        const targetMessage = this.messages.find(msg => msg.message_id === messageId)
        await deleteMessage(messageId)
        this.messages = this.messages.filter(msg => msg.message_id !== messageId)
        this.$message.success('消息已删除')
        if (targetMessage && !targetMessage.is_read) {
          this.adjustUnreadForMessage(targetMessage.message_type, -1)
        }
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('删除消息失败')
          console.error('Delete message error:', error)
        }
      }
    },
    
    async markAllAsRead() {
      try {
        await markAllMessagesRead()
        this.messages.forEach(message => {
          message.is_read = 1
        })
        this.setUnreadState(0, {})
        this.$message.success('所有消息已标记为已读')
      } catch (error) {
        this.$message.error('操作失败')
        console.error('Mark all as read error:', error)
      }
    },
    
    async clearAllMessages() {
      try {
        await this.$confirm('确定要清空所有消息吗？此操作不可恢复！', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        // await api.delete('/messages/clear-all/')
        this.messages = []
        this.setUnreadState(0, {})
        this.$message.success('所有消息已清空')
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('清空消息失败')
          console.error('Clear all messages error:', error)
        }
      }
    },
    
    refreshMessages() {
      this.loadMessages()
    },
    
    handlePageChange(page) {
      this.currentPage = page
      this.loadMessages()
    },
    
    updateUnreadCount() {
      this.setUnreadState(null, null)
    },

    setUnreadState(unreadCount, typeCounts) {
      let normalizedCounts = null
      if (typeCounts && typeof typeCounts === 'object') {
        normalizedCounts = {}
        Object.keys(typeCounts).forEach(key => {
          const normalizedKey = key.toString()
          const value = Number(typeCounts[key])
          normalizedCounts[normalizedKey] = Number.isFinite(value) && value > 0 ? Math.floor(value) : 0
        })
      }

      if (normalizedCounts === null) {
        normalizedCounts = this.calculateLocalTypeCounts()
      }

      const normalizedUnread = Number.isFinite(unreadCount)
        ? Math.max(0, Math.floor(unreadCount))
        : Object.values(normalizedCounts).reduce((sum, value) => sum + value, 0)

      this.unreadCount = normalizedUnread
      this.$store.commit('SET_UNREAD_COUNT', this.unreadCount)
      this.unreadTypeCounts = { ...normalizedCounts }
      this.applyFilterCounts(this.unreadTypeCounts)
    },

    calculateLocalTypeCounts() {
      const counts = {}
      this.messages.forEach(message => {
        if (!message.is_read) {
          const key = message.message_type ? message.message_type.toString() : ''
          counts[key] = (counts[key] || 0) + 1
        }
      })
      return counts
    },

    applyFilterCounts(typeCounts) {
      const counts = typeCounts || {}
      this.messageFilters = this.messageFilters.map(filter => {
        const nextFilter = { ...filter }
        if (filter.type === '') {
          nextFilter.count = this.unreadCount
        } else {
          const key = filter.type.toString()
          nextFilter.count = counts[key] || 0
        }
        return nextFilter
      })
    },

    adjustUnreadForMessage(messageType, delta) {
      if (!delta) {
        return
      }
      const nextTotal = Math.max(0, this.unreadCount + delta)
      this.unreadCount = nextTotal
      this.$store.commit('SET_UNREAD_COUNT', this.unreadCount)

      const key = messageType ? messageType.toString() : ''
      const updatedCounts = { ...this.unreadTypeCounts }
      if (key) {
        const current = updatedCounts[key] || 0
        const nextValue = Math.max(0, current + delta)
        if (nextValue > 0) {
          updatedCounts[key] = nextValue
        } else {
          delete updatedCounts[key]
        }
      }
      this.unreadTypeCounts = updatedCounts
      this.applyFilterCounts(updatedCounts)
    },
    
    getMessageTitle(message) {
      const titles = {
        '101': '订阅通知',
        '102': '投票通知',
        '103': '评论回复',
        '201': '签约通知',
        '202': '审核结果',
        '301': '作品更新',
        '501': '系统通知'
      }
      return titles[message.message_type] || '系统消息'
    },
    
    getMessageTypeText(type) {
      const texts = {
        '101': '订阅',
        '102': '投票',
        '103': '评论',
        '201': '签约',
        '202': '审核',
        '301': '更新',
        '501': '系统'
      }
      return texts[type] || '消息'
    },
    
    getMessageTypeColor(type) {
      const colors = {
        '101': 'success',
        '102': 'warning',
        '103': 'info',
        '201': 'primary',
        '202': 'danger',
        '301': 'success',
        '501': 'info'
      }
      return colors[type] || 'info'
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
      } else if (diff < 604800000) { // 1周内
        return `${Math.floor(diff / 86400000)}天前`
      } else {
        return time.toLocaleDateString()
      }
    }
  }
}
</script>

<style scoped>
.messages-container {
  height: 100%;
}

.messages-header {
  text-align: center;
  margin-bottom: 30px;
}

.messages-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.messages-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.messages-content {
  display: flex;
  gap: 30px;
  height: calc(100% - 120px);
}

.messages-sidebar {
  width: 250px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-filters {
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.message-filters h3 {
  color: #2c3e50;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.filter-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.filter-item:hover {
  background: #f0f2f5;
}

.filter-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.filter-item .el-icon {
  font-size: 1.1rem;
}

.filter-badge {
  margin-left: auto;
}

.message-actions {
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-actions .el-button {
  width: 100%;
  border-radius: 8px;
  padding: 12px;
}

.messages-main {
  flex: 1;
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.message-list {
  flex: 1;
  overflow-y: auto;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.3s ease;
  position: relative;
}

.message-item:hover {
  background: #f8f9fa;
}

.message-item.unread {
  background: #f0f8ff;
  border-left: 4px solid #667eea;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-title {
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.message-time {
  color: #7f8c8d;
  font-size: 0.85rem;
}

.message-text {
  color: #5a6c7d;
  font-size: 0.95rem;
  line-height: 1.5;
  margin: 0 0 10px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.unread-indicator {
  color: #667eea;
  font-size: 0.8rem;
  font-weight: 600;
}

.message-actions {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.delete-btn {
  color: #f56565;
}

.delete-btn:hover {
  color: #e53e3e;
}

.empty-messages {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.pagination {
  margin: 0;
}

@media (max-width: 768px) {
  .messages-content {
    flex-direction: column;
    gap: 20px;
  }
  
  .messages-sidebar {
    width: 100%;
  }
  
  .filter-list {
    flex-direction: row;
    flex-wrap: wrap;
  }
  
  .filter-item {
    flex: 1;
    min-width: 120px;
  }
  
  .message-item {
    padding: 15px;
  }
  
  .message-actions {
    opacity: 1;
  }
}
</style>

