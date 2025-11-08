import axios from 'axios'
import store from '../store'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = store.getters.token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    if (error.response && error.response.status === 401) {
      // Token过期，清除认证信息
      store.dispatch('logout')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API 接口函数
export const login = (data) => api.post('/auth/login/', data)
export const register = (data) => api.post('/auth/register/', data)
export const adminLogin = (data) => api.post('/admin/auth/login/', data)
export const adminRegister = (data) => api.post('/admin/auth/register/', data)
export const getUserInfo = () => api.get('/auth/user/')
export const logout = () => api.post('/auth/logout/')
export const getUserProfile = () => api.get('/profile/')
export const updateUserProfile = (data) => api.put('/profile/', data)
export const getUserStats = () => api.get('/profile/stats/')
export const updateContactInfo = (data) => api.put('/profile/contact/', data)
export const changeUserPassword = (data) => api.put('/profile/password/', data)
export const rechargeBalance = (data) => api.post('/profile/recharge/', data)
export const uploadAvatarFile = (formData) =>
  api.post('/uploads/avatar/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

export const uploadCoverFile = (formData) =>
  api.post('/uploads/cover/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

// 作品相关
export const getWorks = (params) => api.get('/works/', { params })
export const getWorkDetail = (id) => api.get(`/works/${id}/`)
export const createWork = (data) => api.post('/works/', data)
export const updateWork = (id, data) => api.put(`/works/${id}/update/`, data)
export const deleteWork = (id) => api.delete(`/works/${id}/`)

// 章节相关
export const getChapters = (workId) => api.get(`/works/${workId}/chapters/`)
export const getChapterDetail = (workId, chapterId) => api.get(`/works/${workId}/chapters/${chapterId}/`)
export const createChapter = (workId, data) => api.post(`/works/${workId}/chapters/create/`, data)
export const updateChapter = (workId, chapterId, data) => api.put(`/works/${workId}/chapters/${chapterId}/`, data)
export const deleteChapter = (workId, chapterId) => api.delete(`/works/${workId}/chapters/${chapterId}/delete/`)
export const subscribeChapter = (workId, chapterId) => api.post(`/works/${workId}/chapters/${chapterId}/subscribe/`)
export const getWorkMetrics = (workId) => api.get(`/works/${workId}/metrics/`)

// 书架相关
export const getBookshelf = () => api.get('/bookshelf/')
export const addToBookshelf = (workId) => api.post('/bookshelf/add/', { work_id: workId })
export const removeFromBookshelf = (workId) => api.delete(`/bookshelf/remove/${workId}/`)

// 收藏相关
export const getCollections = () => api.get('/collections/')
export const addCollection = (workId) => api.post('/collections/', { work_id: workId })
export const removeCollection = (workId) => api.delete(`/collections/${workId}/`)

// 阅读记录
export const getReadingHistory = () => api.get('/reading/history/')
export const updateReadingRecord = (workId, chapterId) => api.post('/reading-records/', { work_id: workId, chapter_id: chapterId })

// 排行榜
export const getRankings = (params) => {
  if (typeof params === 'string') {
    return api.get('/rankings/', { params: { type: params } })
  }
  return api.get('/rankings/', { params })
}

// 推荐
export const getRecommendations = () => api.get('/recommendations/')
export const sendRecommendationFeedback = (data) => api.post('/recommendations/feedback/', data)

// 搜索
export const searchWorks = (params) => api.get('/search/', { params })
export const getSearchHistory = (params) => api.get('/search/history/', { params })

// 分类
export const getCategories = () => api.get('/categories/')

// 评论
export const getComments = (workId, params) => api.get(`/works/${workId}/comments/`, { params })
export const addComment = (workId, data) => api.post(`/works/${workId}/comments/create/`, data)
export const updateComment = (workId, commentId, data) => api.put(`/works/${workId}/comments/${commentId}/`, data)
export const deleteComment = (workId, commentId) => api.delete(`/works/${workId}/comments/${commentId}/delete/`)
export const likeComment = (workId, commentId) => api.post(`/works/${workId}/comments/${commentId}/like/`)
export const getCommentHistory = (params) => api.get('/comments/history/', { params })
export const deleteUserComment = (commentId) => api.delete(`/comments/${commentId}/delete/`)
export const getCommentThread = (commentId) => api.get(`/comments/${commentId}/`)

// 消息
export const getMessages = (params) => api.get('/messages/', { params })
export const markMessageRead = (messageId) => api.put(`/messages/${messageId}/read/`)
export const markAllMessagesRead = () => api.put('/messages/mark-all-read/')
export const deleteMessage = (messageId) => api.delete(`/messages/${messageId}/delete/`)

// 点券和投票系统
export const getUserPoints = () => api.get('/points/')
export const purchasePoints = (data) => api.post('/points/purchase/', data)
export const voteWork = (workId, data) => api.post(`/works/${workId}/vote/`, data)
export const getVoteRecords = (workId, params) => api.get(`/works/${workId}/votes/`, { params })
export const getUserSubscriptionRecords = (params) => api.get('/subscriptions/records/', { params })
export const getUserVoteRecords = (params) => api.get('/votes/records/', { params })

// 管理员相关
export const fetchAdminUsers = (params) => api.get('/admin/users/', { params })
export const updateUserPermissions = (userId, data) => api.put(`/admin/users/${userId}/permissions/`, data)
export const fetchAdminWorks = (params) => api.get('/admin/works/', { params })
export const updateWorkModeration = (workId, data) => api.put(`/admin/works/${workId}/moderation/`, data)
export const updateChapterStatus = (chapterId, data) => api.put(`/admin/chapters/${chapterId}/status/`, data)
export const fetchAdminComments = (params) => api.get('/admin/comments/', { params })
export const deleteAdminComment = (commentId, data) => api.delete(`/admin/comments/${commentId}/`, { data })
export const fetchAdminActionLogs = (params) => api.get('/admin/action-logs/', { params })
export const fetchUserActionLogs = (params) => api.get('/admin/user-action-logs/', { params })

export default api

