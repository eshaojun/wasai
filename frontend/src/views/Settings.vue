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
          <el-form-item label="服务提供商">
            <el-radio-group v-model="settings.translate_provider">
              <el-radio label="openai">OpenAI</el-radio>
              <el-radio label="deepl" disabled>DeepL（开发中）</el-radio>
            </el-radio-group>
          </el-form-item>
          <template v-if="settings.translate_provider === 'openai'">
            <el-form-item label="模型">
              <el-select v-model="settings.translate_model">
                <el-option label="GPT-4o Mini" value="gpt-4o-mini" />
                <el-option label="GPT-4o" value="gpt-4o" />
                <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
              </el-select>
            </el-form-item>
          </template>
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
import { getSettings, updateSettings } from '@/api'
import LanguageSelect from '@/components/LanguageSelect.vue'

const settings = ref({
  asr_provider: 'openai',
  openai_api_key: '',
  openai_base_url: '',
  whisper_model: 'whisper-1',
  translate_provider: 'openai',
  deepl_api_key: '',
  translate_model: 'gpt-4o-mini',
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

const loadSettings = async () => {
  try {
    const data = await getSettings()
    settings.value = { ...settings.value, ...data }
    originalSettings.value = JSON.parse(JSON.stringify(settings.value))
  } catch (error) {
    ElMessage.error('加载设置失败：' + error.message)
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
