<template>
  <div class="video-uploader">
    <el-upload
      class="upload-area"
      drag
      :action="uploadUrl"
      :on-success="handleSuccess"
      :on-error="handleError"
      :before-upload="beforeUpload"
      accept="video/*"
      :show-file-list="false"
    >
      <el-icon class="upload-icon"><VideoCamera /></el-icon>
      <div class="upload-text">
        <span>拖拽视频到此处上传</span>
        <span class="upload-hint">或点击选择文件</span>
      </div>
      <div class="upload-formats">
        支持格式：MP4、AVI、MOV、MKV、WebM
      </div>
    </el-upload>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  projectId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['success', 'error'])

const uploadUrl = computed(() => `/api/v1/upload/video/${props.projectId}`)

const beforeUpload = (file) => {
  const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm']
  const isVideo = allowedTypes.includes(file.type)
  const isLt500M = file.size / 1024 / 1024 < 500

  if (!isVideo) {
    ElMessage.error('请上传视频文件！')
    return false
  }
  if (!isLt500M) {
    ElMessage.error('视频大小不能超过 500MB！')
    return false
  }
  return true
}

const handleSuccess = (response) => {
  ElMessage.success('视频上传成功')
  emit('success', response)
}

const handleError = (error) => {
  ElMessage.error('上传失败：' + (error.message || '未知错误'))
  emit('error', error)
}
</script>

<style scoped>
.video-uploader {
  width: 100%;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 240px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
  border: 2px dashed #c0c4cc;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  transition: all 0.3s;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: linear-gradient(135deg, #f0f2ff 0%, #e8ebff 100%);
}

.upload-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 16px;
}

.upload-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
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
  margin-top: 16px;
  font-size: 12px;
  color: #909399;
}
</style>
