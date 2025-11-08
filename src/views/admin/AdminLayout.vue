<template>
  <el-container class="admin-layout">
    <el-aside width="220px" class="admin-aside">
      <div class="logo-area" @click="goDashboard">
        <span class="logo-mark">后台</span>
        <span class="logo-text">创作平台管理</span>
      </div>
      <el-menu
        class="side-menu"
        :default-active="activeMenu"
        background-color="transparent"
        text-color="#d7dcf0"
        active-text-color="#ffffff"
        router
      >
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/works">
          <el-icon><Collection /></el-icon>
          <span>作品管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/comments">
          <el-icon><ChatDotRound /></el-icon>
          <span>评论巡查</span>
        </el-menu-item>
        <el-menu-item index="/admin/logs">
          <el-icon><Document /></el-icon>
          <span>行为日志</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="admin-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item to="/admin/users">管理员首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ breadcrumbTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tag type="danger" effect="dark">管理员</el-tag>
          <span class="username">{{ user.username }}</span>
          <el-button type="info" link @click="goRoleSelect">角色选择</el-button>
          <el-divider direction="vertical" />
          <el-button type="primary" plain size="small" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <el-scrollbar class="content-scroll">
          <router-view />
        </el-scrollbar>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import { ElMessage } from 'element-plus'
import { User, Collection, ChatDotRound, Document } from '@element-plus/icons-vue'

export default {
  name: 'AdminLayout',
  components: {
    User,
    Collection,
    ChatDotRound,
    Document
  },
  computed: {
    user() {
      return this.$store.getters.user || {}
    },
    activeMenu() {
      const segments = this.$route.path.split('/')
      if (segments.length < 3) {
        return '/admin/users'
      }
      return `/admin/${segments[2]}`
    },
    breadcrumbTitle() {
      if (this.activeMenu === '/admin/works') {
        return '作品管理'
      }
      if (this.activeMenu === '/admin/comments') {
        return '评论巡查'
      }
      if (this.activeMenu === '/admin/logs') {
        return '行为日志'
      }
      return '用户管理'
    }
  },
  methods: {
    async handleLogout() {
      this.$store.dispatch('logout')
      ElMessage.success('已退出后台')
      this.$router.push('/admin/login')
    },
    goDashboard() {
      if (this.$route.path !== '/admin/users') {
        this.$router.push('/admin/users')
      }
    },
    goRoleSelect() {
      this.$router.push('/role-select')
    }
  }
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  background: #f4f6fb;
}

.admin-aside {
  background: #1a2233;
  color: #d7dcf0;
  display: flex;
  flex-direction: column;
  padding: 0 0 12px;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 22px 20px 18px;
  color: #ffffff;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
}

.logo-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(140deg, #409eff, #36d1dc);
  color: #fff;
  font-weight: 700;
  letter-spacing: 2px;
}

.logo-text {
  white-space: nowrap;
}

.side-menu {
  border-right: none;
  flex: 1;
  padding-top: 12px;
  background: transparent;
}

.side-menu :deep(.el-menu-item) {
  border-radius: 8px;
  margin: 6px 12px;
  height: 44px;
  line-height: 44px;
}

.side-menu :deep(.is-active) {
  background: rgba(64, 158, 255, 0.3) !important;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #ffffff;
  box-shadow: 0 1px 6px rgba(31, 35, 53, 0.08);
}

.header-left {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #3c4a63;
}

.username {
  font-weight: 600;
}

.admin-main {
  background: #f4f6fb;
  padding: 0;
}

.content-scroll {
  height: 100%;
  padding: 20px 24px 28px;
}

@media (max-width: 960px) {
  .admin-aside {
    width: 72px !important;
  }

  .logo-text {
    display: none;
  }

  .logo-area {
    justify-content: center;
  }

  .side-menu :deep(.el-menu-item span) {
    display: none;
  }
}

@media (max-width: 768px) {
  .admin-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
  }

  .header-right {
    flex-wrap: wrap;
    gap: 6px;
  }
}
</style>



