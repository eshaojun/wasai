<template>
  <el-dialog
    v-model="dialogVisible"
    title="导入字幕"
    width="900px"
    :close-on-click-modal="false"
  >
    <!-- 上传区域 -->
    <div v-if="!previewData" class="upload-area">
      <el-upload
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :show-file-list="false"
        accept=".srt,.ass,.ssa,.txt"
      >
        <el-icon class="upload-icon"><Upload /></el-icon>
        <div class="upload-text">
          <span>拖拽字幕文件到此处</span>
          <span class="upload-hint">或点击选择文件</span>
        </div>
        <div class="upload-formats">支持格式：SRT、ASS</div>
      </el-upload>
    </div>

    <!-- 预览对比区域 -->
    <div v-else class="preview-area">
      <div class="preview-header">
        <div class="file-info">
          <el-icon><Document /></el-icon>
          <span>{{ previewData.filename }}</span>
          <el-tag size="small" type="success">{{ previewData.format.toUpperCase() }}</el-tag>
          <span class="subtitle-count">{{ previewData.subtitles.length }} 条字幕</span>
        </div>
        <div class="import-mode">
          <span>导入模式：</span>
          <el-radio-group v-model="importMode" size="small">
            <el-radio-button label="replace">替换现有字幕</el-radio-button>
            <el-radio-button label="append">追加到末尾</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- 对比表格 -->
      <el-table
        :data="comparisonData"
        height="400"
        border
        class="comparison-table"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column label="时间" width="180" align="center">
          <template #default="{ row }">
            <div class="time-cell">
              <div>{{ formatTime(row.start_time) }}</div>
              <div class="time-arrow">→</div>
              <div>{{ formatTime(row.end_time) }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="导入字幕" min-width="200">
          <template #default="{ row }">
            <el-input
              v-model="row.text"
              type="textarea"
              :rows="2"
              size="small"
              placeholder="字幕内容"
            />
          </template>
        </el-table-column>
        <el-table-column v-if="existingSubtitles.length > 0" label="现有字幕" min-width="200">
          <template #default="{ row }">
            <div class="existing-text" :class="{ 'is-new': row.isNew, 'is-modified': row.isModified }">
              {{ row.existingText || '（新字幕）' }}
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 统计信息 -->
      <div class="stats-bar" v-if="existingSubtitles.length > 0">
        <el-tag type="success">新增 {{ stats.new }} 条</el-tag>
        <el-tag type="warning">修改 {{ stats.modified }} 条</el-tag>
        <el-tag type="info">不变 {{ stats.unchanged }} 条</el-tag>
      </div>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">取消</el-button>
        <el-button v-if="previewData" @click="resetUpload">重新选择</el-button>
        <el-button
          v-if="previewData"
          type="primary"
          @click="confirmImport"
          :loading="importing"
        >
          确认导入 ({{ selectedCount }} 条)
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { previewImportSubtitles, importSubtitles } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  projectId: {
    type: Number,
    required: true
  },
  existingSubtitles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'imported'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const previewData = ref(null)
const comparisonData = ref([])
const importMode = ref('replace')
const importing = ref(false)
const selectedItems = ref([])

const selectedCount = computed(() => {
  return comparisonData.value.length
})

const stats = computed(() => {
  const newCount = comparisonData.value.filter(item => item.isNew).length
  const modifiedCount = comparisonData.value.filter(item => item.isModified).length
  const unchangedCount = comparisonData.value.filter(item => !item.isNew && !item.isModified).length
  return { new: newCount, modified: modifiedCount, unchanged: unchangedCount }
})

watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    // 对话框关闭时重置状态
    previewData.value = null
    comparisonData.value = []
  }
})

const handleFileChange = async (file) => {
  if (!file) return

  try {
    const result = await previewImportSubtitles(props.projectId, file.raw)
    previewData.value = result

    // 构建对比数据
    comparisonData.value = result.subtitles.map((sub, index) => {
      // 查找现有字幕中时间相近的
      const existing = props.existingSubtitles.find(es =>
        Math.abs(es.start_time - sub.start_time) < 0.5
      )

      const isNew = !existing
      const isModified = existing && existing.original_text !== sub.original_text

      return {
        ...sub,
        text: sub.original_text || sub.translated_text || '',
        existingText: existing ? (existing.original_text || existing.translated_text) : '',
        isNew,
        isModified,
        selected: true
      }
    })

    ElMessage.success(result.message)
  } catch (error) {
    ElMessage.error('预览失败：' + error.message)
  }
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`
}

const closeDialog = () => {
  dialogVisible.value = false
}

const resetUpload = () => {
  previewData.value = null
  comparisonData.value = []
}

const confirmImport = async () => {
  if (comparisonData.value.length === 0) {
    ElMessage.warning('没有要导入的字幕')
    return
  }

  importing.value = true
  try {
    const subtitlesToImport = comparisonData.value.map((item, index) => ({
      sequence: index,
      start_time: item.start_time,
      end_time: item.end_time,
      original_text: item.text,
      translated_text: ''
    }))

    await importSubtitles(props.projectId, subtitlesToImport, importMode.value)

    emit('imported', subtitlesToImport)
    closeDialog()
  } catch (error) {
    ElMessage.error('导入失败：' + error.message)
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.upload-area {
  padding: 40px;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  padding: 60px 20px;
}

.upload-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 16px;
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.upload-text span {
  font-size: 16px;
  color: #606266;
}

.upload-hint {
  font-size: 14px !important;
  color: #909399 !important;
}

.upload-formats {
  font-size: 12px;
  color: #909399;
}

.preview-area {
  padding: 20px 0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-info .el-icon {
  font-size: 20px;
  color: #667eea;
}

.subtitle-count {
  color: #909399;
  font-size: 14px;
}

.import-mode {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comparison-table {
  margin-top: 16px;
}

.time-cell {
  font-size: 12px;
  color: #606266;
}

.time-arrow {
  color: #c0c4cc;
  margin: 2px 0;
}

.existing-text {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  min-height: 40px;
}

.existing-text.is-new {
  background: #f0f9eb;
  color: #67c23a;
}

.existing-text.is-modified {
  background: #fdf6ec;
  color: #e6a23c;
}

.stats-bar {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
