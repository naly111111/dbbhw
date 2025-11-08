<template>
  <div class="work-detail-container">
    <div class="work-header">
      <div class="work-cover">
        <img :src="workDetail.cover_url || defaultCover" :alt="workDetail.title">
      </div>
      
      <div class="work-info">
        <h1 class="work-title">{{ workDetail.title }}</h1>
        <div class="work-meta">
          <span class="author">
            <el-icon><User /></el-icon>
            {{ authorDisplayName }}
          </span>
          <span class="category">
            <el-icon><Grid /></el-icon>
            {{ categoryDisplayName }}
          </span>
          <span class="status">
            <el-tag :type="getStatusType(workDetail.status) || 'info'">
              {{ getStatusText(workDetail.status) }}
            </el-tag>
          </span>
        </div>
        
        <div class="work-stats">
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(workDetail.read_count || 0) }}</span>
            <span class="stat-label">阅读量</span>
            <span class="stat-sub">独立读者 {{ formatNumber(workDetail.unique_readers || 0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(workDetail.collect_count || 0) }}</span>
            <span class="stat-label">收藏数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(workDetail.subscription_count || 0) }}</span>
            <span class="stat-label">订阅数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatNumber(workDetail.vote_count || 0) }}</span>
            <span class="stat-label">投票数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ workDetail.chapter_count || 0 }}</span>
            <span class="stat-label">章节数</span>
          </div>
        </div>
        
        <div class="work-actions">
          <el-button 
            type="primary" 
            size="large"
            @click="startReading"
            class="read-btn"
          >
            <el-icon><Reading /></el-icon>
            开始阅读
          </el-button>
          <el-button 
            size="large"
            @click="toggleCollection"
            :type="isCollected ? 'success' : 'default'"
          >
            <el-icon><Collection /></el-icon>
            {{ isCollected ? '已收藏' : '收藏' }}
          </el-button>
          <el-button size="large" @click="openVoteDialog">
            <el-icon><Star /></el-icon>
            投月票
          </el-button>
        </div>
      </div>
    </div>
    
    <div class="work-content">
      <el-tabs v-model="activeTab" class="work-tabs">
        <el-tab-pane label="作品简介" name="intro">
          <div class="intro-content">
            <div class="intro-text" v-html="renderedIntro"></div>
            
            <div class="work-tags" v-if="workDetail.tags && workDetail.tags.length > 0">
              <h4>作品标签</h4>
              <div class="tags-list">
                <el-tag 
                  v-for="tag in workDetail.tags" 
                  :key="tag"
                  class="tag-item"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="章节目录" name="chapters">
          <div class="chapters-content">
            <div class="chapters-header">
              <h3>章节目录</h3>
              <div class="chapter-filters">
                <el-radio-group v-model="chapterFilter" @change="filterChapters">
                  <el-radio label="all">全部</el-radio>
                  <el-radio label="free">免费</el-radio>
                  <el-radio label="paid">付费</el-radio>
                </el-radio-group>
              </div>
            </div>
            
            <div class="chapters-list">
              <div 
                v-for="(chapter, index) in filteredChapters" 
                :key="chapter.chapter_id"
                class="chapter-item"
                @click="readChapter(chapter.chapter_id)"
              >
                <div class="chapter-info">
                  <span class="chapter-number">{{ index + 1 }}</span>
                  <span class="chapter-title">{{ chapter.title }}</span>
                </div>
                <div class="chapter-meta">
                  <el-tag 
                    :type="chapter.is_free ? 'success' : 'warning' || 'info'"
                    size="small"
                  >
                    {{ chapter.is_free ? '免费' : '付费' }}
                  </el-tag>
                  <span class="word-count">{{ chapter.word_count }}字</span>
                  <span class="publish-time">{{ formatTime(chapter.publish_time) }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="评论" name="comments">
          <div class="comments-wrapper">
            <div class="comments-column book-comments">
              <div class="comments-header">
                <h3>作品评论</h3>
                <el-button type="primary" @click="openCommentDialog('book')">
                  <el-icon><Edit /></el-icon>
                  发表评论
                </el-button>
              </div>

              <div class="comment-list">
                <template v-if="bookCommentsLoading && bookComments.length === 0">
                  <el-skeleton rows="4" animated />
                </template>
                <template v-else>
                  <div v-if="bookComments.length === 0" class="empty-comments">暂无作品评论</div>
                  <div v-else>
                    <div 
                      v-for="comment in bookComments"
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
                          <el-button type="text" @click="openReplyDialog(comment, 'book')">
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
                    <div class="load-more" v-if="bookCommentHasMore">
                      <el-button type="text" @click="loadMoreBookComments">加载更多</el-button>
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <div class="comments-column chapter-comments">
              <div class="comments-header">
                <h3>章节评论</h3>
                <div class="chapter-controls">
                  <el-select 
                    v-model="selectedChapterId"
                    placeholder="选择章节"
                    size="small"
                    @change="handleChapterSelect"
                    class="chapter-select"
                  >
                    <el-option
                      v-for="chapter in chapters"
                      :key="chapter.chapter_id"
                      :label="`${chapter.chapter_order || 0}. ${chapter.title}${chapter.comment_count ? `（${chapter.comment_count}）` : ''}`"
                      :value="chapter.chapter_id"
                    />
                  </el-select>
                  <el-button 
                    type="primary" 
                    @click="openCommentDialog('chapter', { chapter_id: selectedChapterId })"
                    :disabled="!selectedChapterId"
                  >
                    <el-icon><Edit /></el-icon>
                    发表评论
                  </el-button>
                </div>
              </div>

              <div class="comment-list">
                <template v-if="chapterCommentsLoading && chapterComments.length === 0">
                  <el-skeleton rows="4" animated />
                </template>
                <template v-else>
                  <div v-if="!selectedChapterId" class="empty-comments">请选择章节查看评论</div>
                  <div v-else-if="chapterComments.length === 0" class="empty-comments">暂无章节评论</div>
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
                          <el-button type="text" @click="openReplyDialog(comment, 'chapter')">
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
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="投票记录" name="votes">
          <div class="votes-content">
            <div v-if="voteRecords.length === 0" class="empty-state">
              暂无投票记录
            </div>
            <div v-else class="votes-list">
              <div 
                v-for="record in voteRecords"
                :key="record.vote_id"
                class="vote-item"
              >
                <div class="vote-header">
                  <span class="vote-reader">{{ record.reader_name }}</span>
                  <span class="vote-time">{{ formatTime(record.vote_time) }}</span>
                </div>
                <div class="vote-body">
                  <span class="vote-count">投出 {{ record.count }} 张月票</span>
                  <span v-if="record.message" class="vote-message">{{ record.message }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="作者信息" name="author">
          <div class="author-content">
            <div class="author-info">
              <div class="author-avatar">
                <el-avatar :size="80" :src="authorAvatarUrl">
                  <el-icon><User /></el-icon>
                </el-avatar>
              </div>
              <div class="author-details">
                <h3>{{ workDetail.author_name }}</h3>
                <p class="author-intro">{{ authorInfo.intro || '暂无简介' }}</p>
                <div class="author-stats">
                  <div class="stat-item">
                    <span class="stat-value">{{ authorInfo.works_count || 0 }}</span>
                    <span class="stat-label">作品数</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ formatNumber(authorInfo.total_reads || 0) }}</span>
                    <span class="stat-label">总阅读量</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="author-works">
              <h4>该作者的其他作品</h4>
              <div class="works-grid">
                <div 
                  v-for="work in authorWorks" 
                  :key="work.work_id"
                  class="work-card"
                  @click="goToWork(work.work_id)"
                >
                  <img :src="work.cover_url || defaultCover" :alt="work.title">
                  <h5>{{ work.title }}</h5>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 评论对话框 -->
    <el-dialog
      v-model="commentDialogVisible"
      :title="commentDialogTitle"
      width="500px"
    >
      <el-form :model="commentForm" :rules="commentRules" ref="commentFormRef">
        <el-form-item prop="content">
          <el-input
            v-model="commentForm.content"
            type="textarea"
            :rows="4"
            placeholder="请输入您的评论..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="commentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitComment">发表评论</el-button>
      </template>
    </el-dialog>

    <!-- 投票对话框 -->
    <el-dialog
      v-model="showVoteDialog"
      title="投月票"
      width="400px"
      @closed="resetVoteForm"
    >
      <el-form
        :model="voteForm"
        :rules="voteRules"
        ref="voteFormRef"
        label-position="top"
      >
        <el-form-item label="月票数量" prop="ticket_count">
          <el-input-number
            v-model="voteForm.ticket_count"
            :min="1"
            :max="100"
            :step="1"
            controls-position="right"
            style="width: 100%"
          />
          <p class="vote-cost-hint">
            本次需要 {{ voteCost }} 张月票，当前可用 {{ userTicketCount }} 张
          </p>
        </el-form-item>
        <el-form-item label="投票留言（可选）">
          <el-input
            v-model="voteForm.message"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="给作者留言鼓励..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showVoteDialog = false">取消</el-button>
        <el-button type="primary" @click="handleVote">确认投票</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { 
  User, Grid, Reading, Collection, Star, Edit, ChatDotRound 
} from '@element-plus/icons-vue'
import { 
  getWorkDetail, 
  getChapters, 
  addToBookshelf, 
  removeFromBookshelf, 
  getComments, 
  addComment, 
  likeComment,
  voteWork, 
  getVoteRecords, 
  getUserPoints,
  getCategories,
  getWorkMetrics
} from '@/api'

export default {
  name: 'WorkDetail',
  components: {
    User,
    Grid,
    Reading,
    Collection,
    Star,
    Edit,
    ChatDotRound
  },
  data() {
    return {
      workId: null,
      workDetail: {},
      chapters: [],
      bookComments: [],
      chapterComments: [],
      authorInfo: {},
      authorWorks: [],
      voteRecords: [],
      activeTab: 'intro',
      chapterFilter: 'all',
      isCollected: false,
      showVoteDialog: false,
      userTicketCount: 0,
      categoryMap: {},
      workMetrics: null,
      bookCommentsLoading: false,
      chapterCommentsLoading: false,
      bookCommentPage: 1,
      bookCommentPageSize: 10,
      bookCommentHasMore: false,
      chapterCommentPage: 1,
      chapterCommentPageSize: 10,
      chapterCommentHasMore: false,
      selectedChapterId: null,
      commentDialogVisible: false,
      commentDialogTitle: '',
      commentForm: {
        content: '',
        mode: 'book',
        chapter_id: null,
        parent_id: null
      },
      voteForm: {
        ticket_count: 1,
        message: ''
      },
      commentRules: {
        content: [
          { required: true, message: '请输入评论内容', trigger: 'blur' },
          { min: 3, message: '评论内容不能少于3个字符', trigger: 'blur' }
        ]
      },
      voteRules: {
        ticket_count: [
          { required: true, type: 'number', min: 1, message: '至少投 1 张月票', trigger: 'blur' }
        ]
      },
      defaultCover: 'https://via.placeholder.com/200x280/667eea/ffffff?text=封面'
    }
  },
  computed: {
    filteredChapters() {
      if (this.chapterFilter === 'all') {
        return this.chapters
      } else if (this.chapterFilter === 'free') {
        return this.chapters.filter(chapter => chapter.is_free)
      } else if (this.chapterFilter === 'paid') {
        return this.chapters.filter(chapter => !chapter.is_free)
      }
      return this.chapters
    },
    renderedIntro() {
      const intro = (this.workDetail.intro && this.workDetail.intro.trim()) ? this.workDetail.intro : '暂无简介'
      return intro.replace(/\n/g, '<br>')
    },
    voteCost() {
      return this.voteForm.ticket_count || 1
    },
    authorDisplayName() {
      const work = this.workDetail || {}
      const info = this.authorInfo || {}
      const candidates = [
        work.author_name,
        work.author_pen_name,
        work.author_nickname,
        info.author_name,
        info.pen_name,
        info.nickname,
        work.author_username,
        info.username
      ]
      const name = candidates.find(item => typeof item === 'string' && item.trim())
      return name ? name.trim() : '未知作者'
    },
    categoryDisplayName() {
      const work = this.workDetail || {}
      if (typeof work.category_name === 'string' && work.category_name.trim()) {
        return work.category_name.trim()
      }
      const categoryId = work.category_id
      if (categoryId && this.categoryMap && this.categoryMap[categoryId]) {
        return this.categoryMap[categoryId]
      }
      return '未分类'
    },
    authorAvatarUrl() {
      const info = this.authorInfo || {}
      const work = this.workDetail || {}
      const candidates = [info.avatar_url, info.author_avatar_url, work.author_avatar_url]
      const url = candidates.find(item => typeof item === 'string' && item.trim())
      return url ? url.trim() : ''
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
    }
  },
  methods: {
    async initialize() {
      try {
        this.workId = Number(this.$route.params.workId)
        this.activeTab = 'intro'
        this.chapters = []
        this.workDetail = {}
        this.authorInfo = {}
        this.authorWorks = []
        this.workMetrics = null
        this.bookComments = []
        this.chapterComments = []
        this.bookCommentPage = 1
        this.chapterCommentPage = 1
        this.bookCommentHasMore = false
        this.chapterCommentHasMore = false
        this.isCollected = false
        this.selectedChapterId = null
        await this.loadWorkDetail()
        await this.loadChapters()
        await this.loadBookComments(true)
        if (this.chapters.length > 0) {
          this.selectedChapterId = this.chapters[0].chapter_id
          await this.loadChapterComments(true, this.selectedChapterId)
        } else {
          this.selectedChapterId = null
          this.chapterComments = []
        }
        await this.loadVoteRecords()
        await this.loadUserTickets()
      } catch (error) {
        console.error('Initialize work detail error:', error)
      }
    },
    
    async loadWorkDetail() {
       try {
         const response = await getWorkDetail(this.workId)
         if (response.data && response.data.success) {
           const work = response.data.work || {}
           const introText = typeof work.intro === 'string' ? work.intro : ''
           const authorName = work.author_name || response.data.author_info?.author_name || ''
           const categoryName = work.category_name && work.category_name !== '未分类' ? work.category_name : (work.category_name || response.data.work?.category_name || '未分类')

           this.workDetail = {
             ...work,
             intro: introText,
             author_name: authorName,
             category_name: categoryName,
             read_count: Number(work.read_count || 0),
             collect_count: Number(work.collect_count || 0),
             subscription_count: Number(work.subscription_count || 0),
             vote_count: Number(work.vote_count || 0),
             unique_readers: Number(work.unique_readers || 0),
             chapter_count: Number(work.chapter_count || response.data.work?.chapter_count || 0)
           }
           this.isCollected = !!response.data.is_collected
           this.authorInfo = {
             ...(response.data.author_info || {}),
             intro: (response.data.author_info?.intro && response.data.author_info.intro.trim()) ? response.data.author_info.intro : '作者暂未填写简介'
           }
           this.authorWorks = response.data.author_works || []
           await this.ensureCategoryName()
           await this.loadWorkMetrics()
         } else {
           this.$message.error(response.data?.error || '加载作品详情失败')
         }
       } catch (error) {
         console.error('Load work detail error:', error)
         this.$message.error('加载作品详情失败，请稍后重试')
       }
     },

    async ensureCategoryName() {
       if (!this.workDetail.category_id) return
       if (this.workDetail.category_name && this.workDetail.category_name !== '未分类' && this.workDetail.category_name !== '未知') return
       if (!Object.keys(this.categoryMap).length) {
         try {
          const resp = await getCategories()
          if (resp.data && resp.data.success) {
            this.categoryMap = (resp.data.categories || []).reduce((map, item) => {
              map[item.category_id] = item.name
              return map
            }, {})
          }
        } catch (error) {
          console.warn('Category lookup failed', error)
        }
      }
      const name = this.categoryMap[this.workDetail.category_id]
      if (name) {
        this.workDetail.category_name = name
      }
    },

    async loadWorkMetrics() {
      try {
        const resp = await getWorkMetrics(this.workId)
        if (resp.data && resp.data.success) {
          const metrics = resp.data.metrics || {}
          this.workMetrics = metrics
          this.workDetail.read_count = Number(metrics.total_reads ?? this.workDetail.read_count ?? 0)
          this.workDetail.collect_count = Number(metrics.collect_count ?? this.workDetail.collect_count ?? 0)
          this.workDetail.subscription_count = Number(metrics.subscription_count ?? this.workDetail.subscription_count ?? 0)
          this.workDetail.subscription_income = Number(metrics.subscription_income ?? this.workDetail.subscription_income ?? 0)
          this.workDetail.vote_count = Number(metrics.vote_count ?? this.workDetail.vote_count ?? 0)
          this.workDetail.unique_readers = Number(metrics.unique_readers ?? this.workDetail.unique_readers ?? 0)
        }
      } catch (error) {
        console.warn('Load work metrics failed', error)
      }
    },
    
    async loadChapters() {
      try {
        const response = await getChapters(this.workId)
        if (response.data && response.data.success) {
          this.chapters = response.data.chapters || []
          if (response.data.work_title) {
            this.workDetail.title = this.workDetail.title || response.data.work_title
          }
          this.workDetail.chapter_count = this.chapters.length
        } else {
          this.$message.error(response.data?.error || '加载章节失败')
        }
      } catch (error) {
        console.error('Load chapters error:', error)
        this.$message.error('加载章节失败，请稍后重试')
      }
    },
    
    normalizeComments(rawComments = []) {
      return (rawComments || []).map(comment => ({
        ...comment,
        replies: this.normalizeComments(comment.replies || [])
      }))
    },

    async loadBookComments(reset = false) {
      if (!this.workId) return

      if (reset) {
        this.bookCommentPage = 1
        this.bookComments = []
        this.bookCommentHasMore = false
      }

      this.bookCommentsLoading = true
      try {
        const response = await getComments(this.workId, {
          type: 'book',
          page: this.bookCommentPage,
          page_size: this.bookCommentPageSize
        })

        if (response.data && response.data.success) {
          const fetched = this.normalizeComments(response.data.comments || [])
          if (this.bookCommentPage === 1) {
            this.bookComments = fetched
          } else {
            this.bookComments = [...this.bookComments, ...fetched]
          }

          const total = response.data.total || 0
          this.bookCommentHasMore = this.bookComments.length < total
          if (this.bookCommentHasMore) {
            this.bookCommentPage += 1
          }
        } else {
          this.$message.error(response.data?.error || '加载作品评论失败')
        }
      } catch (error) {
        console.error('Load book comments error:', error)
        this.$message.error('加载作品评论失败，请稍后重试')
      } finally {
        this.bookCommentsLoading = false
      }
    },

    async loadChapterComments(reset = false, chapterId = this.selectedChapterId) {
      if (!this.workId || !chapterId) {
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
          chapter_id: chapterId,
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
          this.$message.error(response.data?.error || '加载章节评论失败')
        }
      } catch (error) {
        console.error('Load chapter comments error:', error)
        this.$message.error('加载章节评论失败，请稍后重试')
      } finally {
        this.chapterCommentsLoading = false
      }
    },

    loadMoreBookComments() {
      if (this.bookCommentHasMore && !this.bookCommentsLoading) {
        this.loadBookComments(false)
      }
    },

    loadMoreChapterComments() {
      if (this.chapterCommentHasMore && !this.chapterCommentsLoading) {
        this.loadChapterComments(false, this.selectedChapterId)
      }
    },

    handleChapterSelect(chapterId) {
      if (!chapterId) {
        this.selectedChapterId = null
        this.chapterComments = []
        this.chapterCommentHasMore = false
        return
      }
      this.selectedChapterId = chapterId
      this.chapterCommentPage = 1
      this.chapterComments = []
      this.chapterCommentHasMore = false
      this.loadChapterComments(true, chapterId)
    },

    openCommentDialog(mode = 'book', options = {}) {
      if (mode === 'chapter') {
        const chapterId = options.chapter_id || this.selectedChapterId
        if (!chapterId) {
          this.$message.warning('请先选择章节')
          return
        }
        this.commentForm.chapter_id = chapterId
      } else {
        this.commentForm.chapter_id = null
      }

      this.commentForm.mode = mode
      this.commentForm.parent_id = options.parent_id || null
      this.commentForm.content = ''
      this.commentDialogTitle = options.title || (mode === 'chapter' ? '发表章节评论' : '发表作品评论')
      this.commentDialogVisible = true
      this.$nextTick(() => {
        if (this.$refs.commentFormRef) {
          this.$refs.commentFormRef.clearValidate()
        }
      })
    },

    openReplyDialog(comment, mode = 'book') {
      const title = `回复 ${comment.reader_name || '读者'}`
      const options = {
        parent_id: comment.comment_id,
        chapter_id: mode === 'chapter' ? (comment.chapter_id || this.selectedChapterId) : null,
        title
      }
      this.openCommentDialog(mode, options)
    },
    
    startReading() {
      if (this.chapters.length > 0) {
        const firstChapter = this.chapters[0]
        this.$router.push(`/main/reading/${this.workId}/${firstChapter.chapter_id}`)
      } else {
        this.$message.warning('暂时没有可阅读的章节')
      }
    },
    
    readChapter(chapterId) {
      if (!chapterId) return
      this.$router.push(`/main/reading/${this.workId}/${chapterId}`)
    },
    
    async openVoteDialog() {
      await this.loadUserTickets()
      this.showVoteDialog = true
    },

    async loadVoteRecords() {
      if (!this.workId) return
      try {
        const response = await getVoteRecords(this.workId, { page_size: 20 })
        if (response.data && response.data.success) {
          this.voteRecords = response.data.records || []
        } else {
          this.$message.error(response.data?.error || '加载投票记录失败')
        }
      } catch (error) {
        console.error('Load vote records error:', error)
        this.$message.error('加载投票记录失败，请稍后重试')
      }
    },

    async loadUserTickets() {
      try {
        const response = await getUserPoints()
        if (response.data && response.data.success) {
          this.userTicketCount = response.data.ticket_count || 0
        }
      } catch (error) {
        // 未登录或其他错误时不阻塞流程，仅记录日志
        console.error('Load user tickets error:', error)
      }
    },

    async toggleCollection() {
      if (!this.workId) return
      if (this.isCollected) {
        try {
          const response = await removeFromBookshelf(this.workId)
          if (response.data && response.data.success) {
            this.isCollected = false
            if (this.workDetail.collect_count > 0) {
              this.workDetail.collect_count -= 1
            }
            this.$message.success('已取消收藏')
            await this.loadWorkDetail()
          } else {
            this.$message.error(response.data?.error || '取消收藏失败')
          }
        } catch (error) {
          console.error('Remove from bookshelf error:', error)
          this.$message.error('取消收藏失败，请稍后重试')
        }
      } else {
        try {
          const response = await addToBookshelf(this.workId)
          if (response.data && response.data.success) {
            this.isCollected = true
            this.workDetail.collect_count = (this.workDetail.collect_count || 0) + 1
            this.$message.success('收藏成功')
            await this.loadWorkDetail()
          } else {
            this.$message.error(response.data?.error || '收藏失败')
          }
        } catch (error) {
          console.error('Add to bookshelf error:', error)
          this.$message.error('收藏失败，请稍后重试')
        }
      }
    },
    
    async handleVote() {
      try {
        await this.$refs.voteFormRef.validate()
      } catch (error) {
        return
      }

      if (this.voteForm.ticket_count > this.userTicketCount) {
        this.$message.error('月票数量不足')
        return
      }

      const usedTickets = this.voteForm.ticket_count || 0

      try {
        const response = await voteWork(this.workId, {
          ticket_count: usedTickets,
          message: this.voteForm.message
        })

        if (response.data && response.data.success) {
          this.$message.success(response.data.message || '投票成功')
          this.workDetail.vote_count = (this.workDetail.vote_count || 0) + (response.data.ticket_count || usedTickets)
          this.showVoteDialog = false
          this.resetVoteForm()
          if (response.data.remaining_tickets !== undefined) {
            this.userTicketCount = response.data.remaining_tickets
          } else {
            this.userTicketCount = Math.max(this.userTicketCount - usedTickets, 0)
          }
          await this.loadWorkDetail()
          await this.loadVoteRecords()
        } else {
          this.$message.error(response.data?.error || '投票失败')
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || '投票失败，请稍后重试'
        this.$message.error(errorMessage)
        console.error('Vote work error:', error)
      }
    },

    resetVoteForm() {
      if (this.$refs.voteFormRef) {
        this.$refs.voteFormRef.resetFields()
      }
      this.voteForm = {
        ticket_count: 1,
        message: ''
      }
    },
    
    filterChapters() {
      // 章节筛选逻辑已在computed中处理
    },
    
    async submitComment() {
      try {
        await this.$refs.commentFormRef.validate()
        
        const payload = {
          content: this.commentForm.content
        }

        if (this.commentForm.mode === 'chapter' && this.commentForm.chapter_id) {
          payload.chapter_id = this.commentForm.chapter_id
        }

        if (this.commentForm.parent_id) {
          payload.parent_id = this.commentForm.parent_id
        }

        const response = await addComment(this.workId, payload)

        if (response.data && response.data.success) {
          this.$message.success('评论发表成功')
          const isChapter = this.commentForm.mode === 'chapter'
          const chapterId = this.commentForm.chapter_id

          if (isChapter) {
            if (!this.commentForm.parent_id && chapterId) {
              const chapter = this.chapters.find(item => item.chapter_id === chapterId)
              if (chapter) {
                chapter.comment_count = (chapter.comment_count || 0) + 1
              }
            }
            await this.loadChapterComments(true, chapterId)
          } else {
            await this.loadBookComments(true)
          }

          this.commentDialogVisible = false
          this.commentForm = {
            content: '',
            mode: 'book',
            chapter_id: null,
            parent_id: null
          }
        } else {
          this.$message.error(response.data?.error || '评论发表失败')
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || '评论发表失败，请稍后重试'
        this.$message.error(errorMessage)
        console.error('Submit comment error:', error)
      }
    },

    async toggleCommentLike(comment) {
      try {
        const response = await likeComment(this.workId, comment.comment_id)
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
    
    goToWork(workId) {
      this.$router.push(`/main/work-detail/${workId}`)
    },
    
    getStatusType(status) {
      const types = {
        0: 'info',    // 草稿
        1: 'success', // 连载中
        2: 'warning', // 完结
        3: 'danger'   // 下架
      }
      return types[status] || 'info'
    },
    
    getStatusText(status) {
      const texts = {
        0: '草稿',
        1: '连载中',
        2: '完结',
        3: '下架'
      }
      return texts[status] || '未知'
    },
    
    formatNumber(num) {
      const value = Number(num) || 0
      if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万'
      }
      return value.toString()
    },

    formatDateTime(timeString) {
      if (!timeString) return ''
      const time = new Date(timeString)
      return time.toLocaleString()
    },
    
    formatTime(timeString) {
      if (!timeString) return ''
      const time = new Date(timeString)
      return time.toLocaleDateString()
    }
  }
}
</script>

<style scoped>
.work-detail-container {
  min-height: 100vh;
  background: #f8f9fa;
}

.work-header {
  background: white;
  padding: 30px;
  display: flex;
  gap: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.work-cover {
  flex-shrink: 0;
}

.work-cover img {
  width: 200px;
  height: 280px;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.work-info {
  flex: 1;
}

.work-title {
  color: #2c3e50;
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.work-meta {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  color: #7f8c8d;
}

.work-meta span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.work-stats {
  display: flex;
  gap: 30px;
  margin-bottom: 30px;
  padding: 20px 0;
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #7f8c8d;
  display: block;
}

.stat-sub {
  font-size: 0.75rem;
  color: #94a3b8;
  display: block;
  margin-top: 2px;
}

.work-actions {
  display: flex;
  gap: 15px;
}

.read-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 12px 30px;
  font-size: 1.1rem;
}

.work-content {
  margin: 30px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.work-tabs {
  padding: 0 30px;
}

.intro-content {
  padding: 30px 0;
}

.intro-text {
  color: #2c3e50;
  font-size: 1.1rem;
  line-height: 1.8;
  margin-bottom: 30px;
}

.work-tags h4 {
  color: #2c3e50;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-item {
  margin: 0;
}

.vote-cost-hint {
  margin-top: 8px;
  color: #7f8c8d;
  font-size: 0.85rem;
}

.chapters-content {
  padding: 30px 0;
}

.chapters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.chapters-header h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0;
}

.chapters-list {
  max-height: 500px;
  overflow-y: auto;
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
  gap: 15px;
}

.word-count, .publish-time {
  color: #7f8c8d;
  font-size: 0.8rem;
}

.comments-wrapper {
  display: flex;
  gap: 30px;
  padding: 30px 0;
}

.comments-column {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  min-height: 420px;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.comments-header h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0;
}

.comments-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.comment-item {
  display: flex;
  gap: 15px;
  padding: 20px 0;
  border-bottom: 1px solid #f0f0f0;
}

.comment-body {
  flex: 1;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.comment-author {
  color: #2c3e50;
  font-weight: 600;
}

.comment-time {
  color: #7f8c8d;
  font-size: 0.8rem;
}

.comment-text {
  color: #5a6c7d;
  line-height: 1.6;
  margin: 0 0 10px 0;
}

.comment-actions {
  display: flex;
  gap: 15px;
}

.reply-list {
  margin-top: 12px;
  padding-left: 50px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reply-item {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px 14px;
}

.votes-content {
  padding: 30px 0;
}

.votes-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.vote-item {
  padding: 15px 20px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafafa;
}

.vote-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.vote-reader {
  font-weight: 600;
  color: #2c3e50;
}

.vote-time {
  font-size: 0.85rem;
  color: #94a3b8;
}

.vote-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #5a6c7d;
}

.vote-message {
  font-size: 0.9rem;
  color: #667eea;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #94a3b8;
  font-size: 0.95rem;
}

.empty-comments {
  text-align: center;
  color: #94a3b8;
  padding: 40px 0;
  font-size: 0.95rem;
}

.load-more {
  text-align: center;
  margin-top: 10px;
}

.chapter-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chapter-select {
  min-width: 220px;
}

.author-content {
  padding: 30px 0;
}

.author-info {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.author-details h3 {
  color: #2c3e50;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.author-intro {
  color: #5a6c7d;
  line-height: 1.6;
  margin: 0 0 20px 0;
}

.author-stats {
  display: flex;
  gap: 30px;
}

.author-works h4 {
  color: #2c3e50;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
}

.work-card {
  text-align: center;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.work-card:hover {
  transform: translateY(-3px);
}

.work-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 10px;
}

.work-card h5 {
  color: #2c3e50;
  font-size: 0.9rem;
  font-weight: 500;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .work-header {
    flex-direction: column;
    padding: 20px;
  }
  
  .work-cover {
    align-self: center;
  }
  
  .work-cover img {
    width: 150px;
    height: 210px;
  }
  
  .work-title {
    font-size: 1.5rem;
  }
  
  .work-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .work-stats {
    flex-wrap: wrap;
    gap: 20px;
  }
  
  .work-actions {
    flex-wrap: wrap;
  }
  
  .work-content {
    margin: 20px;
  }
  
  .work-tabs {
    padding: 0 20px;
  }
  
  .chapter-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .chapter-meta {
    align-self: flex-end;
  }
  
  .author-info {
    flex-direction: column;
    text-align: center;
  }
  
  .author-stats {
    justify-content: center;
  }

  .comments-wrapper {
    flex-direction: column;
  }
}
</style>

