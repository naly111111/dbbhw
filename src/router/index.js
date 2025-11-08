import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'

const ADMIN_ROLE = 9

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: () => import('../views/Welcome.vue')
  },
  {
    path: '/role-select',
    name: 'RoleSelect',
    component: () => import('../views/RoleSelect.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/admin/AdminLogin.vue')
  },
  {
    path: '/admin/register',
    name: 'AdminRegister',
    component: () => import('../views/admin/AdminRegister.vue')
  },
  {
    path: '/main',
    name: 'Main',
    component: () => import('../views/Main.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'MainDefault',
        redirect: 'bookshelf'
      },
      {
        path: 'bookshelf',
        name: 'Bookshelf',
        component: () => import('../views/Bookshelf.vue')
      },
      {
        path: 'rankings',
        name: 'Rankings',
        component: () => import('../views/Rankings.vue')
      },
      {
        path: 'recommendations',
        name: 'Recommendations',
        component: () => import('../views/Recommendations.vue')
      },
      {
        path: 'search',
        name: 'Search',
        component: () => import('../views/Search.vue')
      },
      {
        path: 'categories',
        name: 'Categories',
        component: () => import('../views/Categories.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue')
      },
      {
        path: 'author-mode',
        name: 'AuthorMode',
        component: () => import('../views/AuthorMode.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue')
      },
      {
        path: 'messages',
        name: 'Messages',
        component: () => import('../views/Messages.vue')
      },
      {
        path: 'work-edit/:workId',
        name: 'WorkEdit',
        component: () => import('../views/WorkEdit.vue')
      },
      {
        path: 'chapter-manage/:workId',
        name: 'ChapterManage',
        component: () => import('../views/ChapterManage.vue')
      },
      {
        path: 'comment-manage/:workId',
        name: 'CommentManage',
        component: () => import('../views/CommentManage.vue')
      },
      {
        path: 'reading/:workId/:chapterId?',
        name: 'Reading',
        component: () => import('../views/Reading.vue')
      },
      {
        path: 'work-detail/:workId',
        name: 'WorkDetail',
        component: () => import('../views/WorkDetail.vue')
      }
    ]
  },
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: '/admin/users'
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../views/admin/AdminUserList.vue')
      },
      {
        path: 'works',
        name: 'AdminWorks',
        component: () => import('../views/admin/AdminWorkList.vue')
      },
      {
        path: 'comments',
        name: 'AdminComments',
        component: () => import('../views/admin/AdminCommentList.vue')
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('../views/admin/AdminActionLogs.vue')
      }
    ]
  },
  {
    path: '/reading/:workId/:chapterId?',
    name: 'ReadingLegacy',
    redirect: (to) => `/main/reading/${to.params.workId}${to.params.chapterId ? '/' + to.params.chapterId : ''}`
  },
  {
    path: '/work-detail/:workId',
    name: 'WorkDetailLegacy',
    redirect: (to) => `/main/work-detail/${to.params.workId}`
  },
  {
    path: '/bookshelf',
    redirect: '/main/bookshelf'
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = store.getters.token
  const userRole = store.getters.userRole
  const isAdmin = userRole === ADMIN_ROLE

  if (to.meta.requiresAdmin) {
    if (!token) {
      return next('/admin/login')
    }
    if (!isAdmin) {
      return next(token ? '/main' : '/admin/login')
    }
    return next()
  }

  if ((to.name === 'AdminLogin' || to.name === 'AdminRegister') && token && isAdmin) {
    return next('/admin')
  }
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.requiresAuthor && userRole !== 2) {
    next('/main')
  } else {
    next()
  }
})

export default router

