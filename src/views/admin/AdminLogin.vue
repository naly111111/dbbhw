<template>
  <div class="auth-container">
    <div class="auth-content">
      <div class="auth-header">
        <el-button
          type="text"
          @click="goToRoleSelect"
          class="back-button"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回角色选择
        </el-button>
        <h1>管理员通道</h1>
        <p>登录或申请管理员账号进入后台控制台</p>
      </div>

      <el-tabs v-model="activeTab" class="auth-tabs">
        <el-tab-pane name="login">
          <template #label>
            <div class="tab-label">
              <el-icon><User /></el-icon>
              <span>登录</span>
            </div>
          </template>
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="auth-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入管理员用户名"
                size="large"
                :prefix-icon="User"
                autocomplete="username"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                autocomplete="current-password"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loginLoading"
                class="submit-button"
                @click="handleLogin"
              >
                登录
              </el-button>
            </el-form-item>
            <!-- <div class="auth-links">
              <span>还没有管理员账号？</span>
              <el-button type="primary" link @click="switchTab('register')">
                申请管理员
              </el-button>
            </div> -->
          </el-form>
        </el-tab-pane>

        <el-tab-pane name="register">
          <template #label>
            <div class="tab-label">
              <el-icon><Edit /></el-icon>
              <span>注册</span>
            </div>
          </template>
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-width="100px"
            class="auth-form"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入管理员用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item label="显示名称" prop="display_name">
              <el-input
                v-model="registerForm.display_name"
                placeholder="后台显示名称，可选"
                size="large"
                :prefix-icon="Edit"
              />
            </el-form-item>
            <el-form-item label="联系电话" prop="phone">
              <el-input
                v-model="registerForm.phone"
                placeholder="可选，便于紧急联系"
                size="large"
                :prefix-icon="Phone"
              />
            </el-form-item>
            <el-form-item label="联系邮箱" prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="可选，用于通知"
                size="large"
                :prefix-icon="Message"
              />
            </el-form-item>
            <el-form-item label="管理员密钥" prop="secret_key">
              <el-input
                v-model="registerForm.secret_key"
                placeholder="请输入管理员注册密钥"
                size="large"
                :prefix-icon="Key"
                show-password
              />
            </el-form-item>
            <el-form-item label="登录密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="至少6位"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="registerLoading"
                class="submit-button"
                @click="handleRegister"
              >
                注册
              </el-button>
            </el-form-item>
            <!-- <div class="auth-links">
              <span>已经拥有管理员账号？</span>
              <el-button type="primary" link @click="switchTab('login')">
                返回登录
              </el-button>
            </div> -->
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  User,
  Lock,
  Phone,
  Message,
  Key,
  Edit
} from '@element-plus/icons-vue'
import { adminRegister as adminRegisterApi } from '@/api'

const TAB_NAMES = ['login', 'register']

export default {
  name: 'AdminLogin',
  components: {
    ArrowLeft,
    User,
    Lock,
    Phone,
    Message,
    Key,
    Edit
  },
  props: {
    defaultTab: {
      type: String,
      default: 'login'
    }
  },
  data() {
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.registerForm.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }

    return {
      activeTab: TAB_NAMES.includes(this.defaultTab) ? this.defaultTab : 'login',
      loginLoading: false,
      registerLoading: false,
      loginForm: {
        username: '',
        password: ''
      },
      registerForm: {
        username: '',
        display_name: '',
        phone: '',
        email: '',
        secret_key: '',
        password: '',
        confirmPassword: ''
      },
      loginRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
        ]
      },
      registerRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, message: '用户名长度不能少于3位', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少6位', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ],
        secret_key: [
          { required: true, message: '请输入管理员密钥', trigger: 'blur' }
        ],
        email: [
          { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
        ]
      }
    }
  },
  watch: {
    defaultTab(newVal) {
      if (TAB_NAMES.includes(newVal)) {
        this.activeTab = newVal
      }
    },
    activeTab(newTab, oldTab) {
      if (newTab === oldTab || !TAB_NAMES.includes(newTab)) {
        return
      }
      this.updateRouteForTab(newTab)
    },
    $route(to) {
      this.syncTabWithRoute(to)
    }
  },
  created() {
    this.syncTabWithRoute(this.$route)
  },
  methods: {
    syncTabWithRoute(route) {
      if (!route) {
        return
      }
      const { path } = route

      if (path.includes('/admin/register')) {
        this.activeTab = 'register'
        return
      }
      if (path.includes('/admin/login')) {
        this.activeTab = 'login'
        return
      }
    },
    updateRouteForTab(tab) {
      const targetPath = tab === 'register' ? '/admin/register' : '/admin/login'
      if (this.$route.path !== targetPath) {
        this.$router.push(targetPath)
      }
    },
    switchTab(tab) {
      if (!TAB_NAMES.includes(tab)) {
        return
      }
      this.activeTab = tab
    },
    goToRoleSelect() {
      this.$router.push('/role-select')
    },
    async handleLogin() {
      try {
        await this.$refs.loginFormRef.validate()
      } catch (error) {
        return
      }

      if (this.loginLoading) {
        return
      }

      this.loginLoading = true
      try {
        const { success, error } = await this.$store.dispatch('adminLogin', {
          ...this.loginForm
        })
        if (success) {
          ElMessage.success('登录成功，正在跳转后台')
          this.$router.push('/admin')
        } else {
          ElMessage.error(error || '登录失败')
        }
      } catch (err) {
        ElMessage.error(err?.message || '登录失败')
      } finally {
        this.loginLoading = false
      }
    },
    async handleRegister() {
      try {
        await this.$refs.registerFormRef.validate()
      } catch (error) {
        return
      }

      if (this.registerLoading) {
        return
      }

      this.registerLoading = true
      try {
        const payload = {
          username: this.registerForm.username,
          password: this.registerForm.password,
          display_name: this.registerForm.display_name,
          phone: this.registerForm.phone,
          email: this.registerForm.email,
          secret_key: this.registerForm.secret_key
        }
        const { data } = await adminRegisterApi(payload)
        if (data.success) {
          ElMessage.success('管理员注册成功，请登录')
          this.loginForm.username = this.registerForm.username
          this.switchTab('login')
        } else {
          ElMessage.error(data.error || '注册失败')
        }
      } catch (err) {
        ElMessage.error(err?.message || '注册失败')
      } finally {
        this.registerLoading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.auth-content {
  background: #ffffff;
  border-radius: 20px;
  padding: 40px;
  max-width: 560px;
  width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
}

.auth-header {
  text-align: center;
  margin-bottom: 10px;
  position: relative;
}

.back-button {
  position: absolute;
  left: 0;
  top: 0;
  color: #7f8c8d;
  font-size: 1rem;
}

.back-button:hover {
  color: #667eea;
}

.auth-header h1 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 700;
}

.auth-header p {
  color: #7f8c8d;
}

.auth-tabs {
  margin-top: 24px;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 1.05rem;
}

.auth-form {
  margin-top: 20px;
}

.submit-button {
  width: 100%;
  padding: 15px;
  font-size: 1.1rem;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.28);
}

.auth-links {
  margin-top: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  color: #7f8c8d;
}

::deep(.el-form-item) {
  margin-bottom: 20px;
}

::deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 12px 15px;
}

::deep(.el-tabs__item) {
  font-size: 1.05rem;
  font-weight: 600;
  flex: 1;
  display: inline-flex;
  justify-content: center;
  align-items: center;
}

::deep(.el-tabs__nav-wrap) {
  flex: 1;
}

::deep(.el-tabs__active-bar) {
  height: 4px;
  border-radius: 4px;
}

::deep(.el-tabs__nav) {
  display: flex;
  justify-content: space-between;
  width: 100%;
}

::deep(.el-tabs__nav-scroll) {
  width: 100%;
}

@media (max-width: 768px) {
  .auth-content {
    padding: 30px 22px;
  }

  .auth-header h1 {
    font-size: 1.6rem;
  }

  .auth-tabs {
    margin-top: 16px;
  }
}
</style>
