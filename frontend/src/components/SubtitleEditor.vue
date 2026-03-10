<template>
  <div class="subtitle-editor">
    <div class="toolbar">
      <el-button type="primary" @click="addSubtitle">
        <el-icon><Plus /></el-icon>添加字幕
      </el-button>
      <el-button @click="autoTranslate" :loading="translating">
        <el-icon><Refresh /></el-icon>自动翻译
      </el-button>
      <el-button @click="saveSubtitles" type="success">
        <el-icon><Check /></el-icon>保存修改
      </el-button>
      <el-divider direction="vertical" />
      <el-button @click="showImportDialog">
        <el-icon><Upload /></el-icon>导入字幕
      </el-button>
      <el-dropdown @command="handleExport" trigger="click">
        <el-button>
          <el-icon><Download /></el-icon>导出字幕
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="srt">导出为 SRT</el-dropdown-item>
            <el-dropdown-item command="ass">导出为 ASS</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 导入对话框 -->
    <SubtitleImportDialog
      v-model="importDialogVisible"
      :project-id="projectId"
      :existing-subtitles="subtitles"
      @imported="onSubtitlesImported"
    />

    <div class="subtitle-list">
      <div
        v-for="(subtitle, index) in subtitles"
        :key="subtitle.id || index"
        class="subtitle-item"
        :class="{ active: selectedIndex === index }"
        @click="selectSubtitle(index)"
      >
        <div class="subtitle-header">
          <span class="subtitle-number">#{{ index + 1 }}</span>
          <div class="subtitle-time">
            <el-input-number
              v-model="subtitle.start_time"
              :precision="2"
              :step="0.1"
              size="small"
              controls-position="right"
              class="time-input"
            />
            <span class="time-separator">-</span>
            <el-input-number
              v-model="subtitle.end_time"
              :precision="2"
              :step="0.1"
              size="small"
              controls-position="right"
              class="time-input"
            />
          </div>
          <el-button
            type="info"
            size="small"
            circle
            @click.stop="seekVideoToSubtitle(index)"
            title="跳转到视频"
          >
            <el-icon><VideoPlay /></el-icon>
          </el-button>
          <el-button
            type="danger"
            size="small"
            circle
            @click.stop="deleteSubtitle(index)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <div class="subtitle-content">
          <div class="original-text">
            <label>原文</label>
            <el-input
              v-model="subtitle.original_text"
              type="textarea"
              :rows="2"
              placeholder="原文"
            />
          </div>
          <div class="translated-text">
            <label>译文</label>
            <el-input
              v-model="subtitle.translated_text"
              type="textarea"
              :rows="2"
              placeholder="译文（可编辑）"
            />
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="subtitles.length === 0" description="暂无字幕数据" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import { translateSubtitles, exportSubtitles } from '@/api'
import SubtitleImportDialog from './SubtitleImportDialog.vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  projectId: {
    type: Number,
    required: true
  },
  sourceLanguage: {
    type: String,
    default: 'zh'
  },
  targetLanguage: {
    type: String,
    default: 'en'
  }
})

const emit = defineEmits(['update:modelValue', 'save', 'refresh', 'seek-video'])

const subtitles = ref([])
const selectedIndex = ref(-1)
const translating = ref(false)
const importDialogVisible = ref(false)

// 滚动到指定字幕
const scrollToSubtitle = (index) => {
  const subtitleItems = document.querySelectorAll('.subtitle-item')
  if (subtitleItems[index]) {
    subtitleItems[index].scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

// 选择字幕（供外部调用）
const selectSubtitle = (index) => {
  selectedIndex.value = index
}

// 跳转到视频时间点
const seekVideoToSubtitle = (index) => {
  emit('seek-video', index)
}

watch(() => props.modelValue, (newVal) => {
  subtitles.value = JSON.parse(JSON.stringify(newVal))
}, { immediate: true, deep: true })

const addSubtitle = () => {
  const lastSubtitle = subtitles.value[subtitles.value.length - 1]
  const startTime = lastSubtitle ? lastSubtitle.end_time : 0

  subtitles.value.push({
    id: null,
    project_id: props.projectId,
    start_time: startTime,
    end_time: startTime + 3,
    original_text: '',
    translated_text: '',
    sequence: subtitles.value.length
  })
}

const deleteSubtitle = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除这条字幕吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    subtitles.value.splice(index, 1)
    // 更新序号
    subtitles.value.forEach((sub, i) => {
      sub.sequence = i
    })
  } catch {
    // 取消删除
  }
}

const autoTranslate = async () => {
  if (subtitles.value.length === 0) {
    ElMessage.warning('没有需要翻译的字幕')
    return
  }

  translating.value = true
  try {
    const texts = subtitles.value.map(sub => sub.original_text)
    const result = await translateSubtitles(props.projectId, {
      texts,
      source_language: props.sourceLanguage,
      target_language: props.targetLanguage
    })

    // 更新译文
    if (result.translated_texts) {
      subtitles.value.forEach((sub, i) => {
        if (result.translated_texts[i]) {
          sub.translated_text = result.translated_texts[i]
        }
      })
    }

    ElMessage.success('翻译完成')
  } catch (error) {
    ElMessage.error('翻译失败：' + error.message)
  } finally {
    translating.value = false
  }
}

const saveSubtitles = () => {
  emit('update:modelValue', subtitles.value)
  emit('save', subtitles.value)
}

const showImportDialog = () => {
  importDialogVisible.value = true
}

const onSubtitlesImported = (importedSubtitles) => {
  // 替换当前字幕
  subtitles.value = importedSubtitles
  emit('update:modelValue', subtitles.value)
  emit('save', subtitles.value)
  emit('refresh')
  ElMessage.success('字幕导入成功')
}

const handleExport = async (format) => {
  try {
    const response = await exportSubtitles(props.projectId, format)

    // 创建下载链接
    const blob = new Blob([response], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `subtitles.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success(`字幕已导出为 ${format.toUpperCase()} 格式`)
  } catch (error) {
    ElMessage.error('导出失败：' + error.message)
  }
}

// 暴露方法供父组件调用
defineExpose({
  selectSubtitle,
  scrollToSubtitle
})
</script>

<style scoped>
.subtitle-editor {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.subtitle-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 600px;
  overflow-y: auto;
}

.subtitle-item {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
  border: 2px solid transparent;
  transition: all 0.3s;
  cursor: pointer;
}

.subtitle-item:hover {
  background: #e8f4ff;
}

.subtitle-item.active {
  border-color: #667eea;
  background: #f0f2ff;
}

.subtitle-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.subtitle-number {
  font-weight: bold;
  color: #667eea;
  min-width: 40px;
}

.subtitle-time {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.time-input {
  width: 100px;
}

.time-separator {
  color: #909399;
}

.subtitle-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.original-text label,
.translated-text label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

:deep(.el-textarea__inner) {
  resize: none;
}
</style>
