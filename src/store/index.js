import { createStore } from 'vuex'
import api, {
  adminLogin as adminLoginApi
} from '../api'

const ADMIN_ROLE = 9

export default createStore({
  state: {
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || '{}'),
    sidebarCollapsed: false,
    unreadCount: 0
  },
  
  getters: {
    token: state => state.token,
    user: state => state.user,
    userRole: state => state.user.role,
    isLoggedIn: state => !!state.token,
    sidebarCollapsed: state => state.sidebarCollapsed,
    isAdmin: state => state.user.role === ADMIN_ROLE,
    unreadCount: state => state.unreadCount
  },
  
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token
      localStorage.setItem('token', token)
    },
    
    SET_USER(state, user) {
      state.user = { ...state.user, ...user }
      localStorage.setItem('user', JSON.stringify(state.user))
    },
    
    CLEAR_AUTH(state) {
      state.token = ''
      state.user = {}
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      state.unreadCount = 0
    },
    
    TOGGLE_SIDEBAR(state) {
      state.sidebarCollapsed = !state.sidebarCollapsed
    },

    SET_UNREAD_COUNT(state, count) {
      const numeric = Number(count)
      state.unreadCount = Number.isFinite(numeric) && numeric > 0 ? Math.floor(numeric) : 0
    }
  },
  
  actions: {
    async login({ commit, dispatch }, credentials) {
      try {
        const response = await api.post('/auth/login/', credentials)
        if (response.data.success) {
          commit('SET_TOKEN', response.data.token)
          commit('SET_USER', {
            user_id: response.data.user_id,
            username: response.data.username,
            role: response.data.role
          })
          await dispatch('refreshUserProfile')
          return { success: true }
        } else {
          return { success: false, error: response.data.error }
        }
      } catch (error) {
        return { success: false, error: '登录失败，请检查网络连接' }
      }
    },

    async adminLogin({ commit, dispatch }, credentials) {
      try {
        const response = await adminLoginApi(credentials)
        if (response.data.success) {
          commit('SET_TOKEN', response.data.token)
          commit('SET_USER', {
            user_id: response.data.user_id,
            username: response.data.username,
            role: response.data.role
          })
          await dispatch('refreshUserProfile')
          return { success: true }
        }
        return { success: false, error: response.data.error }
      } catch (error) {
        return { success: false, error: '登录失败，请检查网络连接' }
      }
    },
    
    async register({ commit }, userData) {
      try {
        const response = await api.post('/auth/register/', userData)
        if (response.data.success) {
          return { success: true, message: response.data.message }
        } else {
          return { success: false, error: response.data.error }
        }
      } catch (error) {
        return { success: false, error: '注册失败，请检查网络连接' }
      }
    },
    
    logout({ commit }) {
      commit('CLEAR_AUTH')
    },
    
    toggleSidebar({ commit }) {
      commit('TOGGLE_SIDEBAR')
    },

    async refreshUserProfile({ state, commit }) {
      if (!state.token) {
        return { success: false, error: '未登录' }
      }
      try {
        const response = await api.get('/profile/')
        if (response.data && response.data.success && response.data.profile) {
          const profile = response.data.profile
          commit('SET_USER', {
            ...state.user,
            ...profile
          })
          return { success: true, profile }
        }
        return { success: false, error: response.data?.error || '获取用户资料失败' }
      } catch (error) {
        console.error('Refresh user profile error:', error)
        return { success: false, error: '获取用户资料失败' }
      }
    },

    async fetchUnreadCount({ state, commit }) {
      if (!state.token) {
        commit('SET_UNREAD_COUNT', 0)
        return { success: false, error: '未登录' }
      }
      try {
        const response = await api.get('/messages/', {
          params: { page: 1, page_size: 1 }
        })
        if (response.data && response.data.success) {
          const count = response.data.unread_count ?? 0
          commit('SET_UNREAD_COUNT', count)
          return { success: true, count }
        }
        commit('SET_UNREAD_COUNT', 0)
        return { success: false, error: response.data?.error || '获取未读消息失败' }
      } catch (error) {
        console.error('Fetch unread count error:', error)
        commit('SET_UNREAD_COUNT', 0)
        return { success: false, error: '获取未读消息失败' }
      }
    }
  }
})

