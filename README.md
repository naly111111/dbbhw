# 网络文学平台

一个基于Vue3 + Django的网络文学阅读平台，支持用户注册、作品管理、阅读记录、评论互动等功能。

## 技术栈

### 前端
- Vue 3.3.4
- Vue Router 4.2.4
- Vuex 4.1.0
- Element Plus 2.3.12
- Axios 1.5.0

### 后端
- Django 4.2.7
- Django REST Framework 3.14.0
- PyMySQL 1.1.0
- PyJWT 2.8.0

### 数据库
- MySQL 8.0+

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd dbbhw
   ```

2. **配置数据库**
   - 启动MySQL服务
   - 创建数据库：`CREATE DATABASE novel_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
   - 导入表结构：`mysql -u root -p113442 novel_platform < init_database.sql`

3. **启动应用**

   **方法一：一键启动（推荐）**
   ```bash
   # 双击运行
   start_all.bat
   ```

   **方法二：分别启动**
   ```bash
   # 启动后端
   start_backend.bat
   
   # 启动前端（新开命令行窗口）
   start_frontend.bat
   ```

4. **测试连接**
   ```bash
   # 测试服务器连接
   test_connection.bat
   ```

5. **访问应用**
   - 前端：http://localhost:8080
   - 后端API：http://localhost:8000

## 项目结构

```
dbbhw/
├── backend/                 # Django后端配置
│   ├── settings.py         # 项目设置
│   ├── urls.py            # 根URL配置
│   └── wsgi.py            # WSGI配置
├── novel_platform/         # 主应用
│   ├── models.py          # 数据模型
│   ├── views.py           # API视图
│   ├── urls.py            # 应用URL配置
│   └── authentication.py  # 认证模块
├── src/                   # Vue前端源码
│   ├── views/             # 页面组件
│   ├── router/            # 路由配置
│   ├── store/             # 状态管理
│   └── api/               # API接口
├── init_database.sql      # 数据库初始化脚本
├── requirements.txt       # Python依赖
├── package.json          # Node.js依赖
├── start_backend.bat     # 后端启动脚本
├── start_frontend.bat    # 前端启动脚本
├── start_all.bat         # 一键启动脚本
└── test_connection.bat   # 连接测试脚本
```

## 功能特性

### 用户系统
- 用户注册/登录
- 角色管理（读者/作者/编辑）
- JWT身份认证

### 作品管理
- 作品创建/编辑
- 章节管理
- 分类标签
- 状态管理

### 阅读功能
- 在线阅读
- 阅读记录
- 收藏订阅
- 评论互动

### 推荐系统
- 个性化推荐
- 排行榜
- 搜索功能

## 启动脚本说明

### start_all.bat
一键启动前后端服务器，自动处理启动顺序。

### start_backend.bat
仅启动Django后端服务器。

### start_frontend.bat
仅启动Vue前端开发服务器。

### test_connection.bat
测试服务器连接状态和API可用性。

## 常见问题

### 1. 数据库连接失败
- 检查MySQL服务是否运行
- 确认数据库配置正确
- 验证用户名密码

### 2. 前端启动失败
- 检查Node.js版本（需要16+）
- 删除node_modules重新安装
- 检查端口8080是否被占用

### 3. 后端启动失败
- 检查Python版本（需要3.8+）
- 激活虚拟环境
- 安装所有依赖

### 4. 注册用户失败
- 确认数据库表已创建
- 检查API接口是否正常
- 查看后端日志

## 开发说明

### 数据库操作
项目使用原生SQL进行数据库操作，不使用Django ORM。所有数据库操作都在 `novel_platform/views.py` 中通过 `connection.cursor()` 执行。

### API接口
- 用户注册：`POST /api/auth/register/`
- 用户登录：`POST /api/auth/login/`
- 测试认证：`GET /api/test-auth/`

### 前端路由
- 欢迎页：`/`
- 角色选择：`/role-select`
- 登录页：`/login`
- 主界面：`/main`

## 许可证

MIT License