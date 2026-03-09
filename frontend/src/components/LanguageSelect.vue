<template>
  <el-select v-model="selectedLanguage" :placeholder="placeholder" @change="handleChange">
    <el-option
      v-for="lang in languages"
      :key="lang.code"
      :label="lang.name"
      :value="lang.code"
    >
      <span class="lang-option">
        <span class="lang-flag">{{ lang.flag }}</span>
        <span class="lang-name">{{ lang.name }}</span>
      </span>
    </el-option>
  </el-select>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'zh'
  },
  placeholder: {
    type: String,
    default: '选择语言'
  },
  exclude: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const languages = [
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'en', name: '英语', flag: '🇺🇸' },
  { code: 'ja', name: '日语', flag: '🇯🇵' },
  { code: 'ko', name: '韩语', flag: '🇰🇷' },
  { code: 'es', name: '西班牙语', flag: '🇪🇸' },
  { code: 'fr', name: '法语', flag: '🇫🇷' },
  { code: 'de', name: '德语', flag: '🇩🇪' },
  { code: 'ru', name: '俄语', flag: '🇷🇺' },
  { code: 'ar', name: '阿拉伯语', flag: '🇸🇦' },
  { code: 'pt', name: '葡萄牙语', flag: '🇵🇹' },
  { code: 'th', name: '泰语', flag: '🇹🇭' },
  { code: 'vi', name: '越南语', flag: '🇻🇳' },
  { code: 'id', name: '印尼语', flag: '🇮🇩' }
].filter(lang => !props.exclude.includes(lang.code))

const selectedLanguage = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const handleChange = (val) => {
  emit('change', val)
}
</script>

<style scoped>
.lang-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lang-flag {
  font-size: 16px;
}

.lang-name {
  font-size: 14px;
}
</style>
