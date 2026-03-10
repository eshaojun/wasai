<template>
  <div class="settings">
    <div class="header">
      <h1>设置</h1>
    </div>

    <el-tabs type="border-card" class="settings-tabs">
      <!-- ASR 设置 -->
      <el-tab-pane label="语音识别 (ASR)">
        <el-form :model="settings" label-width="120px" class="settings-form">
          <el-form-item label="服务提供商">
            <el-radio-group v-model="settings.asr_provider">
              <el-radio label="openai">OpenAI Whisper</el-radio>
              <el-radio label="local" disabled>本地模型（开发中）</el-radio>
            </el-radio-group>
          </el-form-item>
          <template v-if="settings.asr_provider === 'openai'">
            <el-form-item label="API Key">
              <el-input
                v-model="settings.openai_api_key"
                type="password"
                show-password
                placeholder="sk-..."
              />
            </el-form-item>
            <el-form-item label="Base URL">
              <el-input
                v-model="settings.openai_base_url"
                placeholder="https://api.openai.com/v1"
              />
              <div class="form-tip">可选，用于第三方 API 代理</div>
            </el-form-item>
            <el-form-item label="模型">
              <el-select v-model="settings.whisper_model">
                <el-option label="Whisper" value="whisper-1" />
              </el-select>
            </el-form-item>
          </template>
        </el-form>
      </el-tab-pane>

      <!-- 翻译设置 -->
      <el-tab-pane label="翻译">
        <el-form :model="settings" label-width="120px" class="settings-form">
          <!-- 提供商选择 -->
          <el-form-item label="服务提供商">
            <el-radio-group v-model="settings.translate.provider">
              <el-radio label="custom">自定义接口</el-radio>
              <el-radio label="openai">OpenAI</el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- OpenAI 配置 -->
          <template v-if="settings.translate.provider === 'openai'">
            <el-form-item label="API Key">
              <el-input
                v-model="settings.translate.openai_api_key"
                type="password"
                show-password
                placeholder="sk-..."
              />
            </el-form-item>
            <el-form-item label="模型">
              <el-select v-model="settings.translate.openai_model">
                <el-option label="GPT-4o Mini" value="gpt-4o-mini" />
                <el-option label="GPT-4o" value="gpt-4o" />
                <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
              </el-select>
            </el-form-item>
          </template>

          <!-- 自定义接口配置 -->
          <template v-if="settings.translate.provider === 'custom'">
            <el-form-item label="Base URL">
              <el-input
                v-model="settings.translate.custom_base_url"
                placeholder="https://api.deepseek.com/v1"
              />
              <div class="form-tip">支持任意兼容 OpenAI API 的服务商</div>
            </el-form-item>
            <el-form-item label="API Key">
              <el-input
                v-model="settings.translate.custom_api_key"
                type="password"
                show-password
                placeholder="sk-..."
              />
            </el-form-item>
            <el-form-item label="模型">
              <el-input
                v-model="settings.translate.custom_model"
                placeholder="gpt-4o-mini"
              />
              <div class="form-tip">填写服务商支持的模型名称</div>
            </el-form-item>
          </template>

          <!-- 翻译提示词 -->
          <el-divider content-position="left">翻译提示词</el-divider>

          <el-form-item label="预设模板">
            <el-select v-model="selectedPromptTemplate" @change="onPromptTemplateChange">
              <el-option label="标准翻译" value="standard" />
              <el-option label="口语化翻译" value="colloquial" />
              <el-option label="保留原文风格" value="preserve_style" />
              <el-option label="自定义" value="custom" />
            </el-select>
          </el-form-item>

          <el-form-item label="提示词内容">
            <el-input
              v-model="settings.translate.translate_prompt"
              type="textarea"
              :rows="4"
              placeholder="输入翻译提示词..."
            />
          </el-form-item>

          <!-- 批量翻译设置 -->
          <el-divider content-position="left">批量翻译设置</el-divider>

          <el-form-item label="批量大小">
            <el-slider
              v-model="settings.translate.translate_batch_size"
              :min="10"
              :max="100"
              :step="10"
              show-stops
            />
            <div class="form-tip">每次翻译的字幕条数: {{ settings.translate.translate_batch_size }} 条</div>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- TTS 设置 -->
      <el-tab-pane label="语音合成 (TTS)">
        <el-form :model="settings" label-width="120px" class="settings-form">
          <el-form-item label="服务提供商">
            <el-radio-group v-model="settings.tts_provider">
              <el-radio label="openai">OpenAI TTS</el-radio>
              <el-radio label="azure" disabled>Azure Speech（开发中）</el-radio>
              <el-radio label="coqui" disabled>Coqui TTS（开发中）</el-radio>
            </el-radio-group>
          </el-form-item>
          <template v-if="settings.tts_provider === 'openai'">
            <el-form-item label="模型">
              <el-select v-model="settings.tts_model">
                <el-option label="TTS-1" value="tts-1" />
                <el-option label="TTS-1-HD" value="tts-1-hd" />
              </el-select>
            </el-form-item>
            <el-form-item label="默认声音">
              <el-select v-model="settings.tts_voice">
                <el-option label="Alloy（中性）" value="alloy" />
                <el-option label="Echo（男性）" value="echo" />
                <el-option label="Fable（男性）" value="fable" />
                <el-option label="Onyx（男性）" value="onyx" />
                <el-option label="Nova（女性）" value="nova" />
                <el-option label="Shimmer（女性）" value="shimmer" />
              </el-select>
            </el-form-item>
          </template>
        </el-form>
      </el-tab-pane>

      <!-- 默认设置 -->
      <el-tab-pane label="默认语言">
        <el-form :model="settings" label-width="120px" class="settings-form">
          <el-form-item label="默认源语言">
            <LanguageSelect v-model="settings.default_source_language" />
          </el-form-item>
          <el-form-item label="默认目标语言">
            <LanguageSelect
              v-model="settings.default_target_language"
              :exclude="[settings.default_source_language]"
            />
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <div class="actions">
      <el-button type="primary" size="large" @click="saveSettings" :loading="saving">
        保存设置
      </el-button>
      <el-button size="large" @click="resetSettings">重置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings, getTranslatePrompts } from '@/api'
import LanguageSelect from '@/components/LanguageSelect.vue'

const settings = ref({
  asr_provider: 'openai',
  openai_api_key: '',
  openai_base_url: '',
  whisper_model: 'whisper-1',
  translate: {
    provider: 'custom',
    custom_base_url: '',
    custom_api_key: '',
    custom_model: 'gpt-4o-mini',
    openai_api_key: '',
    openai_model: 'gpt-4o-mini',
    translate_prompt: '',
    translate_batch_size: 50
  },
  tts_provider: 'openai',
  azure_api_key: '',
  azure_region: '',
  tts_model: 'tts-1',
  tts_voice: 'alloy',
  default_source_language: 'zh',
  default_target_language: 'en'
})

const originalSettings = ref(null)
const saving = ref(false)
const translatePrompts = ref({})
const selectedPromptTemplate = ref('custom')

const loadSettings = async () => {
  try {
    const data = await getSettings()
    // 兼容旧版本设置
    if (data.translate) {
      settings.value.translate = {
        ...settings.value.translate,
        ...data.translate
      }
    } else {
      // 旧版本数据迁移
      settings.value.translate.provider = data.translate_provider || 'custom'
      settings.value.translate.custom_base_url = data.openai_base_url || ''
      settings.value.translate.custom_api_key = data.deepl_api_key || ''
      settings.value.translate.custom_model = data.translate_model || 'gpt-4o-mini'
      settings.value.translate.translate_batch_size = data.translate_batch_size || 50
    }
    // 其他设置
    settings.value.asr_provider = data.asr_provider || 'openai'
    settings.value.openai_api_key = data.openai_api_key || ''
    settings.value.openai_base_url = data.openai_base_url || ''
    settings.value.whisper_model = data.whisper_model || 'whisper-1'
    settings.value.tts_provider = data.tts_provider || 'openai'
    settings.value.tts_model = data.tts_model || 'tts-1'
    settings.value.tts_voice = data.tts_voice || 'alloy'
    settings.value.default_source_language = data.default_source_language || 'zh'
    settings.value.default_target_language = data.default_target_language || 'en'

    originalSettings.value = JSON.parse(JSON.stringify(settings.value))

    // 加载预设提示词
    try {
      translatePrompts.value = await getTranslatePrompts()
    } catch (e) {
      console.warn('加载预设提示词失败:', e)
    }
  } catch (error) {
    ElMessage.error('加载设置失败：' + error.message)
  }
}

const onPromptTemplateChange = (template) => {
  if (template !== 'custom' && translatePrompts.value[template]) {
    settings.value.translate.translate_prompt = translatePrompts.value[template]
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await updateSettings(settings.value)
    originalSettings.value = JSON.parse(JSON.stringify(settings.value))
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  } finally {
    saving.value = false
  }
}

const resetSettings = () => {
  if (originalSettings.value) {
    settings.value = JSON.parse(JSON.stringify(originalSettings.value))
  }
  ElMessage.info('设置已重置')
}

onMounted(loadSettings)
</script>

<style scoped>
.settings {
  max-width: 900px;
  margin: 0 auto;
}

.header {
  margin-bottom: 24px;
}

.header h1 {
  font-size: 24px;
  color: #303133;
}

.settings-tabs {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.settings-form {
  padding: 20px;
  max-width: 600px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}
</style>
