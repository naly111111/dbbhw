<template>
  <div class="login-container">
    <div class="login-content">
      <div class="login-header">
        <el-button 
          type="text" 
          @click="goBack"
          class="back-button"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回角色选择
        </el-button>
        <h1>管理员登录</h1>
        <p>请输入您的账号信息</p>
      </div>
      
      <div class="login-form">
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form 
              :model="loginForm" 
              :rules="loginRules" 
              ref="loginFormRef"
              @submit.prevent="handleLogin"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入管理员用户名"
                  size="large"
                  prefix-icon="User"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  prefix-icon="Lock"
                  show-password
                />
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="primary" 
                  size="large" 
                  @click="handleLogin"
                  :loading="loginLoading"
                  class="login-button"
                >
                  登录
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
          <el-tab-pane label="注册" name="register">
            <el-form 
              :model="registerForm" 
              :rules="registerRules" 
              ref="registerFormRef"
              @submit.prevent="handleRegister"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="请输入用户名"
                  size="large"
                  prefix-icon="User"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  prefix-icon="Lock"
                  show-password
                />
              </el-form-item>
              
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="请确认密码"
                  size="large"
                  prefix-icon="Lock"
                  show-password
                />
              </el-form-item>
              
              <el-form-item prop="phone">
                <el-input
                  v-model="registerForm.phone"
                  placeholder="请输入手机号（可选）"
                  size="large"
                  prefix-icon="Phone"
                />
              </el-form-item>
              
              <el-form-item prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="请输入邮箱（可选）"
                  size="large"
                  prefix-icon="Message"
                />
              </el-form-item>
              
              <el-form-item prop="nickname">
                <el-input
                  v-model="registerForm.nickname"
                  placeholder="请输入昵称"
                  size="large"
                  prefix-icon="User"
                />
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="primary" 
                  size="large" 
                  @click="handleRegister"
                  :loading="registerLoading"
                  class="register-button"
                >
                  注册
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script>
import { ArrowLeft, User, Lock, Phone, Message, Edit } from '@element-plus/icons-vue'
import { mapActions } from 'vuex'

export default {
  name: 'Login',
  components: {
    ArrowLeft,
    User,
    Lock,
    Phone,
    Message,
    Edit
  },
  data() {
    return {
      activeTab: 'login',
      loginLoading: false,
      registerLoading: false,
      loginForm: {
        username: '',
        password: ''
      },
      registerForm: {
        username: '',
        password: '',
        confirmPassword: '',
        phone: '',
        email: '',
        nickname: ''
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
          { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请确认密码', trigger: 'blur' },
          { validator: this.validateConfirmPassword, trigger: 'blur' }
        ],
        nickname: [
          { required: true, message: '请输入昵称', trigger: 'blur' }
        ]
      }
    }
  },
  created() {
    // 移除角色相关逻辑
  },
  methods: {
    ...mapActions(['login', 'register']),
    
    goBack() {
      this.$router.push('/role-select')
    },
    
    
    validateConfirmPassword(rule, value, callback) {
      if (value !== this.registerForm.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    },
    
    async handleLogin() {
      try {
        await this.$refs.loginFormRef.validate()
        this.loginLoading = true
        
        const result = await this.login({
          ...this.loginForm,
          role: 1 // 默认为普通用户
        })
        
        if (result.success) {
          this.$message.success('登录成功')
          this.$router.push('/main')
        } else {
          this.$message.error(result.error)
        }
      } catch (error) {
        console.error('Login error:', error)
      } finally {
        this.loginLoading = false
      }
    },
    
    async handleRegister() {
      try {
        await this.$refs.registerFormRef.validate()
        this.registerLoading = true
        
        const registerData = {
          username: this.registerForm.username,
          password: this.registerForm.password,
          role: 1, // 默认为普通用户
          phone: this.registerForm.phone,
          email: this.registerForm.email,
          nickname: this.registerForm.nickname
        }
        
        const result = await this.register(registerData)
        
        if (result.success) {
          this.$message.success('注册成功，请登录')
          this.activeTab = 'login'
          this.loginForm.username = this.registerForm.username
        } else {
          this.$message.error(result.error)
        }
      } catch (error) {
        console.error('Register error:', error)
      } finally {
        this.registerLoading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-content {
  background: white;
  border-radius: 20px;
  padding: 40px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
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

.login-header h1 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 700;
}

.login-header p {
  color: #7f8c8d;
}

.login-tabs {
  margin-top: 20px;
}

.login-button,
.register-button {
  width: 100%;
  padding: 15px;
  font-size: 1.1rem;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.login-button:hover,
.register-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 12px 15px;
}

:deep(.el-tabs__item) {
  font-size: 1.1rem;
  font-weight: 600;
}

@media (max-width: 768px) {
  .login-content {
    padding: 30px 20px;
  }
  
  .login-header h1 {
    font-size: 1.5rem;
  }
}
</style>

