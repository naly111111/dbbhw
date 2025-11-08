<template>
  <div class="settings-container">
    <div class="settings-header">
      <h2>设置</h2>
      <p>个性化您的阅读体验</p>
    </div>
    
    <div class="settings-content">
      <el-tabs v-model="activeTab" class="settings-tabs">
        <el-tab-pane label="界面设置" name="interface">
          <div class="settings-section">
            <h3>界面主题</h3>
            <div class="theme-options">
              <div 
                v-for="theme in themes" 
                :key="theme.value"
                class="theme-option"
                :class="{ active: currentTheme === theme.value }"
                @click="changeTheme(theme.value)"
              >
                <div class="theme-preview" :class="theme.value">
                  <div class="preview-header"></div>
                  <div class="preview-content"></div>
                </div>
                <span class="theme-name">{{ theme.label }}</span>
              </div>
            </div>
          </div>
          
          <div class="settings-section">
            <h3>字体设置</h3>
            <div class="font-settings">
              <div class="setting-item">
                <label>字体大小</label>
                <el-slider
                  v-model="fontSize"
                  :min="12"
                  :max="20"
                  :step="1"
                  @change="updateFontSize"
                  class="font-slider"
                />
                <span class="font-size-display">{{ fontSize }}px</span>
              </div>
              
              <div class="setting-item">
                <label>字体类型</label>
                <el-select v-model="fontFamily" @change="updateFontFamily">
                  <el-option label="系统默认" value="system"></el-option>
                  <el-option label="微软雅黑" value="Microsoft YaHei"></el-option>
                  <el-option label="宋体" value="SimSun"></el-option>
                  <el-option label="黑体" value="SimHei"></el-option>
                  <el-option label="楷体" value="KaiTi"></el-option>
                </el-select>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="阅读设置" name="reading">
          <div class="settings-section">
            <h3>阅读偏好</h3>
            <div class="reading-settings">
              <div class="setting-item">
                <label>自动翻页</label>
                <el-switch
                  v-model="autoScroll"
                  @change="updateAutoScroll"
                />
              </div>
              
              <div class="setting-item">
                <label>翻页速度</label>
                <el-slider
                  v-model="scrollSpeed"
                  :min="1"
                  :max="10"
                  :step="1"
                  @change="updateScrollSpeed"
                  :disabled="!autoScroll"
                />
                <span class="speed-display">{{ scrollSpeed }}秒/页</span>
              </div>
              
              <div class="setting-item">
                <label>阅读模式</label>
                <el-radio-group v-model="readingMode" @change="updateReadingMode">
                  <el-radio label="day">日间模式</el-radio>
                  <el-radio label="night">夜间模式</el-radio>
                  <el-radio label="auto">跟随系统</el-radio>
                </el-radio-group>
              </div>
              
              <div class="setting-item">
                <label>行间距</label>
                <el-slider
                  v-model="lineHeight"
                  :min="1.2"
                  :max="2.0"
                  :step="0.1"
                  @change="updateLineHeight"
                />
                <span class="height-display">{{ lineHeight }}倍</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="通知设置" name="notifications">
          <div class="settings-section">
            <h3>消息通知</h3>
            <div class="notification-settings">
              <div class="setting-item">
                <label>作品更新通知</label>
                <el-switch
                  v-model="notifications.workUpdate"
                  @change="updateNotifications"
                />
              </div>
              
              <div class="setting-item">
                <label>评论回复通知</label>
                <el-switch
                  v-model="notifications.commentReply"
                  @change="updateNotifications"
                />
              </div>
              
              <div class="setting-item">
                <label>系统消息通知</label>
                <el-switch
                  v-model="notifications.systemMessage"
                  @change="updateNotifications"
                />
              </div>
              
              <div class="setting-item">
                <label>推荐作品通知</label>
                <el-switch
                  v-model="notifications.recommendation"
                  @change="updateNotifications"
                />
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="隐私设置" name="privacy">
          <div class="settings-section">
            <h3>隐私保护</h3>
            <div class="privacy-settings">
              <div class="setting-item">
                <label>阅读记录隐私</label>
                <el-radio-group v-model="privacy.readingRecord" @change="updatePrivacy">
                  <el-radio label="public">公开</el-radio>
                  <el-radio label="friends">仅好友可见</el-radio>
                  <el-radio label="private">仅自己可见</el-radio>
                </el-radio-group>
              </div>
              
              <div class="setting-item">
                <label>收藏作品隐私</label>
                <el-radio-group v-model="privacy.collections" @change="updatePrivacy">
                  <el-radio label="public">公开</el-radio>
                  <el-radio label="friends">仅好友可见</el-radio>
                  <el-radio label="private">仅自己可见</el-radio>
                </el-radio-group>
              </div>
              
              <div class="setting-item">
                <label>个人资料可见性</label>
                <el-radio-group v-model="privacy.profile" @change="updatePrivacy">
                  <el-radio label="public">公开</el-radio>
                  <el-radio label="friends">仅好友可见</el-radio>
                  <el-radio label="private">仅自己可见</el-radio>
                </el-radio-group>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <div class="settings-actions">
        <el-button @click="resetSettings">恢复默认</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Settings',
  data() {
    return {
      activeTab: 'interface',
      currentTheme: 'light',
      themes: [
        { label: '浅色主题', value: 'light' },
        { label: '深色主题', value: 'dark' },
        { label: '护眼主题', value: 'green' },
        { label: '经典主题', value: 'classic' }
      ],
      fontSize: 14,
      fontFamily: 'system',
      autoScroll: false,
      scrollSpeed: 3,
      readingMode: 'auto',
      lineHeight: 1.5,
      notifications: {
        workUpdate: true,
        commentReply: true,
        systemMessage: true,
        recommendation: false
      },
      privacy: {
        readingRecord: 'friends',
        collections: 'public',
        profile: 'public'
      }
    }
  },
  created() {
    this.loadSettings()
  },
  methods: {
    loadSettings() {
      // 从本地存储加载设置
      const savedSettings = localStorage.getItem('userSettings')
      if (savedSettings) {
        const settings = JSON.parse(savedSettings)
        Object.assign(this, settings)
      }
    },
    
    saveSettings() {
      // 保存设置到本地存储
      const settings = {
        currentTheme: this.currentTheme,
        fontSize: this.fontSize,
        fontFamily: this.fontFamily,
        autoScroll: this.autoScroll,
        scrollSpeed: this.scrollSpeed,
        readingMode: this.readingMode,
        lineHeight: this.lineHeight,
        notifications: this.notifications,
        privacy: this.privacy
      }
      
      localStorage.setItem('userSettings', JSON.stringify(settings))
      this.$message.success('设置已保存')
    },
    
    resetSettings() {
      this.$confirm('确定要恢复默认设置吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.currentTheme = 'light'
        this.fontSize = 14
        this.fontFamily = 'system'
        this.autoScroll = false
        this.scrollSpeed = 3
        this.readingMode = 'auto'
        this.lineHeight = 1.5
        this.notifications = {
          workUpdate: true,
          commentReply: true,
          systemMessage: true,
          recommendation: false
        }
        this.privacy = {
          readingRecord: 'friends',
          collections: 'public',
          profile: 'public'
        }
        this.saveSettings()
      })
    },
    
    changeTheme(theme) {
      this.currentTheme = theme
      this.applyTheme(theme)
    },
    
    applyTheme(theme) {
      document.body.className = `theme-${theme}`
    },
    
    updateFontSize(size) {
      document.documentElement.style.setProperty('--font-size', `${size}px`)
    },
    
    updateFontFamily(family) {
      if (family === 'system') {
        document.documentElement.style.setProperty('--font-family', 'system-ui, -apple-system, sans-serif')
      } else {
        document.documentElement.style.setProperty('--font-family', family)
      }
    },
    
    updateAutoScroll(enabled) {
      // 更新自动翻页设置
    },
    
    updateScrollSpeed(speed) {
      // 更新翻页速度设置
    },
    
    updateReadingMode(mode) {
      // 更新阅读模式设置
    },
    
    updateLineHeight(height) {
      document.documentElement.style.setProperty('--line-height', height)
    },
    
    updateNotifications() {
      // 更新通知设置
    },
    
    updatePrivacy() {
      // 更新隐私设置
    }
  }
}
</script>

<style scoped>
.settings-container {
  height: 100%;
}

.settings-header {
  text-align: center;
  margin-bottom: 30px;
}

.settings-header h2 {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.settings-header p {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.settings-content {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  height: calc(100% - 120px);
  overflow-y: auto;
}

.settings-tabs {
  height: 100%;
}

.settings-section {
  margin-bottom: 40px;
}

.settings-section h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0 0 20px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #e0e0e0;
}

.theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.theme-option {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.theme-option:hover {
  transform: translateY(-3px);
}

.theme-option.active {
  transform: translateY(-3px);
}

.theme-preview {
  width: 100%;
  height: 80px;
  border-radius: 8px;
  margin-bottom: 10px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.3s ease;
}

.theme-option.active .theme-preview {
  border-color: #667eea;
}

.theme-preview.light {
  background: #ffffff;
}

.theme-preview.dark {
  background: #2c3e50;
}

.theme-preview.green {
  background: #f0f8f0;
}

.theme-preview.classic {
  background: #f5f5dc;
}

.preview-header {
  height: 20px;
  background: #667eea;
}

.preview-content {
  height: 60px;
  background: currentColor;
  opacity: 0.1;
}

.theme-name {
  color: #2c3e50;
  font-size: 0.9rem;
  font-weight: 500;
}

.font-settings,
.reading-settings,
.notification-settings,
.privacy-settings {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 20px;
}

.setting-item label {
  min-width: 120px;
  color: #2c3e50;
  font-weight: 500;
}

.font-slider {
  flex: 1;
  max-width: 200px;
}

.font-size-display,
.speed-display,
.height-display {
  min-width: 60px;
  color: #7f8c8d;
  font-size: 0.9rem;
  text-align: right;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

@media (max-width: 768px) {
  .settings-content {
    padding: 20px;
  }
  
  .theme-options {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 15px;
  }
  
  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .setting-item label {
    min-width: auto;
  }
  
  .font-slider {
    max-width: 100%;
  }
  
  .settings-actions {
    flex-direction: column;
  }
}
</style>

<style>
/* 主题样式 */
.theme-light {
  --bg-color: #ffffff;
  --text-color: #2c3e50;
  --border-color: #e0e0e0;
}

.theme-dark {
  --bg-color: #2c3e50;
  --text-color: #ffffff;
  --border-color: #34495e;
}

.theme-green {
  --bg-color: #f0f8f0;
  --text-color: #2c3e50;
  --border-color: #c8e6c9;
}

.theme-classic {
  --bg-color: #f5f5dc;
  --text-color: #2c3e50;
  --border-color: #d4c4a8;
}
</style>

