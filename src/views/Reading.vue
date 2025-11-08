<template>
  <div class="reading-container">
    
    <div class="reading-content with-toolbar">
      <div class="chapter-content" v-if="chapter">
        <div class="chapter-header">
          <h3>{{ chapter.title }}</h3>
          <div class="chapter-meta">
            <span class="word-count">{{ chapter.word_count }}字</span>
            <span class="publish-time">{{ formatTime(chapter.publish_time) }}</span>
            <el-tag :type="chapter.is_free ? 'success' : 'warning'" size="small">
              {{ chapter.is_free ? '免费章节' : '付费章节' }}
            </el-tag>
          </div>
        </div>
        
        <div 
          class="chapter-text" 
          v-if="chapterAccessible"
          v-html="chapterContent"
        ></div>
        <div class="chapter-locked" v-else>
          <el-result
            icon="warning"
            title="该章节为付费章节"
            :sub-title="`需要订阅后才能阅读（需 ${chapterCost} 点券，1 点券 = 200 字）`"
          />
        </div>
        
        <div class="chapter-actions" v-if="chapter && !chapter.is_free && !chapterAccessible">
          <el-button 
            type="primary" 
            :loading="subscribing"
            @click="subscribeChapter"
          >
            订阅本章节（{{ chapterCost }} 点券）
          </el-button>
        </div>
      </div>
      
      <div v-else class="no-chapter">
        <el-empty description="章节不存在或已被删除">
          <el-button type="primary" @click="goBack">
            返回作品详情
          </el-button>
        </el-empty>
      </div>
    </div>
    
    <!-- 底部工具栏 -->
    <div 
      class="reading-toolbar"
      :style="toolbarStyle"
    >
      <div class="toolbar-content">
        <div class="toolbar-side">
          <el-button 
            class="chapter-nav-btn"
            :disabled="!prevChapterId"
            @click="goToPrevChapter"
          >
            <el-icon><ArrowLeft /></el-icon>
            上一章
          </el-button>
        </div>
        <div class="toolbar-center">
          <el-button @click="showChapterList = true">
            <el-icon><List /></el-icon>
            目录
          </el-button>
          <el-button @click="openWorkDetail">
            <el-icon><InfoFilled /></el-icon>
            详情
          </el-button>
          <el-button @click="toggleComments">
            <el-icon><ChatDotRound /></el-icon>
            评论
          </el-button>
        </div>
        <div class="toolbar-side">
          <el-button 
            class="chapter-nav-btn"
            :disabled="!nextChapterId"
            @click="goToNextChapter"
          >
            下一章
            <el-icon class="icon-right"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 章节目录弹窗 -->
    <el-drawer v-model="showChapterList" title="章节目录" size="400px">
      <div class="chapter-list">
        <div 
          v-for="(chapter, index) in chapters" 
          :key="chapter.chapter_id"
          class="chapter-item"
          :class="{ 
            active: chapter.chapter_id === currentChapterId,
            free: chapter.is_free,
            subscribed: isChapterSubscribed(chapter.chapter_id)
          }"
          @click="goToChapter(chapter.chapter_id)"
        >
          <div class="chapter-info">
            <span class="chapter-number">{{ index + 1 }}</span>
            <span class="chapter-title">{{ chapter.title }}</span>
          </div>
          <div class="chapter-meta">
            <el-tag v-if="chapter.is_free" size="small" type="success">免费</el-tag>
            <el-tag v-else-if="isChapterSubscribed(chapter.chapter_id)" size="small" type="primary">已订阅</el-tag>
            <el-tag v-else size="small" type="warning">付费</el-tag>
            <span class="word-count">{{ chapter.word_count }}字</span>
          </div>
        </div>
      </div>
    </el-drawer>
    
    <!-- 作品详情弹窗 -->
    <el-drawer v-model="showWorkDetail" title="作品详情" size="500px">
      <div class="work-detail" v-if="workDetail">
        <div class="work-cover">
          <img :src="workDetail.cover_url || defaultCover" :alt="workDetail.title">
        </div>
        <div class="work-info">
          <h3>{{ workDetail.title }}</h3>
          <p class="author">{{ workDetail.author_name }}</p>
          <p class="category">{{ workDetail.category_name }}</p>
          <p class="intro">{{ workDetail.intro }}</p>
          <div class="work-stats">
            <span class="stat">
              <el-icon><View /></el-icon>
              {{ formatNumber(workDetail.read_count || 0) }}
            </span>
            <span class="stat">
              <el-icon><Collection /></el-icon>
              {{ formatNumber(workDetail.collect_count || 0) }}
            </span>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 评论抽屉 -->
    <el-drawer
      v-model="showComments"
      title="章节评论"
      size="420px"
    >
      <div class="comment-drawer">
        <div class="comment-compose">
          <el-input
            v-model="chapterCommentContent"
            type="textarea"
            :rows="3"
            placeholder="请输入您的评论..."
          />
          <div class="compose-actions">
            <el-button type="primary" :loading="commentSubmitting" @click="submitChapterComment">
              发表评论
            </el-button>
          </div>
        </div>

        <div class="comment-list">
          <template v-if="chapterCommentsLoading && chapterComments.length === 0">
            <el-skeleton rows="4" animated />
          </template>
          <template v-else>
            <div v-if="chapterComments.length === 0" class="empty-comments">暂无章节评论</div>
            <div v-else>
              <div
                v-for="comment in chapterComments"
                :key="comment.comment_id"
                class="comment-item"
              >
                <div class="comment-avatar">
                  <el-avatar :size="40" :src="comment.avatar_url">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                </div>
                <div class="comment-body">
                  <div class="comment-header">
                    <span class="comment-author">{{ comment.reader_name }}</span>
                    <span class="comment-time">{{ formatDateTime(comment.create_time) }}</span>
                  </div>
                  <p class="comment-text">{{ comment.content }}</p>
                  <div class="comment-actions">
                    <el-button type="text" @click="toggleCommentLike(comment)">
                      <el-icon><Star /></el-icon>
                      {{ comment.like_count || 0 }}
                    </el-button>
                    <el-button type="text" @click="openReplyDialog(comment)">
                      <el-icon><ChatDotRound /></el-icon>
                      追评
                    </el-button>
                  </div>
                  <div class="reply-list" v-if="comment.replies && comment.replies.length">
                    <div
                      v-for="reply in comment.replies"
                      :key="reply.comment_id"
                      class="reply-item"
                    >
                      <div class="comment-header">
                        <span class="comment-author">{{ reply.reader_name }}</span>
                        <span class="comment-time">{{ formatDateTime(reply.create_time) }}</span>
                      </div>
                      <p class="comment-text">{{ reply.content }}</p>
                      <div class="comment-actions">
                        <el-button type="text" @click="toggleCommentLike(reply)">
                          <el-icon><Star /></el-icon>
                          {{ reply.like_count || 0 }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="load-more" v-if="chapterCommentHasMore">
                <el-button type="text" @click="loadMoreChapterComments">加载更多</el-button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </el-drawer>

    <!-- 回复对话框 -->
    <el-dialog
      v-model="commentDialogVisible"
      :title="commentDialogTitle"
      width="420px"
    >
      <el-form :model="replyForm" :rules="replyRules" ref="replyFormRef">
        <el-form-item prop="content">
          <el-input
            v-model="replyForm.content"
            type="textarea"
            :rows="4"
            placeholder="请输入回复内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="commentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReplyComment">发表回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { 
  ArrowLeft, ArrowRight, Menu as MenuIcon, Collection, ChatDotRound, 
  List, InfoFilled, Star
} from '@element-plus/icons-vue'
import { mapGetters } from 'vuex'
import { 
  getWorkDetail, 
  getChapters, 
  getChapterDetail, 
  subscribeChapter as subscribeChapterApi,
  getComments,
  addComment as addCommentApi,
  likeComment as likeCommentApi
} from '@/api'

export default {
  name: 'Reading',
  components: {
    ArrowLeft,
    ArrowRight,
    MenuIcon,
    Collection,
    ChatDotRound,
    List,
    InfoFilled,
    Star
  },
  data() {
    return {
      workId: null,
      currentChapterId: null,
      workTitle: '',
      chapter: null,
      chapters: [],
      workDetail: null,
      showChapterList: false,
      showWorkDetail: false,
      showComments: false,
      isSubscribed: false,
      hasFullSubscription: false,
      subscribedChapterIds: [],
      canReadChapter: true,
      requiresSubscription: false,
      chapterCost: 0,
      subscribing: false,
      chapterComments: [],
      chapterCommentsLoading: false,
      chapterCommentPage: 1,
      chapterCommentPageSize: 10,
      chapterCommentHasMore: false,
      chapterCommentContent: '',
      commentSubmitting: false,
      commentDialogVisible: false,
      commentDialogTitle: '',
      replyForm: {
        content: '',
        parent_id: null
      },
      replyRules: {
        content: [
          { required: true, message: '请输入评论内容', trigger: 'blur' },
          { min: 3, message: '评论内容不能少于3个字符', trigger: 'blur' }
        ]
      },
      defaultCover: 'https://via.placeholder.com/200x280/667eea/ffffff?text=封面'
    }
  },
  computed: {
    ...mapGetters(['sidebarCollapsed']),
    chapterContent() {
      if (!this.chapter || !this.chapter.content) return ''
      return String(this.chapter.content).replace(/\n/g, '<br>')
    },
    chapterAccessible() {
      if (!this.chapter) return false
      if (this.chapter.is_free) return true
      if (this.hasFullSubscription) return true
      if (this.isSubscribed) return true
      return this.canReadChapter
    },
    toolbarStyle() {
      const sidebarWidth = this.sidebarCollapsed ? 60 : 250
      return {
        marginLeft: `${sidebarWidth}px`,
        width: `calc(100% - ${sidebarWidth}px)`
      }
    },
    currentChapterIndex() {
      if (!this.chapters || !this.chapters.length || !this.currentChapterId) {
        return -1
      }
      const currentId = Number(this.currentChapterId)
      return this.chapters.findIndex(chapter => Number(chapter.chapter_id) === currentId)
    },
    prevChapterId() {
      const index = this.currentChapterIndex
      if (index > 0) {
        return this.chapters[index - 1]?.chapter_id || null
      }
      return null
    },
    nextChapterId() {
      const index = this.currentChapterIndex
      if (index >= 0 && index < this.chapters.length - 1) {
        return this.chapters[index + 1]?.chapter_id || null
      }
      return null
    }
  },
  created() {
    this.initialize()
  },
  watch: {
    '$route.params.workId'(newVal, oldVal) {
      if (newVal && newVal !== oldVal) {
        this.initialize()
      }
    },
    '$route.params.chapterId'(newVal, oldVal) {
      if (newVal && newVal !== oldVal) {
        this.currentChapterId = newVal
        this.loadChapter(newVal)
        if (this.showComments) {
          this.resetChapterComments()
          this.loadChapterComments(true)
        }
      }
    },
    showComments(newVal) {
      if (newVal) {
        this.resetChapterComments()
        this.loadChapterComments(true)
      }
    }
  },
  methods: {
    async initialize() {
      try {
        this.workId = Number(this.$route.params.workId)
        this.currentChapterId = this.$route.params.chapterId
        this.chapter = null
        this.chapters = []
        this.isSubscribed = false
        this.hasFullSubscription = false
        this.subscribedChapterIds = []
        this.canReadChapter = true
        this.requiresSubscription = false
        this.chapterCost = 0
        this.subscribing = false
        this.resetChapterComments()
        this.chapterCommentContent = ''
        this.commentDialogVisible = false
        await this.loadWorkDetail()
        await this.loadChapters()
        await this.loadChapter(this.currentChapterId)
      } catch (error) {
        console.error('Initialize reading view error:', error)
      }
    },

    async loadWorkDetail() {
      try {
        const response = await getWorkDetail(this.workId)
        if (response.data && response.data.success) {
          this.workDetail = response.data.work || {}
          this.workTitle = this.workDetail.title
        }
      } catch (error) {
        console.error('Load work detail error:', error)
      }
    },

    async loadChapters() {
      try {
        const response = await getChapters(this.workId)
        if (response.data && response.data.success) {
          this.chapters = response.data.chapters || []
          if (!this.workTitle) {
            this.workTitle = response.data.work_title || ''
          }
          this.hasFullSubscription = !!response.data.has_full_subscription
          this.subscribedChapterIds = (response.data.subscribed_chapter_ids || []).map(id => Number(id))
          if (this.currentChapterId) {
            const chapterIdNumber = Number(this.currentChapterId)
            this.isSubscribed = this.hasFullSubscription || this.subscribedChapterIds.includes(chapterIdNumber)
          }
          if (!this.currentChapterId && this.chapters.length > 0) {
            this.currentChapterId = this.chapters[0].chapter_id
          }
        } else {
          this.$message.error(response.data?.error || '章节目录加载失败')
        }
      } catch (error) {
        console.error('Load chapters error:', error)
        this.$message.error('章节目录加载失败，请稍后重试')
      }
    },

    async loadChapter(chapterId) {
      try {
        let targetChapterId = chapterId || this.currentChapterId
        if (!targetChapterId && this.chapters.length > 0) {
          targetChapterId = this.chapters[0].chapter_id
        }
        if (!targetChapterId) {
          this.chapter = null
          return
        }

        const response = await getChapterDetail(this.workId, targetChapterId)
        if (response.data && response.data.success) {
          this.chapter = response.data.chapter
          this.currentChapterId = this.chapter.chapter_id
          this.chapterCost = response.data.cost || 0
          this.canReadChapter = response.data.can_read !== false
          this.requiresSubscription = !this.canReadChapter && this.chapter && !this.chapter.is_free
          this.isSubscribed = this.hasFullSubscription || !!response.data.is_subscribed
          if (this.chapter) {
            this.chapter.cost = this.chapterCost
            const chapterIdNumber = Number(this.chapter.chapter_id)
            if (this.isSubscribed && !this.subscribedChapterIds.includes(chapterIdNumber)) {
              this.subscribedChapterIds.push(chapterIdNumber)
            }
          }
        } else {
          this.chapter = null
          this.$message.error(response.data?.error || '章节加载失败')
        }
      } catch (error) {
        console.error('Load chapter error:', error)
        this.$message.error('章节加载失败，请稍后重试')
      }
    },
    
    goBack() {
      this.$router.go(-1)
    },
    
    goToChapter(chapterId) {
      if (!chapterId) return
      this.currentChapterId = chapterId
      this.$router.push(`/main/reading/${this.workId}/${chapterId}`)
      this.loadChapter(chapterId)
      this.showChapterList = false
    },
    
    toggleSidebar() {
      this.showChapterList = true
    },

    openWorkDetail() {
      if (this.workId) {
        this.showWorkDetail = false
        this.$router.push(`/main/work-detail/${this.workId}`)
      }
    },

    async subscribeChapter() {
      if (!this.chapter) return
      if (this.subscribing) return
      try {
        this.subscribing = true
        const response = await subscribeChapterApi(this.workId, this.chapter.chapter_id)
        if (response.data && response.data.success) {
          const cost = response.data.cost || 0
          const successMessage = response.data.message || `订阅成功，消耗 ${cost} 点券`
          this.$message.success(successMessage)
          await this.loadChapters()
          await this.loadChapter(this.chapter.chapter_id)
        } else {
          this.$message.error(response.data?.error || '订阅失败')
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || '订阅失败，请稍后重试'
        this.$message.error(errorMessage)
        console.error('Subscribe chapter error:', error)
      } finally {
        this.subscribing = false
      }
    },

    toggleComments() {
      this.showComments = !this.showComments
      if (this.showComments) {
        this.resetChapterComments()
        this.loadChapterComments(true)
      }
    },

    goToPrevChapter() {
      if (!this.prevChapterId) return
      this.goToChapter(this.prevChapterId)
    },

    goToNextChapter() {
      if (!this.nextChapterId) return
      this.goToChapter(this.nextChapterId)
    },

    resetChapterComments() {
      this.chapterCommentPage = 1
      this.chapterComments = []
      this.chapterCommentHasMore = false
    },

    normalizeComments(raw = []) {
      return (raw || []).map(comment => ({
        ...comment,
        replies: this.normalizeComments(comment.replies || [])
      }))
    },

    async loadChapterComments(reset = false) {
      if (!this.workId || !this.currentChapterId) {
        this.chapterComments = []
        this.chapterCommentHasMore = false
        return
      }

      if (reset) {
        this.chapterCommentPage = 1
        this.chapterComments = []
        this.chapterCommentHasMore = false
      }

      this.chapterCommentsLoading = true
      try {
        const response = await getComments(this.workId, {
          type: 'chapter',
          chapter_id: this.currentChapterId,
          page: this.chapterCommentPage,
          page_size: this.chapterCommentPageSize
        })

        if (response.data && response.data.success) {
          const fetched = this.normalizeComments(response.data.comments || [])
          if (this.chapterCommentPage === 1) {
            this.chapterComments = fetched
          } else {
            this.chapterComments = [...this.chapterComments, ...fetched]
          }

          const total = response.data.total || 0
          this.chapterCommentHasMore = this.chapterComments.length < total
          if (this.chapterCommentHasMore) {
            this.chapterCommentPage += 1
          }
        } else {
          this.$message.error(response.data?.error || '加载评论失败')
        }
      } catch (error) {
        console.error('Load chapter comments error:', error)
        this.$message.error('加载评论失败，请稍后重试')
      } finally {
        this.chapterCommentsLoading = false
      }
    },

    loadMoreChapterComments() {
      if (this.chapterCommentHasMore && !this.chapterCommentsLoading) {
        this.loadChapterComments(false)
      }
    },

    isChapterSubscribed(chapterId) {
      const id = Number(chapterId)
      if (this.hasFullSubscription) return true
      if (this.subscribedChapterIds.includes(id)) return true
      if (this.chapter && Number(this.chapter.chapter_id) === id) {
        return this.chapterAccessible
      }
      return false
    },

    async submitChapterComment() {
      if (!this.currentChapterId) {
        this.$message.warning('未找到章节信息')
        return
      }

      const content = (this.chapterCommentContent || '').trim()
      if (!content) {
        this.$message.warning('请输入评论内容')
        return
      }
      if (content.length < 3) {
        this.$message.warning('评论内容不能少于3个字符')
        return
      }

      this.commentSubmitting = true
      try {
        const response = await addCommentApi(this.workId, {
          content,
          chapter_id: this.currentChapterId
        })

        if (response.data && response.data.success) {
          this.$message.success('评论发表成功')
          this.chapterCommentContent = ''
          this.resetChapterComments()
          await this.loadChapterComments(true)
        } else {
          this.$message.error(response.data?.error || '评论发表失败')
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || '评论发表失败，请稍后重试'
        this.$message.error(errorMessage)
        console.error('Submit chapter comment error:', error)
      } finally {
        this.commentSubmitting = false
      }
    },

    openReplyDialog(comment) {
      this.replyForm = {
        content: '',
        parent_id: comment.comment_id
      }
      this.commentDialogTitle = `回复 ${comment.reader_name || '读者'}`
      this.commentDialogVisible = true
      this.$nextTick(() => {
        if (this.$refs.replyFormRef) {
          this.$refs.replyFormRef.clearValidate()
        }
      })
    },

    async submitReplyComment() {
      try {
        await this.$refs.replyFormRef.validate()
      } catch (error) {
        return
      }

      if (!this.currentChapterId || !this.replyForm.parent_id) {
        this.$message.error('回复目标不存在')
        return
      }

      try {
        const response = await addCommentApi(this.workId, {
          content: this.replyForm.content,
          chapter_id: this.currentChapterId,
          parent_id: this.replyForm.parent_id
        })

        if (response.data && response.data.success) {
          this.$message.success('回复成功')
          this.commentDialogVisible = false
          this.replyForm = { content: '', parent_id: null }
          this.resetChapterComments()
          await this.loadChapterComments(true)
        } else {
          this.$message.error(response.data?.error || '回复失败')
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || '回复失败，请稍后重试'
        this.$message.error(errorMessage)
        console.error('Submit reply comment error:', error)
      }
    },

    async toggleCommentLike(comment) {
      try {
        const response = await likeCommentApi(this.workId, comment.comment_id)
        if (response.data && response.data.success) {
          comment.like_count = response.data.like_count
          comment.liked = response.data.liked
        } else {
          this.$message.error(response.data?.error || '操作失败')
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || '操作失败，请稍后重试'
        this.$message.error(errorMessage)
        console.error('Toggle comment like error:', error)
      }
    },

    formatDateTime(timeString) {
      if (!timeString) return ''
      return new Date(timeString).toLocaleString()
    },

    formatTime(timeString) {
      if (!timeString) return ''
      const time = new Date(timeString)
      return time.toLocaleDateString()
    },
    
    formatNumber(num) {
      const value = Number(num) || 0
      if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万'
      }
      return value.toString()
    }
  }
}
</script>

<style scoped>
.reading-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.reading-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.back-btn {
  color: #667eea;
  font-size: 1.1rem;
}

.reading-header h2 {
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0;
}

.reading-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.chapter-content {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chapter-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.chapter-header h3 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.chapter-meta {
  display: flex;
  justify-content: center;
  gap: 20px;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.chapter-text {
  color: #2c3e50;
  font-size: 1.1rem;
  line-height: 1.8;
  margin-bottom: 40px;
  text-indent: 2em;
}

.chapter-locked {
  padding: 40px 0;
}

.chapter-locked .el-result {
  margin-top: 20px;
}

.chapter-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.no-chapter {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.reading-content.with-toolbar {
  padding-bottom: 110px;
}

.reading-toolbar {
  position: fixed;
  bottom: 0;
  left: 0;
  background: white;
  border-top: 1px solid #e0e0e0;
  padding: 18px 32px;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.08);
  z-index: 998;
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 20px;
}

.toolbar-side {
  display: flex;
  align-items: center;
}

.toolbar-content .el-button {
  border-radius: 24px;
  padding: 12px 28px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.chapter-nav-btn {
  min-width: 140px;
  justify-content: center;
}

.chapter-nav-btn .icon-right {
  margin-left: 4px;
}

.chapter-list {
  padding: 20px 0;
}

.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.3s ease;
}

.chapter-item:hover {
  background: #f8f9fa;
}

.chapter-item.active {
  background: #e3f2fd;
  border-left: 4px solid #667eea;
}

.chapter-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.chapter-number {
  color: #7f8c8d;
  font-size: 0.9rem;
  min-width: 30px;
}

.chapter-title {
  color: #2c3e50;
  font-weight: 500;
}

.chapter-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.word-count {
  color: #7f8c8d;
  font-size: 0.8rem;
}

.work-detail {
  padding: 20px;
}

.work-cover {
  text-align: center;
  margin-bottom: 20px;
}

.work-cover img {
  width: 200px;
  height: 280px;
  object-fit: cover;
  border-radius: 8px;
}

.work-info h3 {
  color: #2c3e50;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.author, .category {
  color: #7f8c8d;
  margin: 0 0 5px 0;
}

.intro {
  color: #5a6c7d;
  line-height: 1.6;
  margin: 15px 0;
}

.work-stats {
  display: flex;
  gap: 20px;
  margin-top: 15px;
}

.comment-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.comment-compose {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
}

.compose-actions {
  margin-top: 12px;
  text-align: right;
}

.comment-drawer .comment-list {
  flex: 1;
  margin-top: 20px;
  overflow-y: auto;
  padding-right: 8px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.comment-avatar {
  flex-shrink: 0;
}

.comment-body {
  flex: 1;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.comment-author {
  font-weight: 600;
  color: #2c3e50;
}

.comment-time {
  font-size: 0.8rem;
  color: #94a3b8;
}

.comment-text {
  margin: 0 0 10px 0;
  color: #4b5563;
  line-height: 1.6;
}

.comment-actions {
  display: flex;
  gap: 12px;
}

.reply-list {
  margin-top: 10px;
  padding-left: 48px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reply-item {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px 12px;
}

.empty-comments {
  text-align: center;
  color: #94a3b8;
  padding: 30px 0;
}

.comment-drawer .load-more {
  text-align: center;
  margin-top: 10px;
}

.stat .el-icon {
  color: #667eea;
}

@media (max-width: 768px) {
  .reading-content {
    padding: 20px;
  }
  
  .chapter-content {
    padding: 20px;
  }
  
  .chapter-header h3 {
    font-size: 1.4rem;
  }
  
  .chapter-text {
    font-size: 1rem;
  }
  
  .chapter-actions {
    flex-wrap: wrap;
  }
  
  .chapter-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .chapter-meta {
    align-self: flex-end;
  }
}
</style>

