<template>
  <div class="register-container">
    <div class="register-content">
      <div class="header">
        <el-button 
          type="text" 
          @click="goBack"
          class="back-button"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1>注册账号</h1>
        <p>创建您的账号，开始阅读之旅</p>
      </div>
      
      <el-form
        ref="registerForm"
        :model="form"
        :rules="rules"
        label-width="80px"
        class="register-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            prefix-icon="Phone"
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            @click="handleRegister"
            :loading="loading"
            class="register-button"
          >
            注册
          </el-button>
          <el-button @click="goToLogin" class="login-button">
            已有账号？立即登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ArrowLeft } from '@element-plus/icons-vue'
import { register } from '@/api'

export default {
  name: 'Register',
  components: {
    ArrowLeft
  },
  data() {
    return {
      loading: false,
      form: {
        username: '',
        password: '',
        confirmPassword: '',
        phone: '',
        email: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          { validator: this.validateConfirmPassword, trigger: 'blur' }
        ],
        phone: [
          { required: true, message: '请输入手机号', trigger: 'blur' },
          { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }
        ]
      }
    }
  },
  methods: {
    goBack() {
      this.$router.push('/role-select')
    },
    
    goToLogin() {
      this.$router.push('/login')
    },
    
    validateConfirmPassword(rule, value, callback) {
      if (value !== this.form.password) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    },
    
    async handleRegister() {
      try {
        await this.$refs.registerForm.validate()
        this.loading = true
        
        const response = await register({
          username: this.form.username,
          password: this.form.password,
          phone: this.form.phone,
          email: this.form.email,
          role: 1 // 默认为普通用户
        })
        
        if (response.success) {
          this.$message.success('注册成功！')
          this.$router.push('/login')
        } else {
          this.$message.error(response.message || '注册失败')
        }
      } catch (error) {
        console.error('注册错误:', error)
        this.$message.error('注册失败，请检查网络连接')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.register-content {
  background: white;
  border-radius: 20px;
  padding: 40px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.header {
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

.header h1 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 700;
}

.header p {
  font-size: 1rem;
  color: #7f8c8d;
}

.register-form {
  margin-top: 20px;
}

.register-button {
  width: 100%;
  height: 45px;
  font-size: 1.1rem;
  margin-bottom: 15px;
}

.login-button {
  width: 100%;
  height: 45px;
  font-size: 1rem;
}

@media (max-width: 768px) {
  .register-content {
    padding: 20px;
  }
  
  .header h1 {
    font-size: 1.5rem;
  }
}
</style>
