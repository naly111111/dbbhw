<template>
  <div class="welcome-container">
    <div class="welcome-content">
      <div class="platform-logo">
        <h1>网络文学平台</h1>
        <p class="platform-subtitle">连接作者与读者的桥梁</p>
      </div>
      
      <div class="platform-description">
        <h2>平台特色</h2>
        <div class="features">
          <div class="feature-item">
            <el-icon><Reading /></el-icon>
            <h3>海量作品</h3>
            <p>汇聚各类优质网络文学作品</p>
          </div>
          <div class="feature-item">
            <el-icon><Star /></el-icon>
            <h3>个性化推荐</h3>
            <p>基于阅读习惯的智能推荐</p>
          </div>
          <div class="feature-item">
            <el-icon><Trophy /></el-icon>
            <h3>实时榜单</h3>
            <p>多维度排行榜，发现热门作品</p>
          </div>
          <div class="feature-item">
            <el-icon><ChatDotRound /></el-icon>
            <h3>互动社区</h3>
            <p>读者作者互动，评论交流</p>
          </div>
          <div class="feature-item">
            <el-icon><Search /></el-icon>
            <h3>精准检索</h3>
            <p>多条件筛选，快速找到目标作品</p>
          </div>
          <div class="feature-item">
            <el-icon><Edit /></el-icon>
            <h3>优质读写体验</h3>
            <p>清爽阅读界面，便捷创作工具</p>
          </div>
        </div>
      </div>
      
      <div class="welcome-actions">
        <el-button 
          type="primary" 
          size="large" 
          @click="goToRoleSelect"
          class="start-button"
        >
          开始使用
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { Reading, Star, Trophy, ChatDotRound } from '@element-plus/icons-vue'

export default {
  name: 'Welcome',
  components: {
    Reading,
    Star,
    Trophy,
    ChatDotRound
  },
  methods: {
    goToRoleSelect() {
      this.$router.push('/role-select')
    }
  }
}
</script>

<style scoped>
.welcome-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.welcome-content {
  background: white;
  border-radius: 20px;
  padding: 60px;
  max-width: 800px;
  width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.platform-logo h1 {
  font-size: 3rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 700;
}

.platform-subtitle {
  font-size: 1.2rem;
  color: #7f8c8d;
  margin-bottom: 40px;
}

.platform-description h2 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 30px;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 30px;
  margin-bottom: 40px;
}

.feature-item {
  padding: 20px;
  border-radius: 10px;
  background: #f8f9fa;
  transition: transform 0.3s ease;
}

.feature-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.feature-item .el-icon {
  font-size: 2.5rem;
  color: #667eea;
  margin-bottom: 15px;
}

.feature-item h3 {
  font-size: 1.3rem;
  color: #2c3e50;
  margin-bottom: 10px;
}

.feature-item p {
  color: #7f8c8d;
  line-height: 1.6;
}

.start-button {
  padding: 15px 40px;
  font-size: 1.2rem;
  border-radius: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.start-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

@media (max-width: 768px) {
  .welcome-content {
    padding: 40px 20px;
  }
  
  .platform-logo h1 {
    font-size: 2rem;
  }
  
  .features {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>

