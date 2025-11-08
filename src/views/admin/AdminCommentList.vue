<template>
  <div class="admin-page">
    <div class="card-panel">
      <div class="panel-header">
        <div class="title">
          <h3>评论巡查管理</h3>
          <p>快速定位违规言论并通知相关用户</p>
        </div>
        <div class="filters">
          <el-input
            v-model="filters.search"
            placeholder="评论内容 / 作品标题 / 用户"
            clearable
            :prefix-icon="searchIcon"
            @keyup.enter.native="handleFilter"
          />
          <el-select v-model="filters.status" placeholder="评论状态" clearable @change="handleFilter">
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-button type="primary" @click="handleFilter">筛选</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </div>

      <el-table :data="comments" border stripe v-loading="loading" class="comment-table">
        <el-table-column prop="comment_id" label="ID" width="80" />
        <el-table-column label="评论内容" min-width="260">
          <template #default="{ row }">
            <el-popover placement="top-start" trigger="hover" :content="row.content">
              <template #reference>
                <div class="comment-content">{{ truncate(row.content, 80) }}</div>
              </template>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column label="所属作品" min-width="200">
          <template #default="{ row }">
            <div class="work-cell">
              <span>{{ row.work_title || '-' }}</span>
              <el-tag size="small" v-if="row.chapter_id">章节 {{ row.chapter_id }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="评论者" min-width="140">
          <template #default="{ row }">
            <div class="user-cell">
              <span>{{ row.reader_name || '未知用户' }}</span>
              <span class="user-id">ID：{{ row.reader_id }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="发表时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.create_time) || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '正常' : '已删除' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              :disabled="row.status === 0"
              :loading="isDeleting(row.comment_id)"
              @click="() => handleDelete(row)"
            >
              删除评论
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-area">
        <el-pagination
          background
          layout="total, prev, pager, next, sizes"
          :page-sizes="[10, 20, 30, 50]"
          :page-size="pagination.pageSize"
          :current-page="pagination.page"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { fetchAdminComments, deleteAdminComment } from '@/api'

export default {
  name: 'AdminCommentList',
  data() {
    return {
      loading: false,
      comments: [],
      filters: {
        search: '',
        status: ''
      },
      pagination: {
        page: 1,
        pageSize: 20,
        total: 0
      },
      deleting: {},
      statusOptions: [
        { label: '全部状态', value: '' },
        { label: '正常', value: 1 },
        { label: '已删除', value: 0 }
      ]
    }
  },
  created() {
    this.fetchComments()
  },
  computed: {
    searchIcon() {
      return Search
    }
  },
  methods: {
    async fetchComments() {
      this.loading = true
      try {
        const params = {
          search: this.filters.search || undefined,
          status: this.filters.status !== '' ? this.filters.status : undefined,
          page: this.pagination.page,
          page_size: this.pagination.pageSize
        }
        const { data } = await fetchAdminComments(params)
        if (data.success) {
          this.comments = data.comments || []
          this.pagination.total = data.total || 0
        } else {
          ElMessage.error(data.error || '获取评论列表失败')
        }
      } catch (error) {
        ElMessage.error(error?.message || '获取评论列表失败')
      } finally {
        this.loading = false
      }
    },
    handleFilter() {
      this.pagination.page = 1
      this.fetchComments()
    },
    handleReset() {
      this.filters = { search: '', status: '' }
      this.pagination.page = 1
      this.fetchComments()
    },
    handlePageChange(page) {
      this.pagination.page = page
      this.fetchComments()
    },
    handleSizeChange(size) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      this.fetchComments()
    },
    async handleDelete(comment) {
      if (comment.status === 0) {
        return
      }
      const mapKey = `${comment.comment_id}`
      this.deleting = { ...this.deleting, [mapKey]: true }
      try {
        const reason = await this.askReason('删除原因（可选）')
        if (reason === null) {
          return
        }
        const { data } = await deleteAdminComment(comment.comment_id, { reason })
        if (data.success) {
          comment.status = 0
          ElMessage.success('评论已删除并通知相关用户')
          this.fetchComments()
        } else {
          ElMessage.error(data.error || '删除失败')
        }
      } catch (error) {
        if (error !== null) {
          ElMessage.error(error?.message || '删除失败')
        }
      } finally {
        const { [mapKey]: _ignore, ...rest } = this.deleting
        this.deleting = rest
      }
    },
    isDeleting(commentId) {
      return !!this.deleting[`${commentId}`]
    },
    async askReason(message) {
      try {
        const { value } = await ElMessageBox.prompt(message, '删除确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputType: 'textarea',
          inputPlaceholder: '可留空，最长200字',
          inputValidator: () => true,
          inputMaxlength: 200,
          draggable: true
        })
        return (value || '').trim()
      } catch (error) {
        return null
      }
    },
    formatDate(value) {
      if (!value) {
        return ''
      }
      return value.replace('T', ' ').slice(0, 19)
    },
    truncate(text, length) {
      if (!text) {
        return ''
      }
      if (text.length <= length) {
        return text
      }
      return `${text.slice(0, length)}...`
    }
  }
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-panel {
  background: #ffffff;
  border-radius: 14px;
  padding: 22px 24px 28px;
  box-shadow: 0 8px 20px rgba(31, 35, 53, 0.06);
}

.panel-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-header .title h3 {
  margin: 0;
  font-size: 20px;
  color: #1f2d3d;
}

.panel-header .title p {
  margin: 6px 0 0;
  color: #5c6c7c;
  font-size: 14px;
}

.filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filters :deep(.el-input),
.filters :deep(.el-select) {
  width: 200px;
}

.comment-table {
  margin-top: 10px;
}

.comment-content {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #334155;
}

.work-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #445066;
}

.user-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: #445066;
}

.user-id {
  font-size: 12px;
  color: #8893a5;
}

.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

@media (max-width: 768px) {
  .filters {
    width: 100%;
    justify-content: flex-start;
  }

  .filters :deep(.el-input),
  .filters :deep(.el-select) {
    width: 100%;
  }
}
</style>


