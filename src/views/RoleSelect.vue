<template>
  <div class="role-select-container">
    <div class="role-select-content">
      <div class="header">
        <el-button 
          type="text" 
          @click="goBack"
          class="back-button"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回欢迎页
        </el-button>
        <h1>加入我们</h1>
        <p>注册账号，开启您的阅读创作之旅</p>
      </div>
      
      <div class="role-options">
        <div 
          class="role-card admin-card"
          @click="goToAdminLogin"
          >
          <div class="role-icon">
            <el-icon><Management /></el-icon>
          </div>
          <h3>管理员</h3>
          <p>守护社区秩序，保障创作生态健康运行</p>
          <ul class="role-features">
            <li>用户行为权限管理</li>
            <li>作品审核与状态控制</li>
            <li>评论巡查与违规处理</li>
            <li>违规通知与消息推送</li>
            <li>专属后台仪表盘</li>
          </ul>
          <div class="action-button">
            <el-button type="primary" size="large">开始管理</el-button>
          </div>
        </div>
        
        <div 
          class="role-card"
          @click="goToLogin"
        >
          <div class="role-icon">
            <el-icon><Key /></el-icon>
          </div>
          <h3>普通用户</h3>
          <p>登录/注册您的账号，开始您的阅读之旅</p>
          <ul class="role-features">
            <li>海量作品阅读</li>
            <li>个性化推荐</li>
            <li>收藏订阅管理</li>
            <li>评论互动</li>
            <li>创作管理</li>
          </ul>
          <div class="action-button">
            <el-button type="success" size="large">登录/注册</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ArrowLeft, User, Key, Management } from '@element-plus/icons-vue'

export default {
  name: 'RoleSelect',
  components: {
    ArrowLeft,
    User,
    Key,
    Management
  },
  methods: {
    goBack() {
      this.$router.push('/')
    },
    
    goToRegister() {
      this.$router.push('/register')
    },
    
    goToLogin() {
      this.$router.push('/login')
    },

    goToAdminLogin() {
      this.$router.push('/admin/login')
    },

    goToAdminRegister() {
      this.$router.push('/admin/register')
    }
  }
}
</script>

<style scoped>
.role-select-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.role-select-content {
  background: white;
  border-radius: 20px;
  padding: 40px;
  max-width: 1000px;
  width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.header {
  text-align: center;
  margin-bottom: 40px;
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
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 700;
}

.header p {
  font-size: 1.1rem;
  color: #7f8c8d;
}

.role-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 30px;
}

.role-card {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.role-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border-color: #667eea;
  background: white;
}

.role-card.admin-card {
  cursor: pointer;
}

.role-card.admin-card .action-button {
  margin: 20px;
}

.role-card.admin-card .action-button .el-button + .el-button {
  margin-left: 0;
}

.role-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.role-icon .el-icon {
  font-size: 2.5rem;
  color: white;
}

.role-card h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 600;
}

.role-card p {
  color: #7f8c8d;
  margin-bottom: 20px;
  line-height: 1.6;
}

.role-features {
  list-style: none;
  text-align: center;
  padding-left: 0;
  margin-bottom: 20px;
}

.role-features li {
  padding: 8px 0;
  color: #5a6c7d;
  position: relative;
  padding-left: 30px;
}

.role-features li::before {
  content: '✓';
  position: absolute;
  left: 100px;
  color: #667eea;
  font-weight: bold;
}

.action-button {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .role-select-content {
    padding: 20px;
  }
  
  .role-options {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .header h1 {
    font-size: 2rem;
  }
}
</style>

