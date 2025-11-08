<template>
  <div class="profile-container">
    <div class="profile-header">
      <h2>个人中心</h2>
      <p>管理您的个人信息和账户设置</p>
    </div>
    
    <div class="profile-content">
      <div class="profile-sidebar">
        <div class="user-info-card">
          <div class="avatar-section">
            <el-avatar :size="80" :src="userInfo.avatar_url">
              <el-icon><User /></el-icon>
            </el-avatar>
            <h3>{{ userInfo.nickname || userInfo.username }}</h3>
            <p class="user-role">{{ getRoleText(userInfo.role) }}</p>
          </div>
          
          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-value">{{ pointsInfo.balance || userInfo.balance || 0 }}</span>
              <span class="stat-label">点券余额</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ pointsInfo.ticket_count || 0 }}</span>
              <span class="stat-label">月票数量</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ userStats.collections || 0 }}</span>
              <span class="stat-label">收藏作品</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ userStats.reading_time || 0 }}</span>
              <span class="stat-label">阅读时长(小时)</span>
            </div>
          </div>
        </div>
        
        <div class="action-buttons">
          <el-button 
            type="primary" 
            @click="showRechargeDialog = true"
            class="action-btn"
          >
            <el-icon><Money /></el-icon>
            充值点券
          </el-button>
          <el-button 
            @click="showEditDialog = true"
            class="action-btn"
          >
            <el-icon><Edit /></el-icon>
            编辑资料
          </el-button>
        </div>
      </div>
      
      <div class="profile-main">
        <el-tabs
          v-model="activeTab"
          class="profile-tabs"
          @tab-change="handleTabChange"
        >
          <el-tab-pane label="基本信息" name="basic">
            <div class="info-section">
              <h3>基本信息</h3>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="用户名">
                  {{ userInfo.username }}
                </el-descriptions-item>
                <el-descriptions-item label="昵称">
                  {{ userInfo.nickname || '未设置' }}
                </el-descriptions-item>
                <el-descriptions-item label="手机号">
                  {{ userInfo.phone || '未绑定' }}
                </el-descriptions-item>
                <el-descriptions-item label="邮箱">
                  {{ userInfo.email || '未绑定' }}
                </el-descriptions-item>
                <el-descriptions-item label="注册时间">
                  {{ formatTime(userInfo.create_time) }}
                </el-descriptions-item>
                <el-descriptions-item label="最后登录">
                  {{ formatTime(userInfo.last_login_time) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="阅读统计" name="reading">
            <div class="stats-section">
              <h3>阅读统计</h3>
              <div class="stats-grid">
                <div class="stat-card">
                  <div class="stat-icon">
                    <el-icon><Reading /></el-icon>
                  </div>
                  <div class="stat-content">
                    <span class="stat-value">{{ userStats.total_reading || 0 }}</span>
                    <span class="stat-label">总阅读作品数</span>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon">
                    <el-icon><Clock /></el-icon>
                  </div>
                  <div class="stat-content">
                    <span class="stat-value">{{ userStats.reading_time || 0 }}</span>
                    <span class="stat-label">总阅读时长(小时)</span>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon">
                    <el-icon><Collection /></el-icon>
                  </div>
                  <div class="stat-content">
                    <span class="stat-value">{{ userStats.collections || 0 }}</span>
                    <span class="stat-label">收藏作品数</span>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon">
                    <el-icon><Star /></el-icon>
                  </div>
                  <div class="stat-content">
                    <span class="stat-value">{{ userStats.votes || 0 }}</span>
                    <span class="stat-label">投票总数</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="资产记录" name="assets">
            <div class="assets-section">
              <h3>资产概览</h3>
              <div class="assets-summary">
                <div class="asset-card">
                  <div class="asset-title">点券余额</div>
                  <div class="asset-value">{{ pointsInfo.balance || 0 }}</div>
                </div>
                <div class="asset-card">
                  <div class="asset-title">月票数量</div>
                  <div class="asset-value">{{ pointsInfo.ticket_count || 0 }}</div>
                </div>
              </div>

              <div class="transactions-section">
                <h4>最近交易</h4>
                <el-table
                  ref="assetsTable"
                  v-if="pointTransactions.length > 0"
                  :data="pointTransactions"
                  border
                  stripe
                  class="transactions-table"
                >
                  <el-table-column prop="create_time" label="时间" width="180" />
                  <el-table-column prop="transaction_type" label="类型" width="140" />
                  <el-table-column prop="amount" label="金额" width="120">
                    <template #default="scope">
                      <span :class="{ 'amount-positive': scope.row.amount > 0, 'amount-negative': scope.row.amount < 0 }">
                        {{ scope.row.amount }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" />
                </el-table>
                <div v-else class="empty-transactions">暂无交易记录</div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="账户安全" name="security">
            <div class="security-section">
              <h3>账户安全</h3>
              <div class="security-items">
                <div class="security-item">
                  <div class="item-info">
                    <h4>修改密码</h4>
                    <p>定期修改密码有助于保护账户安全</p>
                  </div>
                  <el-button @click="showPasswordDialog = true">
                    修改密码
                  </el-button>
                </div>
                <div class="security-item">
                  <div class="item-info">
                    <h4>绑定手机</h4>
                    <p>{{ userInfo.phone ? '已绑定' : '未绑定' }} - {{ userInfo.phone || '点击绑定' }}</p>
                  </div>
                  <el-button @click="showPhoneDialog = true">
                    {{ userInfo.phone ? '更换' : '绑定' }}
                  </el-button>
                </div>
                <div class="security-item">
                  <div class="item-info">
                    <h4>绑定邮箱</h4>
                    <p>{{ userInfo.email ? '已绑定' : '未绑定' }} - {{ userInfo.email || '点击绑定' }}</p>
                  </div>
                  <el-button @click="showEmailDialog = true">
                    {{ userInfo.email ? '更换' : '绑定' }}
                  </el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
    
    <!-- 充值对话框 -->
    <el-dialog v-model="showRechargeDialog" title="充值点券" width="400px" @closed="resetRechargeForm">
      <el-form :model="rechargeForm" :rules="rechargeRules" ref="rechargeFormRef">
        <el-form-item label="充值金额" prop="amount">
          <el-input-number
            v-model="rechargeForm.amount"
            :min="10"
            :max="10000"
            :step="10"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="支付方式">
          <el-radio-group v-model="rechargeForm.payment_method">
            <el-radio label="alipay">支付宝</el-radio>
            <el-radio label="wechat">微信支付</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRechargeDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRecharge">确认充值</el-button>
      </template>
    </el-dialog>
    
    <!-- 编辑资料对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑资料" width="500px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef">
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="editForm.nickname" />
        </el-form-item>
        <el-form-item label="头像">
          <div class="avatar-upload-wrapper">
            <el-upload
              class="avatar-uploader"
              :show-file-list="false"
              accept="image/*"
              :http-request="handleAvatarUpload"
              :before-upload="beforeAvatarUpload"
              :disabled="avatarUploading"
            >
              <el-avatar
                v-if="editForm.avatar_url"
                :size="80"
                :src="editForm.avatar_url"
                class="avatar-preview"
              />
              <div v-else class="avatar-uploader-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传头像</span>
              </div>
            </el-upload>
            <div class="upload-hint">支持 JPG/PNG/GIF/WebP，大小不超过 2MB</div>
            <el-button
              v-if="editForm.avatar_url"
              type="text"
              class="remove-avatar-btn"
              @click="removeAvatar"
            >
              移除头像
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="个人简介" prop="intro">
          <el-input
            v-model="editForm.intro"
            type="textarea"
            :rows="4"
            placeholder="介绍一下自己..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="showPasswordDialog"
      title="修改密码"
      width="400px"
      @closed="resetPasswordForm"
    >
      <el-form
        :model="passwordForm"
        :rules="passwordRules"
        ref="passwordFormRef"
        label-position="top"
      >
        <el-form-item label="当前密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handlePassword">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 绑定手机号对话框 -->
    <el-dialog
      v-model="showPhoneDialog"
      :title="userInfo.phone ? '更换手机号' : '绑定手机号'"
      width="400px"
      @closed="resetPhoneForm"
    >
      <el-form
        :model="phoneForm"
        :rules="phoneRules"
        ref="phoneFormRef"
        label-position="top"
      >
        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="phoneForm.phone"
            maxlength="20"
            placeholder="请输入手机号"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPhoneDialog = false">取消</el-button>
        <el-button type="primary" @click="handlePhone">确认</el-button>
      </template>
    </el-dialog>

    <!-- 绑定邮箱对话框 -->
    <el-dialog
      v-model="showEmailDialog"
      :title="userInfo.email ? '更换邮箱' : '绑定邮箱'"
      width="400px"
      @closed="resetEmailForm"
    >
      <el-form
        :model="emailForm"
        :rules="emailRules"
        ref="emailFormRef"
        label-position="top"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="emailForm.email"
            placeholder="请输入邮箱"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEmailDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEmail">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { 
  User, Money, Edit, Reading, Clock, Collection, Star, Plus 
} from '@element-plus/icons-vue'
import { mapGetters } from 'vuex'
import { 
  getUserProfile,
  getUserStats,
  updateUserProfile,
  rechargeBalance,
  updateContactInfo,
  changeUserPassword,
  getUserPoints,
  uploadAvatarFile
} from '../api'

export default {
  name: 'Profile',
  components: {
    User,
    Money,
    Edit,
    Reading,
    Clock,
    Collection,
    Star,
    Plus
  },
  data() {
    const passwordForm = {
      old_password: '',
      new_password: '',
      confirm_password: ''
    }

    const phoneForm = {
      phone: ''
    }

    const emailForm = {
      email: ''
    }

    const validateConfirmPassword = (rule, value, callback) => {
      if (!value) {
        callback(new Error('请再次输入新密码'))
      } else if (value !== passwordForm.new_password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }

    const validatePhone = (rule, value, callback) => {
      if (!value) {
        callback(new Error('请输入手机号'))
      } else if (!/^\d{6,20}$/.test(value)) {
        callback(new Error('请输入有效的手机号'))
      } else {
        callback()
      }
    }

    const validateEmail = (rule, value, callback) => {
      if (!value) {
        callback(new Error('请输入邮箱'))
      } else if (!/^\S+@\S+\.\S+$/.test(value)) {
        callback(new Error('邮箱格式不正确'))
      } else {
        callback()
      }
    }

    return {
      activeTab: 'basic',
      userInfo: {},
      userStats: {},
      pointsInfo: {
        balance: 0,
        ticket_count: 0
      },
      pointTransactions: [],
      assetsLayoutRaf: null,
      showRechargeDialog: false,
      showEditDialog: false,
      showPasswordDialog: false,
      showPhoneDialog: false,
      showEmailDialog: false,
      avatarUploading: false,
      rechargeForm: {
        amount: 100,
        payment_method: 'alipay'
      },
      editForm: {
        nickname: '',
        avatar_url: '',
        intro: ''
      },
      passwordForm,
      phoneForm,
      emailForm,
      rechargeRules: {
        amount: [
          { required: true, message: '请输入充值金额', trigger: 'blur' },
          { type: 'number', min: 10, message: '充值金额不能少于10元', trigger: 'blur' }
        ]
      },
      editRules: {
        nickname: [
          { required: true, message: '请输入昵称', trigger: 'blur' }
        ]
      },
      passwordRules: {
        old_password: [
          { required: true, message: '请输入当前密码', trigger: 'blur' }
        ],
        new_password: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { min: 6, message: '新密码长度不能少于6位', trigger: 'blur' }
        ],
        confirm_password: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      },
      phoneRules: {
        phone: [
          { validator: validatePhone, trigger: 'blur' }
        ]
      },
      emailRules: {
        email: [
          { validator: validateEmail, trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    ...mapGetters(['user'])
  },
  created() {
    if (this.user && this.user.user_id) {
      this.loadUserInfo()
      this.loadUserStats()
      this.loadPointsInfo()
    }
  },
  methods: {
    async loadUserInfo() {
      try {
        const response = await getUserProfile()
        if (response.data.success) {
          const profile = response.data.profile || {}
          this.userInfo = profile
          this.editForm = {
            nickname: profile.nickname || '',
            avatar_url: profile.avatar_url || '',
            intro: profile.intro || ''
          }
          this.phoneForm.phone = profile.phone || ''
          this.emailForm.email = profile.email || ''
          this.syncStoreUser(profile)
        } else {
          this.$message.error(response.data.error || '获取用户信息失败')
        }
      } catch (error) {
        console.error('Load user info error:', error)
        this.$message.error('获取用户信息失败')
      }
    },
    
    async loadUserStats() {
      try {
        const response = await getUserStats()
        if (response.data.success) {
          const stats = response.data.stats || {}
          this.userStats = {
            total_reading: stats.total_reading || 0,
            reading_time: stats.reading_time || 0,
            collections: stats.collections || 0,
            votes: stats.votes || 0
          }
        } else {
          this.$message.error(response.data.error || '获取统计信息失败')
        }
      } catch (error) {
        console.error('Load user stats error:', error)
      }
    },
    
    async loadPointsInfo() {
      try {
        const response = await getUserPoints()
        if (response.data && response.data.success) {
          this.pointsInfo = {
            balance: response.data.balance || 0,
            ticket_count: response.data.ticket_count || 0
          }
          this.pointTransactions = response.data.transactions || []
          this.userInfo.balance = this.pointsInfo.balance
          this.$nextTick(() => {
            if (this.activeTab === 'assets') {
              this.layoutAssetsTable()
            }
          })
        }
      } catch (error) {
        console.error('Load user points error:', error)
      }
    },
    
    getRoleText(role) {
      const roles = {
        1: '读者',
        2: '作者',
        3: '编辑'
      }
      return roles[role] || '未知'
    },
    
    formatTime(timeString) {
      if (!timeString) return '未知'
      const time = new Date(timeString)
      return time.toLocaleString()
    },

    beforeAvatarUpload(file) {
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
      if (!allowedTypes.includes(file.type)) {
        this.$message.error('仅支持 JPG/PNG/GIF/WebP 格式的图片')
        return false
      }

      const isLt2M = file.size / 1024 / 1024 < 2
      if (!isLt2M) {
        this.$message.error('头像图片大小不能超过 2MB')
        return false
      }

      return true
    },

    async handleAvatarUpload(options) {
      const { file, onSuccess, onError } = options
      const successHandler = typeof onSuccess === 'function' ? onSuccess : () => {}
      const errorHandler = typeof onError === 'function' ? onError : () => {}

      this.avatarUploading = true
      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await uploadAvatarFile(formData)
        if (response.data && response.data.success) {
          this.editForm.avatar_url = response.data.url || response.data.relative_url || ''
          successHandler(response.data, file)
          this.$message.success('头像上传成功，请记得保存变更')
        } else {
          const errorMsg = (response.data && response.data.error) || '头像上传失败'
          this.$message.error(errorMsg)
          errorHandler(new Error(errorMsg))
        }
      } catch (error) {
        console.error('Upload avatar error:', error)
        this.$message.error('头像上传失败，请稍后重试')
        errorHandler(error)
      } finally {
        this.avatarUploading = false
      }
    },

    removeAvatar() {
      this.editForm.avatar_url = ''
    },
    
    async handleRecharge() {
      try {
        await this.$refs.rechargeFormRef.validate()
      } catch (error) {
        return
      }

      try {
        const response = await rechargeBalance({ amount: this.rechargeForm.amount })
        if (response.data.success) {
          await this.loadPointsInfo()
          this.$message.success(`充值成功！获得 ${this.rechargeForm.amount} 点券`)
          this.showRechargeDialog = false
          this.resetRechargeForm()
        } else {
          this.$message.error(response.data.error || '充值失败')
        }
      } catch (error) {
        console.error('Recharge error:', error)
        this.$message.error('充值失败，请稍后重试')
      }
    },
    
    resetRechargeForm() {
      if (this.$refs.rechargeFormRef) {
        this.$refs.rechargeFormRef.resetFields()
      }
      this.rechargeForm = {
        amount: 100,
        payment_method: 'alipay'
      }
    },

    async handleEdit() {
      try {
        await this.$refs.editFormRef.validate()
      } catch (error) {
        return
      }

      try {
        const response = await updateUserProfile({
          nickname: this.editForm.nickname,
          avatar_url: this.editForm.avatar_url,
          intro: this.editForm.intro
        })

        if (response.data.success) {
          this.userInfo = response.data.profile
          this.editForm = {
            nickname: this.userInfo.nickname || '',
            avatar_url: this.userInfo.avatar_url || '',
            intro: this.userInfo.intro || ''
          }
          this.phoneForm.phone = this.userInfo.phone || ''
          this.emailForm.email = this.userInfo.email || ''
          this.syncStoreUser(this.userInfo)
          this.$message.success('资料更新成功')
          this.showEditDialog = false
        } else {
          this.$message.error(response.data.error || '资料更新失败')
        }
      } catch (error) {
        console.error('Edit profile error:', error)
        this.$message.error('资料更新失败，请稍后重试')
      }
    },

    async handlePassword() {
      try {
        await this.$refs.passwordFormRef.validate()
      } catch (error) {
        return
      }

      try {
        const response = await changeUserPassword({
          old_password: this.passwordForm.old_password,
          new_password: this.passwordForm.new_password
        })

        if (response.data.success) {
          this.$message.success('密码修改成功')
          this.showPasswordDialog = false
          this.resetPasswordForm()
        } else {
          this.$message.error(response.data.error || '密码修改失败')
        }
      } catch (error) {
        console.error('Change password error:', error)
        this.$message.error('密码修改失败，请稍后重试')
      }
    },

    resetPasswordForm() {
      if (this.$refs.passwordFormRef) {
        this.$refs.passwordFormRef.resetFields()
      }
      this.passwordForm.old_password = ''
      this.passwordForm.new_password = ''
      this.passwordForm.confirm_password = ''
    },

    async handlePhone() {
      try {
        await this.$refs.phoneFormRef.validate()
      } catch (error) {
        return
      }

      try {
        const response = await updateContactInfo({ phone: this.phoneForm.phone })
        if (response.data.success) {
          this.userInfo = response.data.profile
          this.phoneForm.phone = this.userInfo.phone || ''
          this.emailForm.email = this.userInfo.email || ''
          this.syncStoreUser(this.userInfo)
          this.$message.success('手机号更新成功')
          this.showPhoneDialog = false
        } else {
          this.$message.error(response.data.error || '手机号更新失败')
        }
      } catch (error) {
        console.error('Update phone error:', error)
        this.$message.error('手机号更新失败，请稍后重试')
      }
    },

    resetPhoneForm() {
      if (this.$refs.phoneFormRef) {
        this.$refs.phoneFormRef.resetFields()
      }
      this.phoneForm.phone = this.userInfo.phone || ''
    },

    async handleEmail() {
      try {
        await this.$refs.emailFormRef.validate()
      } catch (error) {
        return
      }

      try {
        const response = await updateContactInfo({ email: this.emailForm.email })
        if (response.data.success) {
          this.userInfo = response.data.profile
          this.phoneForm.phone = this.userInfo.phone || ''
          this.emailForm.email = this.userInfo.email || ''
          this.syncStoreUser(this.userInfo)
          this.$message.success('邮箱更新成功')
          this.showEmailDialog = false
        } else {
          this.$message.error(response.data.error || '邮箱更新失败')
        }
      } catch (error) {
        console.error('Update email error:', error)
        this.$message.error('邮箱更新失败，请稍后重试')
      }
    },

    resetEmailForm() {
      if (this.$refs.emailFormRef) {
        this.$refs.emailFormRef.resetFields()
      }
      this.emailForm.email = this.userInfo.email || ''
    },

    syncStoreUser(profile) {
      if (!profile) return
      this.$store.commit('SET_USER', {
        ...this.$store.state.user,
        ...profile
      })
    },

    handleTabChange(activeName) {
      if (activeName === 'assets') {
        this.$nextTick(() => {
          this.layoutAssetsTable()
        })
      }
    },

    layoutAssetsTable() {
      const tableRef = this.$refs.assetsTable
      if (!tableRef || typeof tableRef.doLayout !== 'function') {
        return
      }

      if (this.assetsLayoutRaf) {
        cancelAnimationFrame(this.assetsLayoutRaf)
      }

      this.assetsLayoutRaf = requestAnimationFrame(() => {
        tableRef.doLayout()
        this.assetsLayoutRaf = null
      })
    }
  },
  beforeUnmount() {
    if (this.assetsLayoutRaf) {
      cancelAnimationFrame(this.assetsLayoutRaf)
      this.assetsLayoutRaf = null
    }
  }
}
</script>

<style scoped>
.profile-container {
  height: 100%;
}

.profile-header {
  text-align: center;
  margin-bottom: 30px;
}

.profile-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.profile-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.profile-content {
  display: flex;
  gap: 30px;
  align-items: flex-start;
}

.profile-sidebar {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.user-info-card {
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.avatar-section h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 15px 0 5px 0;
}

.user-role {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 0 0 20px 0;
}

.user-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.8rem;
  color: #7f8c8d;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.avatar-upload-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.avatar-uploader {
  display: inline-block;
}

.avatar-uploader :deep(.el-upload) {
  border: 1px dashed #dcdfe6;
  border-radius: 50%;
  cursor: pointer;
  overflow: hidden;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.3s ease;
  background-color: #f5f7fa;
}

.avatar-uploader :deep(.el-upload:hover) {
  border-color: #409eff;
}

.avatar-preview {
  border-radius: 50%;
}

.avatar-uploader-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 12px;
  gap: 4px;
}

.avatar-uploader-placeholder .el-icon {
  font-size: 20px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.remove-avatar-btn {
  align-self: flex-start;
  padding: 0;
  font-size: 12px;
}

.action-btn {
  width: 100%;
  border-radius: 8px;
  padding: 12px;
}

.profile-main {
  flex: 1;
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  min-width: 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

.profile-tabs {
  height: 100%;
}

.info-section,
.stats-section,
.security-section {
  padding: 20px 0;
}

.info-section h3,
.stats-section h3,
.security-section h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.stat-icon .el-icon {
  font-size: 1.5rem;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-content .stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-content .stat-label {
  font-size: 0.9rem;
  color: #7f8c8d;
}

.security-items {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.item-info h4 {
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 5px 0;
}

.item-info p {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin: 0;
}

@media (max-width: 768px) {
  .profile-content {
    flex-direction: column;
    gap: 20px;
  }
  
  .profile-sidebar {
    width: 100%;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
}

.assets-section {
  padding: 20px;
}

.assets-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.asset-card {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.25);
}

.asset-title {
  font-size: 0.95rem;
  opacity: 0.85;
  margin-bottom: 8px;
}

.asset-value {
  font-size: 1.8rem;
  font-weight: 600;
}

.transactions-section h4 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.transactions-table {
  width: 100%;
}

.amount-positive {
  color: #16a34a;
}

.amount-negative {
  color: #e11d48;
}

.empty-transactions {
  text-align: center;
  padding: 20px;
  color: #94a3b8;
}
</style>

