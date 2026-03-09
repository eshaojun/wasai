import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSettings, updateSettings } from '@/api'

export const useSettingsStore = defineStore('settings', () => {
  // State
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

  const loading = ref(false)
  const saved = ref(false)

  // Getters
  const hasApiKey = computed(() => {
    return !!settings.value.openai_api_key
  })

  const asrConfig = computed(() => ({
    provider: settings.value.asr_provider,
    api_key: settings.value.openai_api_key,
    base_url: settings.value.openai_base_url,
    model: settings.value.whisper_model
  }))

  const translateConfig = computed(() => ({
    provider: settings.value.translate_provider,
    api_key: settings.value.openai_api_key,
    base_url: settings.value.openai_base_url,
    model: settings.value.translate_model
  }))

  const ttsConfig = computed(() => ({
    provider: settings.value.tts_provider,
    api_key: settings.value.openai_api_key,
    base_url: settings.value.openai_base_url,
    model: settings.value.tts_model,
    voice: settings.value.tts_voice
  }))

  // Actions
  const fetchSettings = async () => {
    loading.value = true
    try {
      const data = await getSettings()
      settings.value = { ...settings.value, ...data }
      return settings.value
    } finally {
      loading.value = false
    }
  }

  const saveSettings = async (newSettings) => {
    loading.value = true
    try {
      await updateSettings(newSettings)
      settings.value = { ...settings.value, ...newSettings }
      saved.value = true
      setTimeout(() => {
        saved.value = false
      }, 3000)
      return true
    } finally {
      loading.value = false
    }
  }

  const updateSetting = (key, value) => {
    settings.value[key] = value
  }

  const resetSettings = () => {
    settings.value = {
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
    }
  }

  return {
    // State
    settings,
    loading,
    saved,
    // Getters
    hasApiKey,
    asrConfig,
    translateConfig,
    ttsConfig,
    // Actions
    fetchSettings,
    saveSettings,
    updateSetting,
    resetSettings
  }
})
