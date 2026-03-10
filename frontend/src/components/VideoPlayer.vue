<template>
  <div class="video-player" ref="containerRef">
    <!-- 视频信息面板 -->
    <div class="video-info-panel" v-if="isReady">
      <div class="info-row">
        <div class="info-item">
          <span class="label">分辨率:</span>
          <span class="value">{{ displayWidth }}x{{ displayHeight }}</span>
        </div>
        <div class="info-item">
          <span class="label">帧率:</span>
          <span class="value">{{ displayFps }} fps</span>
        </div>
        <div class="info-item">
          <span class="label">时长:</span>
          <span class="value">{{ formatTime(totalDuration) }}</span>
        </div>
      </div>
      <div class="info-row">
        <div class="info-item">
          <span class="label">当前时间:</span>
          <span class="value">{{ formatTime(currentTime) }}</span>
        </div>
        <div class="info-item">
          <span class="label">当前帧:</span>
          <span class="value">{{ currentFrame }} / {{ totalFrames }}</span>
        </div>
        <div class="info-item" v-if="currentSubtitleIndex >= 0">
          <span class="label">当前字幕:</span>
          <span class="value">#{{ currentSubtitleIndex + 1 }}</span>
        </div>
      </div>
    </div>

    <!-- 视频容器 -->
    <div class="video-container" @click="handleVideoClick">
      <video
        ref="videoRef"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onMetadataLoaded"
        @play="onPlay"
        @pause="onPause"
        @seeking="onSeeking"
        @seeked="onSeeked"
        preload="metadata"
        crossOrigin="anonymous"
      ></video>
      <div v-if="!isReady" class="no-video">
        <el-icon><VideoCamera /></el-icon>
        <p>加载中...</p>
      </div>
    </div>

    <!-- 时间轴 -->
    <div class="timeline" v-if="isReady" @click="handleTimelineClick" ref="timelineRef">
      <div class="timeline-track">
        <div class="progress-bar" :style="{width: progressPercent + '%'}"></div>

        <!-- 字幕标记 -->
        <div class="subtitle-markers">
          <div
            v-for="(sub, index) in subtitles"
            :key="sub.id || index"
            class="subtitle-marker"
            :class="{active: index === currentSubtitleIndex}"
            :style="getMarkerStyle(sub)"
            @click.stop="seekToSubtitle(index)"
          ></div>
        </div>

        <div class="playhead" :style="{left: progressPercent + '%'}"></div>
      </div>

      <div class="time-display">
        <span class="time-text">{{ formatTime(currentTime) }} / {{ formatTime(totalDuration) }}</span>
        <span class="frame-text">帧: {{ currentFrame }} / {{ totalFrames }}</span>
      </div>
    </div>

    <!-- 控制按钮 -->
    <div class="controls" v-if="isReady">
      <div class="control-group">
        <el-button @click.prevent="togglePlay" :icon="isPlaying ? VideoPause : VideoPlay" circle />
        <el-button @click.prevent="stop" circle>
          <el-icon><CircleClose /></el-icon>
        </el-button>
      </div>

      <div class="control-group">
        <el-button @click.prevent="stepBackward" title="后退一帧 (D)">|←</el-button>
        <el-button @click.prevent="stepBackward5" title="后退5帧 (Shift+D)">|«←</el-button>
        <el-button @click.prevent="stepForward" title="前进一帧 (F)">→|</el-button>
        <el-button @click.prevent="stepForward5" title="前进5帧 (Shift+F)">→»|</el-button>
      </div>

      <div class="control-group">
        <el-select v-model="playbackRate" @change="setPlaybackRate" style="width: 100px">
          <el-option label="0.5x" :value="0.5" />
          <el-option label="1.0x" :value="1.0" />
          <el-option label="1.5x" :value="1.5" />
          <el-option label="2.0x" :value="2.0" />
        </el-select>
      </div>

      <div class="control-group shortcuts-hint">
        <el-tooltip content="空格: 播放/暂停 | F/D: 帧 | ←/→: 5秒 | J/K: 慢放/快进 | Home/End: 跳转">
          <el-icon><QuestionFilled /></el-icon>
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { VideoPause, VideoPlay, VideoCamera, QuestionFilled, CircleClose } from '@element-plus/icons-vue'

// 组件挂载计数器 - 用于检测是否被重新挂载
const mountCount = ref(0)
const mountId = Math.random().toString(36).substring(7)

console.log('📌 VideoPlayer 组件创建 (mountId:', mountId + ')')

const props = defineProps({
  videoUrl: {
    type: String,
    default: ''
  },
  videoInfo: {
    type: Object,
    default: () => ({ width: 0, height: 0, fps: 0, duration: 0 })
  },
  subtitles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['subtitle-change', 'time-update'])

// DOM引用
const videoRef = ref(null)
const containerRef = ref(null)
const timelineRef = ref(null)

// 状态变量
const currentTime = ref(0)
const totalDuration = ref(0)
const isPlaying = ref(false)
const playbackRate = ref(1.0)
const currentSubtitleIndex = ref(-1)
const isReady = ref(false)

// 显示信息
const displayWidth = ref(0)
const displayHeight = ref(0)
const displayFps = ref(0)

// 计算属性
const progressPercent = computed(() => {
  if (totalDuration.value > 0) {
    return (currentTime.value / totalDuration.value) * 100
  }
  return 0
})

const currentFrame = computed(() => {
  const fps = displayFps.value || 24
  return Math.floor(currentTime.value * fps)
})

const totalFrames = computed(() => {
  const fps = displayFps.value || 24
  return Math.floor(totalDuration.value * fps)
})

// 格式化时间
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '00:00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 获取字幕标记位置
const getMarkerStyle = (subtitle) => {
  if (!totalDuration.value || totalDuration.value <= 0) {
    return { left: '0%', width: '0%' }
  }
  const left = (subtitle.start_time / totalDuration.value) * 100
  const width = ((subtitle.end_time - subtitle.start_time) / totalDuration.value) * 100
  return { left: left + '%', width: width + '%' }
}

// 初始化视频
const initializeVideo = async () => {
  console.log('=== initializeVideo 调用 ===', {
    videoUrl: props.videoUrl,
    videoRef存在: !!videoRef.value,
    当前src: videoRef.value?.src,
    当前currentTime: videoRef.value?.currentTime
  })

  if (!videoRef.value) {
    console.log('等待 videoRef...')
    await nextTick()
  }

  if (!videoRef.value) {
    console.error('❌ videoRef 仍然不存在')
    return
  }

  if (!props.videoUrl) {
    console.log('⚠️ videoUrl 为空，无法初始化')
    return
  }

  // 检查是否需要重新设置src
  if (videoRef.value.src === props.videoUrl || videoRef.value.src.endsWith(props.videoUrl)) {
    console.log('✓ 视频源已设置，跳过重复设置')
    isReady.value = true
    return
  }

  try {
    console.log('📹 设置视频源:', props.videoUrl)
    videoRef.value.src = props.videoUrl
    isReady.value = true
    console.log('✅ 视频源设置完成')
  } catch (error) {
    console.error('❌ 设置视频源失败:', error)
  }
}

// 元数据加载完成
const onMetadataLoaded = () => {
  if (!videoRef.value) return

  totalDuration.value = videoRef.value.duration || 0
  displayWidth.value = videoRef.value.videoWidth || 0
  displayHeight.value = videoRef.value.videoHeight || 0

  // 如果从videoInfo获取不到fps，使用默认值
  displayFps.value = props.videoInfo.fps || 24

  console.log('元数据加载完成:', {
    duration: totalDuration.value,
    width: displayWidth.value,
    height: displayHeight.value,
    fps: displayFps.value
  })
}

// 时间更新
const onTimeUpdate = () => {
  if (!videoRef.value) return

  const newTime = videoRef.value.currentTime

  // 检测时间是否被异常重置为0
  if (newTime === 0 && currentTime.value > 1) {
    console.error('🚨 警告：currentTime 被异常重置为 0！之前的时间:', currentTime.value)
    console.trace('调用栈：')
  }

  currentTime.value = newTime

  // 更新当前字幕
  updateCurrentSubtitle()
  emit('time-update', newTime)
}

// 更新当前字幕
const updateCurrentSubtitle = () => {
  const index = props.subtitles.findIndex(
    sub => currentTime.value >= sub.start_time && currentTime.value < sub.end_time
  )
  if (index !== currentSubtitleIndex.value) {
    currentSubtitleIndex.value = index
    emit('subtitle-change', index)
  }
}

// 播放控制
const togglePlay = () => {
  if (!videoRef.value) return

  if (videoRef.value.paused) {
    videoRef.value.play().catch(err => {
      console.error('播放失败:', err)
    })
  } else {
    videoRef.value.pause()
  }
}

const stop = () => {
  if (!videoRef.value) return
  videoRef.value.pause()
  videoRef.value.currentTime = 0
}

const setPlaybackRate = (rate) => {
  if (videoRef.value) {
    videoRef.value.playbackRate = rate
  }
}

// 帧控制
const stepForward = () => {
  console.log('=== stepForward 调用 ===')
  if (!videoRef.value) {
    console.log('❌ videoRef 不存在')
    return
  }

  const duration = videoRef.value.duration
  if (!duration || isNaN(duration) || duration === 0) {
    console.error('❌ 视频duration无效:', duration)
    return
  }

  const fps = displayFps.value || 24
  const frameTime = 1 / fps
  const currentTimeBefore = videoRef.value.currentTime
  const newTime = Math.min(currentTimeBefore + frameTime, duration)

  console.log('设置 currentTime:', {
    之前: currentTimeBefore.toFixed(3),
    之后: newTime.toFixed(3),
    frameTime: frameTime.toFixed(3),
    duration: duration.toFixed(3),
    src: videoRef.value.src
  })

  videoRef.value.currentTime = newTime

  // 立即检查是否成功
  setTimeout(() => {
    const actualTime = videoRef.value.currentTime
    console.log('✅ 实际 currentTime:', actualTime.toFixed(3), actualTime === newTime ? '✓ 成功' : '✗ 失败')
  }, 50)
}

const stepBackward = () => {
  console.log('=== stepBackward 调用 ===')
  if (!videoRef.value) {
    console.log('❌ videoRef 不存在')
    return
  }

  const fps = displayFps.value || 24
  const frameTime = 1 / fps
  const currentTimeBefore = videoRef.value.currentTime
  const newTime = Math.max(currentTimeBefore - frameTime, 0)

  console.log('设置 currentTime:', {
    之前: currentTimeBefore.toFixed(3),
    之后: newTime.toFixed(3),
    frameTime: frameTime.toFixed(3),
    duration: (videoRef.value.duration || 0).toFixed(3),
    src: videoRef.value.src
  })

  videoRef.value.currentTime = newTime

  // 立即检查是否成功
  setTimeout(() => {
    const actualTime = videoRef.value.currentTime
    console.log('✅ 实际 currentTime:', actualTime.toFixed(3), actualTime === newTime ? '✓ 成功' : '✗ 失败')
  }, 50)
}

const stepForward5 = () => {
  console.log('=== stepForward5 调用 ===')
  if (!videoRef.value) {
    console.log('❌ videoRef 不存在')
    return
  }

  const duration = videoRef.value.duration
  if (!duration || isNaN(duration) || duration === 0) {
    console.error('❌ 视频duration无效:', duration)
    return
  }

  const fps = displayFps.value || 24
  const frameTime = 5 / fps
  const currentTimeBefore = videoRef.value.currentTime
  const newTime = Math.min(currentTimeBefore + frameTime, duration)

  console.log('设置 currentTime:', {
    之前: currentTimeBefore.toFixed(3),
    之后: newTime.toFixed(3),
    frameTime: frameTime.toFixed(3),
    duration: duration.toFixed(3)
  })

  videoRef.value.currentTime = newTime

  setTimeout(() => {
    console.log('✅ 实际 currentTime:', videoRef.value.currentTime.toFixed(3))
  }, 50)
}

const stepBackward5 = () => {
  console.log('=== stepBackward5 调用 ===')
  if (!videoRef.value) {
    console.log('❌ videoRef 不存在')
    return
  }

  const fps = displayFps.value || 24
  const frameTime = 5 / fps
  const currentTimeBefore = videoRef.value.currentTime
  const newTime = Math.max(currentTimeBefore - frameTime, 0)

  console.log('设置 currentTime:', {
    之前: currentTimeBefore.toFixed(3),
    之后: newTime.toFixed(3),
    frameTime: frameTime.toFixed(3),
    duration: (videoRef.value.duration || 0).toFixed(3)
  })

  videoRef.value.currentTime = newTime

  setTimeout(() => {
    console.log('✅ 实际 currentTime:', videoRef.value.currentTime.toFixed(3))
  }, 50)
}

// 时间轴控制
const handleTimelineClick = (event) => {
  console.log('=== handleTimelineClick 调用 ===')
  if (!timelineRef.value) {
    console.log('❌ timelineRef 不存在')
    return
  }
  if (!videoRef.value) {
    console.log('❌ videoRef 不存在')
    return
  }

  const duration = videoRef.value.duration
  if (!duration || isNaN(duration) || duration === 0) {
    console.error('❌ 视频duration无效:', duration)
    return
  }

  const rect = timelineRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const percent = Math.max(0, Math.min(1, x / rect.width))
  const targetTime = percent * duration
  const currentTimeBefore = videoRef.value.currentTime

  console.log('进度条点击详情:', {
    点击位置X: x,
    进度条宽度: rect.width,
    计算百分比: (percent * 100).toFixed(2) + '%',
    目标时间: targetTime.toFixed(2) + 's',
    当前时间: currentTimeBefore.toFixed(2) + 's',
    视频时长: duration.toFixed(2) + 's',
    视频src: videoRef.value.src
  })

  videoRef.value.currentTime = targetTime

  // 立即检查是否成功
  setTimeout(() => {
    const actualTime = videoRef.value.currentTime
    console.log('✅ 跳转后实际 currentTime:', actualTime.toFixed(2) + 's',
      Math.abs(actualTime - targetTime) < 0.1 ? '✓ 成功' : '✗ 失败')
  }, 50)
}

const seekToSubtitle = (index) => {
  const subtitle = props.subtitles[index]
  if (subtitle && videoRef.value) {
    videoRef.value.currentTime = subtitle.start_time
  }
}

// 视频点击处理
const handleVideoClick = () => {
  togglePlay()
}

// 事件处理函数
const onPlay = () => {
  isPlaying.value = true
  console.log('▶️ 视频开始播放，currentTime:', videoRef.value?.currentTime)
}

const onPause = () => {
  isPlaying.value = false
  console.log('⏸️ 视频暂停，currentTime:', videoRef.value?.currentTime)
}

let seekingStartTime = 0
const onSeeking = () => {
  seekingStartTime = Date.now()
  const timeBeforeSeek = videoRef.value?.currentTime
  console.log('🔍 视频正在seek...', {
    currentTime: timeBeforeSeek,
    触发时间: new Date().toLocaleTimeString()
  })

  // 延迟检查seeking期间是否发生了异常
  setTimeout(() => {
    if (videoRef.value && videoRef.value.currentTime === 0 && timeBeforeSeek > 1) {
      console.error('🚨 seek过程中currentTime被重置为0！seek之前:', timeBeforeSeek)
    }
  }, 100)
}

const onSeeked = () => {
  const seekDuration = Date.now() - seekingStartTime
  const finalTime = videoRef.value?.currentTime
  console.log('✅ 视频seek完成', {
    currentTime: finalTime,
    耗时: seekDuration + 'ms'
  })
}

// 暴露方法
defineExpose({
  videoRef,
  seekToSubtitle
})

// 键盘控制
const handleKeyDown = (event) => {
  // 如果在输入框中，不处理快捷键
  const target = event.target
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
    return
  }

  if (!videoRef.value) return

  switch(event.key) {
    case ' ':
      event.preventDefault()
      togglePlay()
      break
    case 'f':
    case 'F':
      stepForward()
      break
    case 'd':
    case 'D':
      stepBackward()
      break
    case 'ArrowLeft':
      event.preventDefault()
      videoRef.value.currentTime = Math.max(0, videoRef.value.currentTime - 5)
      break
    case 'ArrowRight':
      event.preventDefault()
      videoRef.value.currentTime = Math.min(totalDuration.value, videoRef.value.currentTime + 5)
      break
    case 'j':
    case 'J':
      playbackRate.value = Math.max(0.25, playbackRate.value - 0.25)
      setPlaybackRate(playbackRate.value)
      break
    case 'k':
    case 'K':
      playbackRate.value = Math.min(4, playbackRate.value + 0.25)
      setPlaybackRate(playbackRate.value)
      break
    case 'Home':
      event.preventDefault()
      videoRef.value.currentTime = 0
      break
    case 'End':
      event.preventDefault()
      videoRef.value.currentTime = totalDuration.value
      break
  }
}

// 组件挂载和卸载
onMounted(async () => {
  mountCount.value++
  console.log('🚀 VideoPlayer onMounted', {
    mountId,
    mountCount: mountCount.value,
    videoUrl: props.videoUrl,
    hasVideoRef: !!videoRef.value
  })

  // 添加键盘监听
  document.addEventListener('keydown', handleKeyDown)

  // 等待DOM更新后初始化视频
  await nextTick()
  await initializeVideo()

  // 监听video元素的所有可能导致重载的事件
  if (videoRef.value) {
    videoRef.value.addEventListener('loadstart', () => {
      console.log('⚠️ 视频触发 loadstart 事件 - 可能正在重新加载')
    })
    videoRef.value.addEventListener('abort', () => {
      console.log('⚠️ 视频触发 abort 事件 - 加载被中止')
    })
    videoRef.value.addEventListener('error', (e) => {
      console.log('⚠️ 视频触发 error 事件:', e)
    })
  }
})

onUnmounted(() => {
  console.log('💥 VideoPlayer onUnmounted', {
    mountId,
    mountCount: mountCount.value
  })
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.video-player {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
}

.video-info-panel {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  gap: 24px;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-item {
  display: flex;
  gap: 8px;
}

.info-item .label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.info-item .value {
  font-size: 13px;
  color: #303133;
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', monospace;
}

.video-container {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  cursor: pointer;
}

.video-container video {
  width: 100%;
  max-height: 500px;
  display: block;
  margin: 0 auto;
}

.no-video {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #909399;
}

.no-video .el-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.timeline {
  margin-bottom: 16px;
}

.timeline-track {
  position: relative;
  height: 32px;
  background: #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 8px;
}

.progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
  transition: width 0.1s linear;
  pointer-events: none;
}

.subtitle-markers {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.subtitle-marker {
  position: absolute;
  top: 0;
  height: 100%;
  background: rgba(103, 126, 234, 0.3);
  border: 1px solid rgba(103, 126, 234, 0.6);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.subtitle-marker:hover {
  background: rgba(103, 126, 234, 0.5);
}

.subtitle-marker.active {
  background: rgba(103, 126, 234, 0.7);
  border-color: #667eea;
}

.playhead {
  position: absolute;
  top: 0;
  width: 2px;
  height: 100%;
  background: #f56c6c;
  transform: translateX(-1px);
  z-index: 10;
  pointer-events: none;
}

.time-display {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
  font-family: 'Monaco', 'Menlo', monospace;
}

.controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.control-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.shortcuts-hint {
  margin-left: auto;
  color: #909399;
  cursor: help;
}
</style>
