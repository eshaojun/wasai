<template>
  <div class="workflow-panel">
    <div class="workflow-steps">
      <div
        v-for="(step, index) in steps"
        :key="step.key"
        class="step-item"
        :class="{
          'completed': currentStep > index,
          'active': currentStep === index,
          'pending': currentStep < index
        }"
      >
        <div class="step-icon">
          <el-icon v-if="currentStep > index"><Check /></el-icon>
          <el-icon v-else-if="currentStep === index"><Loading /></el-icon>
          <span v-else>{{ index + 1 }}</span>
        </div>
        <div class="step-content">
          <div class="step-title">{{ step.title }}</div>
          <div class="step-desc">{{ step.description }}</div>
        </div>
        <div v-if="index < steps.length - 1" class="step-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <div class="workflow-actions">
      <el-button
        v-if="canExecute"
        type="primary"
        size="large"
        @click="executeCurrentStep"
        :loading="executing"
      >
        {{ currentStepAction }}
      </el-button>
      <el-button
        v-if="canExport"
        type="success"
        size="large"
        @click="exportVideo"
        :loading="exporting"
      >
        <el-icon><Download /></el-icon>导出视频
      </el-button>
    </div>

    <div v-if="progress > 0" class="progress-area">
      <el-progress :percentage="progress" :status="progressStatus" />
      <div class="progress-text">{{ progressText }}</div>
    </div>

    <!-- 导出完成后的下载链接 -->
    <div v-if="downloadUrl" class="download-area">
      <el-alert type="success" :closable="false" show-icon>
        <template #title>
          视频导出完成
          <el-link type="primary" :href="downloadUrl" :download="downloadFilename" class="download-link">
            点击下载
          </el-link>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { executeASR, executeTTS, exportVideo as exportVideoApi } from '@/api'

const props = defineProps({
  project: {
    type: Object,
    required: true
  },
  subtitles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['step-complete', 'export-complete', 'update:project'])

const steps = [
  { key: 'upload', title: '上传视频', description: '上传原始视频文件' },
  { key: 'asr', title: '语音识别', description: '自动识别视频中的语音' },
  { key: 'translate', title: '翻译字幕', description: '将字幕翻译成目标语言' },
  { key: 'tts', title: '生成配音', description: '使用AI合成配音音频' },
  { key: 'export', title: '导出视频', description: '合成最终视频' }
]

const currentStep = computed(() => {
  const statusMap = {
    'draft': 0,
    'uploaded': 1,
    'asr_done': 2,
    'translated': 3,
    'dubbed': 4,
    'exported': 5
  }
  return statusMap[props.project.status] || 0
})

const canExecute = computed(() => {
  return currentStep.value > 0 && currentStep.value < 4
})

const canExport = computed(() => {
  return currentStep.value >= 3
})

const currentStepAction = computed(() => {
  const actions = {
    1: '开始识别',
    2: '开始翻译',
    3: '生成配音'
  }
  return actions[currentStep.value] || '执行'
})

const executing = ref(false)
const exporting = ref(false)
const progress = ref(0)
const progressText = ref('')
const progressStatus = ref('')
const downloadUrl = ref(null)
const downloadFilename = ref('output.mp4')

const executeCurrentStep = async () => {
  executing.value = true
  progress.value = 0
  progressStatus.value = ''

  try {
    switch (currentStep.value) {
      case 1: // ASR
        await executeASRStep()
        break
      case 2: // Translate
        await executeTranslateStep()
        break
      case 3: // TTS
        await executeTTSStep()
        break
    }
  } catch (error) {
    ElMessage.error('执行失败：' + error.message)
    progressStatus.value = 'exception'
  } finally {
    executing.value = false
  }
}

const executeASRStep = async () => {
  progressText.value = '正在识别语音...'
  progress.value = 30

  const result = await executeASR(props.project.id, {
    language: props.project.source_language
  })

  progress.value = 100
  progressText.value = '语音识别完成'
  ElMessage.success('语音识别完成')
  emit('step-complete', 'asr_done', result.subtitles)
}

const executeTranslateStep = async () => {
  progressText.value = '正在翻译字幕...'
  progress.value = 50

  // 翻译逻辑在 SubtitleEditor 中处理
  progress.value = 100
  progressText.value = '翻译完成'
  emit('step-complete', 'translated')
}

const executeTTSStep = async () => {
  progressText.value = '正在生成配音...'
  progress.value = 30

  const result = await executeTTS(props.project.id, {
    language: props.project.target_language
  })

  progress.value = 100
  progressText.value = '配音生成完成'
  ElMessage.success('配音生成完成')
  emit('step-complete', 'dubbed', result)
}

const exportVideo = async () => {
  exporting.value = true
  progress.value = 0
  progressText.value = '正在合成视频...'

  try {
    const result = await exportVideoApi(props.project.id, {
      burn_subtitles: true
    })

    progress.value = 100
    progressText.value = '视频导出完成'
    ElMessage.success('视频导出成功')
    // 保存下载链接
    if (result.download_url) {
      downloadUrl.value = result.download_url
    }
    if (result.filename) {
      downloadFilename.value = result.filename
    }
    emit('export-complete', result)
  } catch (error) {
    ElMessage.error('导出失败：' + error.message)
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.workflow-panel {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.workflow-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  transition: all 0.3s;
}

.step-item.completed .step-icon {
  background: #67c23a;
  color: #fff;
}

.step-item.active .step-icon {
  background: #667eea;
  color: #fff;
  animation: pulse 2s infinite;
}

.step-item.pending .step-icon {
  background: #e4e7ed;
  color: #909399;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.step-content {
  flex: 1;
}

.step-title {
  font-weight: bold;
  color: #303133;
  font-size: 14px;
}

.step-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.step-arrow {
  color: #c0c4cc;
  margin: 0 8px;
}

.workflow-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.progress-area {
  margin-top: 20px;
  text-align: center;
}

.progress-text {
  margin-top: 8px;
  color: #606266;
  font-size: 14px;
}

.download-area {
  margin-top: 20px;
}

.download-link {
  margin-left: 8px;
}
</style>
