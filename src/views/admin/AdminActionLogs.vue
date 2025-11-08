<template>
  <div class="admin-page logs-page">
    <div class="card-panel">
      <div class="panel-header">
        <div class="title">
          <h3>系统行为日志</h3>
          <p>实时查看管理员与平台用户的关键操作记录，支持条件筛选与溯源</p>
        </div>
      </div>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="管理员日志" name="admin">
          <div class="filters">
            <el-input
              v-model="adminState.filters.adminId"
              placeholder="管理员 ID"
              clearable
              @keyup.enter.native="handleSearch('admin')"
            />
            <el-select
              v-model="adminState.filters.targetType"
              placeholder="目标类型"
              clearable
            >
              <el-option
                v-for="item in adminTargetTypes"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-input
              v-model="adminState.filters.action"
              placeholder="操作标识（action）"
              clearable
              @keyup.enter.native="handleSearch('admin')"
            />
            <el-input
              v-model="adminState.filters.keyword"
              placeholder="详情 / 附加信息关键字"
              clearable
              @keyup.enter.native="handleSearch('admin')"
            />
            <el-date-picker
              v-model="adminState.filters.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              value-format="YYYY-MM-DDTHH:mm:ss"
              :default-time="defaultRangeTime"
            />
            <div class="filter-actions">
              <el-button type="primary" @click="handleSearch('admin')">筛选</el-button>
              <el-button @click="handleReset('admin')">重置</el-button>
            </div>
          </div>

          <el-table
            :data="adminState.logs"
            border
            stripe
            v-loading="adminState.loading"
            class="logs-table"
          >
            <el-table-column prop="create_time" label="时间" min-width="170">
              <template #default="{ row }">
                {{ formatDateTime(row.create_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="admin_id" label="管理员 ID" min-width="120" />
            <el-table-column prop="action" label="操作" min-width="160" />
            <el-table-column prop="target_type" label="目标类型" min-width="110">
              <template #default="{ row }">
                {{ formatAdminTarget(row.target_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="target_id" label="目标 ID" min-width="120" />
            <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
            <el-table-column prop="extra" label="附加数据" min-width="200">
              <template #default="{ row }">
                <span>{{ formatExtra(row.extra) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="ip_address" label="IP" min-width="140" />
            <el-table-column prop="user_agent" label="User-Agent" min-width="240" show-overflow-tooltip />
          </el-table>

          <div class="pagination-area">
            <el-pagination
              background
              layout="total, prev, pager, next, sizes"
              :page-sizes="[10, 20, 30, 50]"
              :page-size="adminState.pagination.pageSize"
              :current-page="adminState.pagination.page"
              :total="adminState.pagination.total"
              @size-change="(val) => handleSizeChange('admin', val)"
              @current-change="(val) => handlePageChange('admin', val)"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="用户日志" name="user">
          <div class="filters">
            <el-input
              v-model="userState.filters.userId"
              placeholder="用户 ID"
              clearable
              @keyup.enter.native="handleSearch('user')"
            />
            <el-select
              v-model="userState.filters.targetType"
              placeholder="目标类型"
              clearable
            >
              <el-option
                v-for="item in userTargetTypes"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-input
              v-model="userState.filters.action"
              placeholder="操作标识（action）"
              clearable
              @keyup.enter.native="handleSearch('user')"
            />
            <el-input
              v-model="userState.filters.keyword"
              placeholder="详情 / 附加信息关键字"
              clearable
              @keyup.enter.native="handleSearch('user')"
            />
            <el-date-picker
              v-model="userState.filters.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              value-format="YYYY-MM-DDTHH:mm:ss"
              :default-time="defaultRangeTime"
            />
            <div class="filter-actions">
              <el-button type="primary" @click="handleSearch('user')">筛选</el-button>
              <el-button @click="handleReset('user')">重置</el-button>
            </div>
          </div>

          <el-table
            :data="userState.logs"
            border
            stripe
            v-loading="userState.loading"
            class="logs-table"
          >
            <el-table-column prop="create_time" label="时间" min-width="170">
              <template #default="{ row }">
                {{ formatDateTime(row.create_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="user_id" label="用户 ID" min-width="120" />
            <el-table-column prop="action" label="操作" min-width="160" />
            <el-table-column prop="target_type" label="目标类型" min-width="110">
              <template #default="{ row }">
                {{ formatUserTarget(row.target_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="target_id" label="目标 ID" min-width="120" />
            <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
            <el-table-column prop="extra" label="附加数据" min-width="200">
              <template #default="{ row }">
                <span>{{ formatExtra(row.extra) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="ip_address" label="IP" min-width="140" />
            <el-table-column prop="user_agent" label="User-Agent" min-width="240" show-overflow-tooltip />
          </el-table>

          <div class="pagination-area">
            <el-pagination
              background
              layout="total, prev, pager, next, sizes"
              :page-sizes="[10, 20, 30, 50]"
              :page-size="userState.pagination.pageSize"
              :current-page="userState.pagination.page"
              :total="userState.pagination.total"
              @size-change="(val) => handleSizeChange('user', val)"
              @current-change="(val) => handlePageChange('user', val)"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import { fetchAdminActionLogs, fetchUserActionLogs } from '@/api'

const buildDefaultState = () => ({
  loading: false,
  logs: [],
  filters: {
    adminId: '',
    userId: '',
    targetType: '',
    action: '',
    keyword: '',
    dateRange: []
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0
  },
  loaded: false
})

export default {
  name: 'AdminActionLogs',
  data() {
    return {
      activeTab: 'admin',
      adminState: buildDefaultState(),
      userState: buildDefaultState(),
      adminTargetTypes: [
        { label: '全部目标', value: '' },
        { label: '系统', value: 0 },
        { label: '用户', value: 1 },
        { label: '作品', value: 2 },
        { label: '评论', value: 3 },
        { label: '章节', value: 4 }
      ],
      userTargetTypes: [
        { label: '全部目标', value: '' },
        { label: '未指定', value: 0 },
        { label: '作品', value: 1 },
        { label: '章节', value: 2 },
        { label: '评论', value: 3 },
        { label: '个人资料', value: 4 },
        { label: '书架', value: 5 },
        { label: '订阅', value: 6 }
      ],
      defaultRangeTime: ['00:00:00', '23:59:59']
    }
  },
  created() {
    this.fetchLogs('admin')
  },
  methods: {
    async fetchLogs(tab) {
      const state = tab === 'admin' ? this.adminState : this.userState
      state.loading = true
      try {
        const params = this.buildParams(tab)
        const request = tab === 'admin' ? fetchAdminActionLogs : fetchUserActionLogs
        const { data } = await request(params)
        if (data.success) {
          state.logs = data.logs || []
          state.pagination.total = data.total || 0
          state.loaded = true
        } else {
          ElMessage.error(data.error || '日志获取失败')
        }
      } catch (error) {
        ElMessage.error(error?.message || '日志获取失败')
      } finally {
        state.loading = false
      }
    },
    buildParams(tab) {
      const state = tab === 'admin' ? this.adminState : this.userState
      const filters = state.filters
      const params = {
        page: state.pagination.page,
        page_size: state.pagination.pageSize
      }
      if (tab === 'admin' && filters.adminId) {
        params.admin_id = filters.adminId.trim()
      }
      if (tab === 'user' && filters.userId) {
        params.user_id = filters.userId.trim()
      }
      if (filters.targetType !== '') {
        params.target_type = filters.targetType
      }
      if (filters.action) {
        params.action = filters.action.trim()
      }
      if (filters.keyword) {
        params.keyword = filters.keyword.trim()
      }
      if (Array.isArray(filters.dateRange) && filters.dateRange.length === 2) {
        params.start_time = filters.dateRange[0]
        params.end_time = filters.dateRange[1]
      }
      return params
    },
    handleSearch(tab) {
      const state = tab === 'admin' ? this.adminState : this.userState
      state.pagination.page = 1
      this.fetchLogs(tab)
    },
    handleReset(tab) {
      const state = tab === 'admin' ? this.adminState : this.userState
      state.filters = {
        adminId: '',
        userId: '',
        targetType: '',
        action: '',
        keyword: '',
        dateRange: []
      }
      state.pagination.page = 1
      this.fetchLogs(tab)
    },
    handlePageChange(tab, page) {
      const state = tab === 'admin' ? this.adminState : this.userState
      state.pagination.page = page
      this.fetchLogs(tab)
    },
    handleSizeChange(tab, size) {
      const state = tab === 'admin' ? this.adminState : this.userState
      state.pagination.pageSize = size
      state.pagination.page = 1
      this.fetchLogs(tab)
    },
    handleTabChange(tab) {
      if (tab === 'user' && !this.userState.loaded) {
        this.fetchLogs('user')
      }
    },
    formatDateTime(value) {
      if (!value) {
        return '-'
      }
      return value.replace('T', ' ').slice(0, 19)
    },
    formatAdminTarget(value) {
      const map = {
        0: '系统',
        1: '用户',
        2: '作品',
        3: '评论',
        4: '章节'
      }
      return map[value] ?? '未知'
    },
    formatUserTarget(value) {
      const map = {
        0: '未指定',
        1: '作品',
        2: '章节',
        3: '评论',
        4: '个人资料',
        5: '书架',
        6: '订阅'
      }
      return map[value] ?? '未知'
    },
    formatExtra(extra) {
      if (extra === null || extra === undefined || extra === '') {
        return '-'
      }
      if (typeof extra === 'object') {
        try {
          return JSON.stringify(extra)
        } catch (error) {
          return String(extra)
        }
      }
      try {
        const parsed = JSON.parse(extra)
        return typeof parsed === 'object' ? JSON.stringify(parsed) : String(parsed)
      } catch (error) {
        return String(extra)
      }
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
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
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
  margin-bottom: 16px;
}

.filters :deep(.el-input),
.filters :deep(.el-select) {
  width: 180px;
}

.filters :deep(.el-date-editor) {
  width: 320px;
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logs-table {
  margin-top: 10px;
}

.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

@media (max-width: 1024px) {
  .filters :deep(.el-input),
  .filters :deep(.el-select) {
    width: 160px;
  }

  .filters :deep(.el-date-editor) {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .filters {
    width: 100%;
    justify-content: flex-start;
  }

  .filters :deep(.el-input),
  .filters :deep(.el-select),
  .filters :deep(.el-date-editor) {
    width: 100%;
  }

  .filter-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>


