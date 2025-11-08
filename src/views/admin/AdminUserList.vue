<template>
  <div class="admin-page">
    <div class="card-panel">
      <div class="panel-header">
        <div class="title">
          <h3>用户行为权限管理</h3>
          <p>普通用户同时具备读者与作者能力，可在此统一管控</p>
        </div>
        <div class="filters">
          <el-input
            v-model="filters.search"
            placeholder="用户名 / 邮箱 / 手机"
            clearable
            :prefix-icon="searchIcon"
            @keyup.enter.native="handleFilter"
          />
          <el-select v-model="filters.role" placeholder="用户类型" clearable @change="handleFilter">
            <el-option
              v-for="item in roleOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-select v-model="filters.status" placeholder="账号状态" clearable @change="handleFilter">
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

      <el-table :data="users" border stripe v-loading="loading" class="user-table">
        <el-table-column prop="username" label="用户名" min-width="140" fixed="left">
          <template #default="{ row }">
            <div class="user-cell">
              <span class="name">{{ row.username }}</span>
              <div class="tag-group">
                <template v-if="row.role === 3">
                  <el-tag size="small" type="info">编辑</el-tag>
                </template>
                <template v-else>
                  <el-tag size="small" type="warning">普通用户</el-tag>
                  <el-tag size="small" type="success">读者</el-tag>
                  <el-tag size="small" type="primary">作者</el-tag>
                </template>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="160">
          <template #default="{ row }">
            <span>{{ row.email || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" min-width="140">
          <template #default="{ row }">
            <span>{{ row.phone || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" min-width="180">
          <template #default="{ row }">
            <span>{{ formatDate(row.create_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_time" label="最近登录" min-width="180">
          <template #default="{ row }">
            <span>{{ formatDate(row.last_login_time) || '尚未登录' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="账号状态" width="160">
          <template #default="{ row }">
            <div class="status-cell">
              <el-tag :type="row.status === 1 ? 'success' : 'danger'">
                {{ row.status === 1 ? '正常' : '禁用' }}
              </el-tag>
              <el-button
                size="small"
                type="danger"
                link
                :loading="isStatusLoading(row.user_id)"
                v-if="row.status === 1"
                @click="() => handleStatusChange(row, 0)"
              >
                禁用
              </el-button>
              <el-button
                size="small"
                type="primary"
                link
                :loading="isStatusLoading(row.user_id)"
                v-else
                @click="() => handleStatusChange(row, 1)"
              >
                恢复
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="权限控制" min-width="360">
          <template #default="{ row }">
            <div class="permission-list">
              <div
                v-for="item in permissionList"
                :key="item.key"
                class="permission-item"
              >
                <span>{{ item.label }}</span>
                <el-switch
                  :model-value="row.permissions[item.key]"
                  :loading="isPermissionLoading(row.user_id, item.key)"
                  active-text="允许"
                  inactive-text="禁止"
                  inline-prompt
                  @change="(val) => handlePermissionToggle(row, item.key, val)"
                />
              </div>
            </div>
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
import { fetchAdminUsers, updateUserPermissions } from '@/api'

export default {
  name: 'AdminUserList',
  components: {
    Search
  },
  data() {
    return {
      loading: false,
      users: [],
      filters: {
        search: '',
        role: '',
        status: ''
      },
      pagination: {
        page: 1,
        pageSize: 20,
        total: 0
      },
      permissionLoading: {},
      statusLoading: {},
      roleOptions: [
        { label: '全部账户', value: '' },
        { label: '普通用户（读者 + 作者）', value: 'normal' },
        { label: '编辑', value: 3 }
      ],
      statusOptions: [
        { label: '全部状态', value: '' },
        { label: '正常', value: 1 },
        { label: '禁用', value: 0 }
      ],
      permissionList: [
        { key: 'can_publish', label: '发表作品' },
        { key: 'can_subscribe', label: '订阅内容' },
        { key: 'can_recharge', label: '充值点券' },
        { key: 'can_comment', label: '发表评论' },
        { key: 'can_vote', label: '参与投票' }
      ]
    }
  },
  created() {
    this.fetchUsers()
  },
  computed: {
    searchIcon() {
      return Search
    }
  },
  methods: {
    async fetchUsers() {
      this.loading = true
      try {
        const params = {
          search: this.filters.search || undefined,
          role: this.filters.role !== '' ? this.filters.role : undefined,
          status: this.filters.status !== '' ? this.filters.status : undefined,
          page: this.pagination.page,
          page_size: this.pagination.pageSize
        }
        const { data } = await fetchAdminUsers(params)
        if (data.success) {
          this.users = data.users || []
          this.pagination.total = data.total || 0
        } else {
          ElMessage.error(data.error || '获取用户列表失败')
        }
      } catch (error) {
        ElMessage.error(error?.message || '获取用户列表失败')
      } finally {
        this.loading = false
      }
    },
    handleFilter() {
      this.pagination.page = 1
      this.fetchUsers()
    },
    handleReset() {
      this.filters = {
        search: '',
        role: '',
        status: ''
      }
      this.pagination.page = 1
      this.fetchUsers()
    },
    handlePageChange(page) {
      this.pagination.page = page
      this.fetchUsers()
    },
    handleSizeChange(size) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      this.fetchUsers()
    },
    async handlePermissionToggle(user, key, value) {
      const mapKey = `${user.user_id}_${key}`
      const previousValue = Boolean(user.permissions[key])
      user.permissions[key] = value
      this.permissionLoading = { ...this.permissionLoading, [mapKey]: true }
      let reason = ''
      try {
        reason = await this.askReason('调整权限原因（可选）')
        if (reason === null) {
          user.permissions[key] = previousValue
          return
        }
        const payload = { [key]: value, reason }
        const { data } = await updateUserPermissions(user.user_id, payload)
        if (data.success) {
          ElMessage.success('权限已更新')
          user.permissions[key] = value
        } else {
          user.permissions[key] = previousValue
          ElMessage.error(data.error || '权限更新失败')
        }
      } catch (error) {
        user.permissions[key] = previousValue
        if (error !== null) {
          ElMessage.error(error?.message || '权限更新失败')
        }
      } finally {
        const { [mapKey]: _ignore, ...rest } = this.permissionLoading
        this.permissionLoading = rest
      }
    },
    async handleStatusChange(user, status) {
      const mapKey = `${user.user_id}_status`
      const previousStatus = user.status
      this.statusLoading = { ...this.statusLoading, [mapKey]: true }
      const actionText = status === 1 ? '恢复账号' : '禁用账号'
      try {
        const reason = await this.askReason(`${actionText}的原因（可选）`)
        if (reason === null) {
          return
        }
        const payload = { status, reason }
        const { data } = await updateUserPermissions(user.user_id, payload)
        if (data.success) {
          user.status = status
          ElMessage.success('账号状态已更新')
        } else {
          user.status = previousStatus
          ElMessage.error(data.error || '账号状态更新失败')
        }
      } catch (error) {
        if (error !== null) {
          ElMessage.error(error?.message || '账号状态更新失败')
        }
        user.status = previousStatus
      } finally {
        const { [mapKey]: _ignore, ...rest } = this.statusLoading
        this.statusLoading = rest
      }
    },
    isPermissionLoading(userId, key) {
      return !!this.permissionLoading[`${userId}_${key}`]
    },
    isStatusLoading(userId) {
      return !!this.statusLoading[`${userId}_status`]
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
  width: 180px;
}

.user-table {
  margin-top: 10px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-cell .name {
  font-weight: 600;
  color: #1f2d3d;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.permission-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px 14px;
}

.permission-item {
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
  .permission-list {
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

  .permission-list {
    grid-template-columns: 1fr;
  }
}
</style>


