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
        <el-form :model="settings" label-width="140px" class="settings-form">
          <el-form-item label="服务提供商">
            <el-radio-group v-model="settings.tts_provider">
              <el-radio label="openai">OpenAI TTS</el-radio>
              <el-radio label="azure" disabled>Azure Speech（开发中）</el-radio>
              <el-radio label="coqui" disabled>Coqui TTS（开发中）</el-radio>
              <el-radio label="local">本地模型 (Qwen3-TTS)</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <!-- OpenAI TTS 设置 -->
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
          
          <!-- 本地 TTS (Qwen3-TTS) 设置 -->
          <template v-if="settings.tts_provider === 'local'">
            <el-form-item label="服务地址">
              <el-input
                v-model="settings.local_tts_base_url"
                placeholder="http://localhost:8003"
              />
              <div class="form-tip">本地 Qwen3-TTS 服务地址</div>
            </el-form-item>
            
            <el-form-item label="说话人">
              <el-select v-model="settings.local_tts_speaker" style="width: 100%">
                <el-option-group label="中文">
                  <el-option label="Vivian - 明亮、略带尖锐的年轻女声" value="vivian" />
                  <el-option label="Serena - 温暖、温柔的年轻女声" value="serena" />
                  <el-option label="Dylan - 年轻北京男声，音色清晰自然" value="dylan" />
                  <el-option label="Eric - 活泼成都男声，略带沙哑的明亮感" value="eric" />
                  <el-option label="Uncle Fu - 经验丰富、低沉醇厚的男声" value="uncle_fu" />
                </el-option-group>
                <el-option-group label="英文">
                  <el-option label="Ryan - 富有节奏感的动感男声" value="ryan" />
                  <el-option label="Aiden - 阳光美式男声，中音清晰" value="aiden" />
                </el-option-group>
                <el-option-group label="其他语言">
                  <el-option label="Ono Anna - 俏皮日本女声，音色轻快灵动（日语）" value="ono_anna" />
                  <el-option label="Sohee - 温暖韩语女声，情感丰富（韩语）" value="sohee" />
                </el-option-group>
              </el-select>
              <div class="form-tip">选择配音使用的说话人角色</div>
            </el-form-item>
            
            <el-form-item label="语言">
              <el-select v-model="settings.local_tts_language" style="width: 100%">
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
              <div class="form-tip">合成语音的语言，建议选择"自动检测"让模型自动识别</div>
            </el-form-item>
            
            <el-form-item>
              <div class="button-group">
                <el-button type="info" plain @click="testLocalTTS" :loading="testing">
                  <el-icon><Connection /></el-icon> 测试连接
                </el-button>
                <el-button type="primary" @click="showTestDialog = true">
                  <el-icon><Microphone /></el-icon> 测试生成
                </el-button>
              </div>
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
    
    <!-- TTS 测试生成弹窗 -->
    <el-dialog
      v-model="showTestDialog"
      title="测试语音合成"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="testForm" label-width="100px">
        <el-form-item label="测试文本">
          <el-input
            v-model="testForm.text"
            type="textarea"
            :rows="3"
            placeholder="请输入要合成的文本，例如：你好，这是Qwen3-TTS的测试语音。"
          />
        </el-form-item>
        
        <el-form-item label="说话人">
          <el-select v-model="testForm.speaker" style="width: 100%">
            <el-option-group label="中文">
              <el-option label="Vivian - 明亮、略带尖锐的年轻女声" value="vivian" />
              <el-option label="Serena - 温暖、温柔的年轻女声" value="serena" />
              <el-option label="Dylan - 年轻北京男声，音色清晰自然" value="dylan" />
              <el-option label="Eric - 活泼成都男声，略带沙哑的明亮感" value="eric" />
              <el-option label="Uncle Fu - 经验丰富、低沉醇厚的男声" value="uncle_fu" />
            </el-option-group>
            <el-option-group label="英文">
              <el-option label="Ryan - 富有节奏感的动感男声" value="ryan" />
              <el-option label="Aiden - 阳光美式男声，中音清晰" value="aiden" />
            </el-option-group>
            <el-option-group label="其他语言">
              <el-option label="Ono Anna - 俏皮日本女声，音色轻快灵动（日语）" value="ono_anna" />
              <el-option label="Sohee - 温暖韩语女声，情感丰富（韩语）" value="sohee" />
            </el-option-group>
          </el-select>
        </el-form-item>
        
        <el-form-item label="语言">
          <el-select v-model="testForm.language" style="width: 100%">
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
        
        <el-form-item label="服务地址">
          <el-input
            v-model="testForm.base_url"
            placeholder="http://localhost:8003"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showTestDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="generateTestAudio" 
          :loading="generating"
          :disabled="!testForm.text.trim()"
        >
          <el-icon><Headset /></el-icon>
          {{ generating ? '生成中...' : '生成并下载' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, Microphone, Headset } from '@element-plus/icons-vue'
import { getSettings, updateSettings } from '@/api'
import LanguageSelect from '@/components/LanguageSelect.vue'
import api from '@/api'

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
  local_tts_base_url: 'http://localhost:8003',
  local_tts_speaker: 'vivian',
  local_tts_language: 'auto',
  default_source_language: 'zh',
  default_target_language: 'en'
})

const originalSettings = ref(null)
const saving = ref(false)
const testing = ref(false)
const showTestDialog = ref(false)
const generating = ref(false)

const testForm = ref({
  text: '你好，这是Qwen3-TTS的测试语音。',
  speaker: 'vivian',
  language: 'auto',
  base_url: 'http://localhost:8003'
})

const loadSettings = async () => {
  try {
    const data = await getSettings()
    settings.value = { ...settings.value, ...data }
    originalSettings.value = JSON.parse(JSON.stringify(settings.value))
    
    // 同步测试表单的默认值
    testForm.value.speaker = settings.value.local_tts_speaker || 'vivian'
    testForm.value.language = settings.value.local_tts_language || 'auto'
    testForm.value.base_url = settings.value.local_tts_base_url || 'http://localhost:8003'
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

const testLocalTTS = async () => {
  testing.value = true
  try {
    const baseUrl = settings.value.local_tts_base_url || 'http://localhost:8003'
    const response = await fetch(`${baseUrl}/health`)
    if (response.ok) {
      const data = await response.json()
      if (data.model_loaded) {
        ElMessage.success(`连接成功！模型类型: ${data.model_type || '未知'}`)
      } else {
        ElMessage.warning('服务运行中，但模型尚未加载完成')
      }
    } else {
      ElMessage.error('连接失败：服务响应异常')
    }
  } catch (error) {
    ElMessage.error('连接失败：' + error.message)
  } finally {
    testing.value = false
  }
}

const generateTestAudio = async () => {
  if (!testForm.value.text.trim()) {
    ElMessage.warning('请输入测试文本')
    return
  }
  
  generating.value = true
  
  try {
    // 使用 axios 发送请求，并设置 responseType 为 blob
    const response = await api.post('/settings/tts/test', {
      text: testForm.value.text,
      speaker: testForm.value.speaker,
      language: testForm.value.language,
      base_url: testForm.value.base_url
    }, {
      responseType: 'blob',
      timeout: 120000  // 2分钟超时
    })
    
    // 创建下载链接
    const blob = new Blob([response], { type: 'audio/wav' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `tts_test_${testForm.value.speaker}_${Date.now()}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('音频生成成功，开始下载')
    showTestDialog.value = false
  } catch (error) {
    // 处理 blob 类型的错误响应
    if (error.response && error.response.data instanceof Blob) {
      const reader = new FileReader()
      reader.onload = () => {
        try {
          const errorData = JSON.parse(reader.result)
          ElMessage.error('生成失败：' + (errorData.detail || errorData.message || '未知错误'))
        } catch {
          ElMessage.error('生成失败：' + error.message)
        }
      }
      reader.readAsText(error.response.data)
    } else {
      ElMessage.error('生成失败：' + error.message)
    }
  } finally {
    generating.value = false
  }
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

.button-group {
  display: flex;
  gap: 12px;
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
