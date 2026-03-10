<template>
  <div class="project-detail">
    <div class="header">
      <div class="header-left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <h1>{{ project.name }}</h1>
      </div>
      <div class="header-actions">
        <el-button
          v-if="downloadUrl"
          type="success"
          @click="downloadVideo"
        >
          <el-icon><Download /></el-icon>下载视频
        </el-button>
        <el-button type="primary" @click="saveProject">保存</el-button>
      </div>
    </div>

    <div class="content">
      <div class="left-panel">
        <!-- 视频播放器 -->
        <div class="video-section">
          <VideoUploader
            v-if="!hasVideo"
            :project-id="projectId"
            @success="onUploadSuccess"
          />
          <VideoPlayer
            v-else
            ref="videoPlayerRef"
            :video-url="videoUrl"
            :video-info="videoInfo"
            :subtitles="subtitles"
            @subtitle-change="onSubtitleChange"
            @time-update="onTimeUpdate"
          />
        </div>

        <!-- 工作流面板 -->
        <WorkflowPanel
          :project="project"
          :subtitles="subtitles"
          @step-complete="onStepComplete"
          @export-complete="onExportComplete"
        />
      </div>

      <div class="right-panel">
        <!-- 项目信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>项目信息</span>
            </div>
          </template>
          <el-form :model="project" label-width="80px" size="small">
            <el-form-item label="名称">
              <el-input v-model="project.name" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="project.description" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="源语言">
              <LanguageSelect v-model="project.source_language" size="small" />
            </el-form-item>
            <el-form-item label="目标语言">
              <LanguageSelect
                v-model="project.target_language"
                size="small"
                :exclude="[project.source_language]"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 字幕编辑器 -->
        <el-card class="subtitle-card">
          <template #header>
            <div class="card-header">
              <span>字幕编辑</span>
              <span class="subtitle-count">{{ subtitles.length }} 条字幕</span>
            </div>
          </template>
          <SubtitleEditor
            ref="subtitleEditorRef"
            v-model="subtitles"
            :project-id="projectId"
            :source-language="project.source_language"
            :target-language="project.target_language"
            @save="saveSubtitles"
            @seek-video="seekToSubtitle"
          />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getProject,
  updateProject,
  getSubtitles,
  batchUpdateSubtitles,
  getProjectVideo
} from '@/api'
import VideoUploader from '@/components/VideoUploader.vue'
import VideoPlayer from '@/components/VideoPlayer.vue'
import SubtitleEditor from '@/components/SubtitleEditor.vue'
import WorkflowPanel from '@/components/WorkflowPanel.vue'
import LanguageSelect from '@/components/LanguageSelect.vue'

const route = useRoute()
const router = useRouter()
const projectId = parseInt(route.params.id)

const project = ref({
  name: '',
  description: '',
  source_language: 'zh',
  target_language: 'en',
  status: 'draft',
  original_video_path: null,
  width: 0,
  height: 0,
  fps: 0,
  duration: 0
})

const subtitles = ref([])
const videoPlayerRef = ref(null)
const subtitleEditorRef = ref(null)
const currentTime = ref(0)
const downloadUrl = ref(null)
const downloadFilename = ref('output.mp4')
const hasVideo = ref(false)
const videoUrl = ref('')

// 视频信息
const videoInfo = computed(() => ({
  width: project.value.width || 0,
  height: project.value.height || 0,
  fps: project.value.fps || 0,
  duration: project.value.duration || 0
}))

const loadProject = async () => {
  try {
    const data = await getProject(projectId)
    project.value = data
    subtitles.value = data.subtitles || []

    // 加载视频信息
    await loadVideoInfo()
  } catch (error) {
    ElMessage.error('加载项目失败：' + error.message)
  }
}

const loadVideoInfo = async () => {
  try {
    const videoData = await getProjectVideo(projectId)
    const newHasVideo = videoData.has_video && videoData.video_url

    // 只有当状态真正改变时才更新
    if (newHasVideo !== hasVideo.value) {
      hasVideo.value = newHasVideo
      console.log('hasVideo状态改变:', hasVideo.value)
    }

    if (videoData.has_video && videoData.video_url) {
      videoUrl.value = videoData.video_url
      project.value.width = videoData.width
      project.value.height = videoData.height
      project.value.fps = videoData.fps
      project.value.duration = videoData.duration
      console.log('视频信息已更新:', {
        videoUrl: videoUrl.value,
        width: project.value.width,
        height: project.value.height,
        fps: project.value.fps,
        duration: project.value.duration
      })
    }
  } catch (error) {
    console.error('加载视频信息失败:', error)
  }
}

const saveProject = async () => {
  try {
    await updateProject(projectId, {
      name: project.value.name,
      description: project.value.description,
      source_language: project.value.source_language,
      target_language: project.value.target_language
    })
    ElMessage.success('项目已保存')
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  }
}

const saveSubtitles = async (subtitleList) => {
  try {
    await batchUpdateSubtitles(projectId, subtitleList)
    ElMessage.success('字幕已保存')
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  }
}

const onUploadSuccess = async () => {
  ElMessage.success('视频上传成功')
  await loadVideoInfo()
}

const onStepComplete = (status, data) => {
  project.value.status = status
  if (data && data.subtitles) {
    subtitles.value = data.subtitles
  }
}

const onExportComplete = (data) => {
  project.value.status = 'exported'
  if (data.output_path) {
    project.value.output_video_path = data.output_path
  }
  if (data.download_url) {
    downloadUrl.value = data.download_url
  }
  if (data.filename) {
    downloadFilename.value = data.filename
  }
}

const downloadVideo = () => {
  if (!downloadUrl.value) return
  // 创建临时链接下载
  const link = document.createElement('a')
  link.href = downloadUrl.value
  link.download = downloadFilename.value
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 字幕联动
const onSubtitleChange = (index) => {
  if (subtitleEditorRef.value) {
    subtitleEditorRef.value.selectSubtitle(index)
    subtitleEditorRef.value.scrollToSubtitle(index)
  }
}

const onTimeUpdate = (time) => {
  // console.log('ProjectDetail onTimeUpdate:', time) // 减少日志噪音
  currentTime.value = time
}

const seekToSubtitle = (index) => {
  if (videoPlayerRef.value) {
    videoPlayerRef.value.seekToSubtitle(index)
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(loadProject)
</script>

<style scoped>
.project-detail {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header h1 {
  font-size: 20px;
  color: #303133;
  margin: 0;
}

.content {
  display: grid;
  grid-template-columns: 1fr 450px;
  gap: 20px;
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-section {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card,
.subtitle-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.subtitle-count {
  font-size: 12px;
  color: #909399;
}

@media (max-width: 1200px) {
  .content {
    grid-template-columns: 1fr;
  }
}
</style>
