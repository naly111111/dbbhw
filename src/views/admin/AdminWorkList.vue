<template>
  <div class="admin-page">
    <div class="card-panel">
      <div class="panel-header">
        <div class="title">
          <h3>作品状态总览</h3>
          <p>审核作品可见性、章节更新与互动能力</p>
        </div>
        <div class="filters">
          <el-input
            v-model="filters.search"
            placeholder="作品标题 / 作者名称"
            clearable
            :prefix-icon="searchIcon"
            @keyup.enter.native="handleFilter"
          />
          <el-select v-model="filters.status" placeholder="作品状态" clearable @change="handleFilter">
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

      <el-table :data="works" border stripe v-loading="loading" class="work-table">
        <el-table-column prop="title" label="作品" min-width="220">
          <template #default="{ row }">
            <div class="work-info">
              <div class="work-title">{{ row.title }}</div>
              <div class="work-meta">
                <span>作者：{{ row.author_name || '未知' }}</span>
                <span>ID：{{ row.work_id }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="作品状态" width="170">
          <template #default="{ row }">
            <el-select
              :model-value="row.status"
              size="small"
              :disabled="isStatusLoading(row.work_id)"
              @change="(val) => handleStatusChange(row, val)"
            >
              <el-option
                v-for="item in statusOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="强制限制" min-width="360">
          <template #default="{ row }">
            <div class="moderation-grid">
              <div
                v-for="item in moderationList"
                :key="item.key"
                class="moderation-item"
              >
                <span>{{ item.label }}</span>
                <el-switch
                  :model-value="row.moderation[item.key]"
                  :loading="isModerationLoading(row.work_id, item.key)"
                  active-text="已限制"
                  inactive-text="正常"
                  inline-prompt
                  @change="(val) => handleModerationToggle(row, item.key, val)"
                />
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="200">
          <template #default="{ row }">
            <div class="note-cell">
              <p>{{ row.moderation.note || '暂无备注' }}</p>
              <el-button type="primary" link size="small" @click="() => editNote(row)">
                编辑备注
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="update_time" label="最近更新" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.update_time) || '无' }}
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

    <el-dialog
      v-model="noteDialog.visible"
      title="编辑作品备注"
      width="480px"
    >
      <el-form label-position="top">
        <el-form-item label="备注内容">
          <el-input
            v-model="noteDialog.note"
            type="textarea"
            :rows="4"
            maxlength="300"
            show-word-limit
            placeholder="可用于记录管理员处理说明，对作者展示"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="noteDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="noteDialog.loading" @click="submitNote">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  fetchAdminWorks,
  updateWorkModeration
} from '@/api'

export default {
  name: 'AdminWorkList',
  data() {
    return {
      loading: false,
      works: [],
      filters: {
        search: '',
        status: ''
      },
      pagination: {
        page: 1,
        pageSize: 20,
        total: 0
      },
      statusOptions: [
        { label: '草稿', value: 0 },
        { label: '连载中', value: 1 },
        { label: '完结', value: 2 },
        { label: '下架', value: 3 }
      ],
      moderationList: [
        { key: 'is_hidden', label: '作品可见性' },
        { key: 'chapters_blocked', label: '章节访问' },
        { key: 'updates_blocked', label: '作品更新' },
        { key: 'subscriptions_blocked', label: '订阅行为' },
        { key: 'votes_blocked', label: '投票行为' }
      ],
      moderationLoading: {},
      statusLoading: {},
      noteDialog: {
        visible: false,
        work: null,
        note: '',
        loading: false
      }
    }
  },
  created() {
    this.fetchWorks()
  },
  computed: {
    searchIcon() {
      return Search
    }
  },
  methods: {
    async fetchWorks() {
      this.loading = true
      try {
        const params = {
          search: this.filters.search || undefined,
          status: this.filters.status !== '' ? this.filters.status : undefined,
          page: this.pagination.page,
          page_size: this.pagination.pageSize
        }
        const { data } = await fetchAdminWorks(params)
        if (data.success) {
          this.works = data.works || []
          this.pagination.total = data.total || 0
        } else {
          ElMessage.error(data.error || '获取作品列表失败')
        }
      } catch (error) {
        ElMessage.error(error?.message || '获取作品列表失败')
      } finally {
        this.loading = false
      }
    },
    handleFilter() {
      this.pagination.page = 1
      this.fetchWorks()
    },
    handleReset() {
      this.filters = { search: '', status: '' }
      this.pagination.page = 1
      this.fetchWorks()
    },
    handlePageChange(page) {
      this.pagination.page = page
      this.fetchWorks()
    },
    handleSizeChange(size) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      this.fetchWorks()
    },
    async handleModerationToggle(work, key, value) {
      const mapKey = `${work.work_id}_${key}`
      const previousValue = Boolean(work.moderation[key])
      work.moderation[key] = value
      this.moderationLoading = { ...this.moderationLoading, [mapKey]: true }
      try {
        const reason = await this.askReason('请填写调整原因（可选）')
        if (reason === null) {
          work.moderation[key] = previousValue
          return
        }
        const payload = { [key]: value, reason }
        const { data } = await updateWorkModeration(work.work_id, payload)
        if (data.success) {
          work.moderation[key] = value
          ElMessage.success('作品限制已更新')
        } else {
          work.moderation[key] = previousValue
          ElMessage.error(data.error || '更新失败')
        }
      } catch (error) {
        work.moderation[key] = previousValue
        if (error !== null) {
          ElMessage.error(error?.message || '更新失败')
        }
      } finally {
        const { [mapKey]: _ignore, ...rest } = this.moderationLoading
        this.moderationLoading = rest
      }
    },
    async handleStatusChange(work, status) {
      const mapKey = `${work.work_id}_status`
      const previousStatus = work.status
      let shouldRefresh = false
      this.statusLoading = { ...this.statusLoading, [mapKey]: true }
      try {
        const reason = await this.askReason('请填写调整原因（可选）')
        if (reason === null) {
          this.$nextTick(() => {
            work.status = previousStatus
          })
          return
        }
        const payload = { status, reason }
        const { data } = await updateWorkModeration(work.work_id, payload)
        if (data.success) {
          work.status = status
          ElMessage.success('作品状态已更新')
          shouldRefresh = true
        } else {
          ElMessage.error(data.error || '更新失败')
          work.status = previousStatus
        }
      } catch (error) {
        if (error !== null) {
          ElMessage.error(error?.message || '更新失败')
        }
        work.status = previousStatus
      } finally {
        const { [mapKey]: _ignore, ...rest } = this.statusLoading
        this.statusLoading = rest
        if (shouldRefresh) {
          this.fetchWorks()
        }
      }
    },
    editNote(work) {
      this.noteDialog.work = work
      this.noteDialog.note = work.moderation.note || ''
      this.noteDialog.visible = true
    },
    async submitNote() {
      if (!this.noteDialog.work) {
        return
      }
      this.noteDialog.loading = true
      try {
        const payload = {
          note: this.noteDialog.note,
          reason: ''
        }
        const { data } = await updateWorkModeration(this.noteDialog.work.work_id, payload)
        if (data.success) {
          this.noteDialog.work.moderation.note = this.noteDialog.note
          ElMessage.success('备注已更新')
          this.noteDialog.visible = false
        } else {
          ElMessage.error(data.error || '备注更新失败')
        }
      } catch (error) {
        ElMessage.error(error?.message || '备注更新失败')
      } finally {
        this.noteDialog.loading = false
      }
    },
    async askReason(message) {
      try {
        const { value } = await ElMessageBox.prompt(message, '操作确认', {
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
    isModerationLoading(workId, key) {
      return !!this.moderationLoading[`${workId}_${key}`]
    },
    isStatusLoading(workId) {
      return !!this.statusLoading[`${workId}_status`]
    },
    formatDate(value) {
      if (!value) {
        return ''
      }
      return value.replace('T', ' ').slice(0, 19)
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

.work-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.work-title {
  font-weight: 600;
  color: #1f2d3d;
}

.work-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #5c6c7c;
}

.moderation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px 16px;
}

.moderation-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #4c596a;
}

.note-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #4c596a;
}

.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

@media (max-width: 1024px) {
  .moderation-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }
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

  .moderation-grid {
    grid-template-columns: 1fr;
  }
}
</style>


