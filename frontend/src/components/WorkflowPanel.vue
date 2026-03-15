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
        v-if="currentStep === 3"
        type="info"
        size="large"
        plain
        @click="showTTSSettings = true"
      >
        <el-icon><Setting /></el-icon>配音设置
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
    
    <!-- TTS 设置弹窗 -->
    <el-dialog
      v-model="showTTSSettings"
      title="配音设置"
      width="500px"
    >
      <el-form :model="ttsSettings" label-width="100px">
        <el-form-item label="TTS 提供商">
          <el-radio-group v-model="ttsSettings.provider">
            <el-radio label="openai">OpenAI TTS</el-radio>
            <el-radio label="local">本地模型 (Qwen3-TTS)</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- OpenAI TTS 设置 -->
        <template v-if="ttsSettings.provider === 'openai'">
          <el-form-item label="声音">
            <el-select v-model="ttsSettings.voice" style="width: 100%">
              <el-option label="Alloy（中性）" value="alloy" />
              <el-option label="Echo（男性）" value="echo" />
              <el-option label="Fable（男性）" value="fable" />
              <el-option label="Onyx（男性）" value="onyx" />
              <el-option label="Nova（女性）" value="nova" />
              <el-option label="Shimmer（女性）" value="shimmer" />
            </el-select>
          </el-form-item>
        </template>
        
        <!-- 本地 TTS 设置 -->
        <template v-if="ttsSettings.provider === 'local'">
          <el-form-item label="说话人">
            <el-select v-model="ttsSettings.speaker" style="width: 100%">
              <el-option-group label="中文">
                <el-option label="Vivian - 明亮、略带尖锐的年轻女声" value="vivian" />
                <el-option label="Serena - 温暖、温柔的年轻女声" value="serena" />
                <el-option label="Dylan - 年轻北京男声" value="dylan" />
                <el-option label="Eric - 活泼成都男声" value="eric" />
                <el-option label="Uncle Fu - 低沉醇厚的男声" value="uncle_fu" />
              </el-option-group>
              <el-option-group label="英文">
                <el-option label="Ryan - 富有节奏感的动感男声" value="ryan" />
                <el-option label="Aiden - 阳光美式男声" value="aiden" />
              </el-option-group>
              <el-option-group label="其他语言">
                <el-option label="Ono Anna - 俏皮日本女声（日语）" value="ono_anna" />
                <el-option label="Sohee - 温暖韩语女声（韩语）" value="sohee" />
              </el-option-group>
            </el-select>
          </el-form-item>
          <el-form-item label="语言">
            <el-select v-model="ttsSettings.language" style="width: 100%">
              <el-option label="自动检测" value="auto" />
              <el-option label="中文" value="zh" />
              <el-option label="英文" value="en" />
              <el-option label="日语" value="ja" />
              <el-option label="韩语" value="ko" />
              <el-option label="法语" value="fr" />
              <el-option label="德语" value="de" />
              <el-option label="意大利语" value="it" />
              <el-option label="葡萄牙语" value="pt" />
              <el-option label="俄语" value="ru" />
              <el-option label="西班牙语" value="es" />
            </el-select>
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="showTTSSettings = false">取消</el-button>
        <el-button type="primary" @click="saveTTSSettings" :loading="savingSettings">
          保存到设置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Loading, ArrowRight, Download, Setting } from '@element-plus/icons-vue'
import { executeASR, executeTTS, exportVideo as exportVideoApi, getSettings, updateSettings } from '@/api'

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

// TTS 设置弹窗
const showTTSSettings = ref(false)
const savingSettings = ref(false)
const ttsSettings = ref({
  provider: 'openai',
  voice: 'alloy',
  speaker: 'vivian',
  language: 'auto'
})

// 加载设置
const loadSettings = async () => {
  try {
    const settings = await getSettings()
    ttsSettings.value.provider = settings.tts_provider || 'openai'
    ttsSettings.value.voice = settings.tts_voice || 'alloy'
    ttsSettings.value.speaker = settings.local_tts_speaker || 'vivian'
    ttsSettings.value.language = settings.local_tts_language || 'auto'
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

// 保存TTS设置
const saveTTSSettings = async () => {
  savingSettings.value = true
  try {
    const settings = await getSettings()
    const updatedSettings = {
      ...settings,
      tts_provider: ttsSettings.value.provider,
      tts_voice: ttsSettings.value.voice,
      local_tts_speaker: ttsSettings.value.speaker,
      local_tts_language: ttsSettings.value.language
    }
    await updateSettings(updatedSettings)
    ElMessage.success('设置已保存')
    showTTSSettings.value = false
  } catch (error) {
    ElMessage.error('保存设置失败：' + error.message)
  } finally {
    savingSettings.value = false
  }
}

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

  // 使用当前TTS设置
  const ttsParams = {
    language: props.project.target_language
  }
  
  // 如果是本地TTS，传递说话人和语言参数
  if (ttsSettings.value.provider === 'local') {
    ttsParams.speaker = ttsSettings.value.speaker
    ttsParams.tts_language = ttsSettings.value.language
  }

  const result = await executeTTS(props.project.id, ttsParams)

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
    emit('export-complete', result)
  } catch (error) {
    ElMessage.error('导出失败：' + error.message)
  } finally {
    exporting.value = false
  }
}

onMounted(loadSettings)
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
</style>
