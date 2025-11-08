<template>
  <div class="main-container">
    <!-- 顶部导航栏 -->
    <div class="top-bar">
      <div class="top-bar-left">
        <el-button 
          type="text" 
          @click="toggleSidebar"
          class="sidebar-toggle"
        >
          <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
        <h2 class="page-title">网络文学平台</h2>
      </div>
      <div class="top-bar-center">
        <el-button
          size="large"
          class="search-button"
          @click="goToSearch"
        >
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      <div class="top-bar-right">
        <el-avatar :size="40" :src="userAvatar" class="top-avatar">
          <el-icon><User /></el-icon>
        </el-avatar>
        <span class="username">{{ userDisplayName }}</span>
        <el-badge
          class="message-badge"
          :value="unreadCount"
          :hidden="unreadCount === 0"
        >
          <el-button
            class="top-action"
            type="text"
            @click="goToMessages"
          >
            <el-icon><Message /></el-icon>
            消息列表
          </el-button>
        </el-badge>
        <el-button
          class="top-action"
          type="text"
          @click="goToProfile"
        >
          <el-icon><User /></el-icon>
          个人中心
        </el-button>
      </div>
    </div>
    <div class="main-content-row">
      <!-- 侧边栏 -->
      <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-content">
          <el-menu
            :default-active="currentView"
            @select="handleMenuSelect"
            :collapse="sidebarCollapsed"
            class="sidebar-menu"
          >
            <el-menu-item index="bookshelf">
              <el-icon><Collection /></el-icon>
              <span v-if="!sidebarCollapsed">书架</span>
            </el-menu-item>
            <el-menu-item index="recommendations">
              <el-icon><Star /></el-icon>
              <span v-if="!sidebarCollapsed">为你推荐</span>
            </el-menu-item>
            <el-menu-item index="rankings">
              <el-icon><Trophy /></el-icon>
              <span v-if="!sidebarCollapsed">排行榜</span>
            </el-menu-item>
            <el-menu-item index="categories">
              <el-icon><Grid /></el-icon>
              <span v-if="!sidebarCollapsed">作品库</span>
            </el-menu-item>
            <el-menu-item index="author-mode">
              <el-icon><Edit /></el-icon>
              <span v-if="!sidebarCollapsed">作者模式</span>
            </el-menu-item>
          </el-menu>
          <div class="sidebar-bottom">
            <el-menu
              :default-active="currentView"
              @select="handleMenuSelect"
              :collapse="sidebarCollapsed"
              class="sidebar-menu"
            >
              <!-- <el-menu-item index="settings">
                <el-icon><Setting /></el-icon>
                <span v-if="!sidebarCollapsed">设置</span>
              </el-menu-item> -->
              <el-menu-item index="logout">
                <el-icon><SwitchButton /></el-icon>
                <span v-if="!sidebarCollapsed">退出</span>
              </el-menu-item>
            </el-menu>
          </div>
        </div>
      </div>
      <!-- 主页面内容 -->
      <div class="main-content-body">
        <div class="page-content">
          <router-view />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  Reading, Collection, Star, Trophy, Grid, Setting, SwitchButton,
  Fold, Expand, Search, Edit, User, Message
} from '@element-plus/icons-vue'
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'MainLayout',
  components: {
    Reading, Collection, Star, Trophy, Grid, Setting, SwitchButton,
    Fold, Expand, Search, Edit, User, Message
  },
  computed: {
    ...mapGetters(['sidebarCollapsed', 'user', 'userRole', 'unreadCount']),
    userAvatar() {
      const candidates = [
        this.user.avatar_url,
        this.user.author_avatar_url
      ]
      const url = candidates.find(item => typeof item === 'string' && item.trim())
      return url ? url.trim() : ''
    },
    userDisplayName() {
      const candidates = [
        this.user.nickname,
        this.user.pen_name,
        this.user.username
      ]
      const name = candidates.find(item => typeof item === 'string' && item.trim())
      return name ? name.trim() : '用户'
    }
  },
  created() {
    this.fetchUnreadCount()
  },
  methods: {
    ...mapActions(['toggleSidebar', 'logout', 'fetchUnreadCount']),
    
    handleMenuSelect(index) {
      if (index === 'logout') {
        this.handleLogout()
        return
      }
      
      this.$router.push(`/main/${index}`)
    },
    
    goToSearch() {
      this.$router.push('/main/search')
    },

    goToProfile() {
      this.$router.push('/main/profile')
    },

    goToMessages() {
      this.$router.push('/main/messages')
    },
    
    handleLogout() {
      this.$confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.logout()
        this.$router.push('/')
        this.$message.success('已退出登录')
      })
    },
    
    async loadUnreadCount() {
      await this.fetchUnreadCount()
    }
  }
}
</script>

<style scoped>
.main-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}
.top-bar {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  width: 100vw;
  height: 60px;
  background: linear-gradient(90deg, #4158d0 0%, #8341e3 100%);
  border-bottom: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 2000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.07);
}
.top-bar-left {
  display: flex;
  align-items: center;
  min-width: 200px;
  height: 60px;
}
.top-bar-center {
  flex: 1;
  max-width: 200px;
  margin: 0 20px;
  display: flex;
  justify-content: center;
}
.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.search-button {
  background: rgba(255, 255, 255, 0.22);
  border: none;
  color: #ffffff;
  border-radius: 24px;
  padding: 8px 22px;
  font-weight: 500;
  transition: background 0.3s ease, transform 0.2s ease;
}

.search-button:hover {
  background: rgba(255, 255, 255, 0.3);
  color: #ffffff;
  transform: translateY(-1px);
}

.search-button:active {
  transform: translateY(0);
  background: rgba(255, 255, 255, 0.26);
}

.search-button :deep(.el-icon) {
  margin-right: 6px;
}


.main-content-row {
  display: flex;
  flex: 1;
  margin-top: 60px;
  height: calc(100vh - 60px);
  overflow: hidden;
}
.sidebar {
  width: 250px;
  background: #fff;
  border-right: 1.5px solid #e2e8f0;
  transition: width 0.3s ease;
  overflow: hidden;
  box-shadow: 2px 0 8px -4px rgba(64,90,170,0.09);
}
.sidebar.collapsed { width: 60px; }
.sidebar-content { padding: 20px 0 0 0; display: flex; flex-direction: column; height: 100%; }
.sidebar-bottom { margin-top: auto; padding-bottom: 30px; }
.sidebar-menu { border: none; }
.sidebar-menu .el-menu-item { height: 50px; line-height: 50px; margin: 0 10px; border-radius: 8px; color: #5a6c7d; }
.sidebar-menu .el-menu-item:hover { background: #f0f2f5; color: #667eea; }
.sidebar-menu .el-menu-item.is-active { background: linear-gradient(135deg, #4158d0 0%, #8341e3 100%); color: white; }
.main-content-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #f6f9fc;
  box-shadow: -1.5px 0 10px 0 rgba(46,54,80,0.04);
  border-left: 1.5px solid #e2e8f0;
}
.page-content { flex: 1; padding: 20px; overflow-y: auto; }

.sidebar-toggle {
  margin-left: 3px;
  margin-right: 18px;
  font-size: 22px;
  color: #fff;
  height: 50px;
  width: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border-radius: 8px;
  background: transparent;
}
.sidebar-toggle :deep(.el-icon) {
  font-size: 22px;
  vertical-align: middle;
  color: inherit;
}
.sidebar-toggle:hover {
  color: #ffd900;
}
.sidebar-menu .el-menu-item .el-icon {
  font-size: 22px !important;
  vertical-align: middle;
}
.page-title {
  font-size: 1.3rem;
  color: #fff;
  font-weight: 600;
  margin: 0;
  letter-spacing: 1px;
}

.username {
  font-weight: 500;
  color: #ffffff;
}

.top-avatar {
  border: 2px solid rgba(255, 255, 255, 0.35);
}

.top-action {
  color: #ffffff;
  padding: 6px 14px;
  border-radius: 18px;
  background: transparent;
  border: none;
}

.top-action:hover {
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

.top-action:focus,
.top-action:active {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.22);
}

.top-action :deep(.el-icon) {
  margin-right: 6px;
}

.message-badge {
  margin-left: 0;
  display: inline-flex;
  align-items: center;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }
  
  .main-content {
    width: 100%;
  }
  
  .top-bar-center {
    display: none;
  }
  
  .top-bar-right {
    gap: 10px;
  }
  
  .username {
    display: none;
  }
}
</style>

