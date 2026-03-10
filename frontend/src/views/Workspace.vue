<template>
  <div class="workspace">
    <div class="header">
      <h1>工作台</h1>
      <el-button type="primary" @click="createProject">
        <el-icon><Plus /></el-icon>新建项目
      </el-button>
    </div>

    <div class="project-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="openProject(project.id)"
      >
        <div class="project-thumbnail">
          <el-icon v-if="!project.original_video_path"><VideoCamera /></el-icon>
          <video v-else :src="project.original_video_path" />
        </div>
        <div class="project-info">
          <h3 class="project-name">{{ project.name }}</h3>
          <p class="project-desc">{{ project.description || '暂无描述' }}</p>
          <div class="project-meta">
            <el-tag size="small" :type="statusType(project.status)">
              {{ statusText(project.status) }}
            </el-tag>
            <span class="project-date">{{ formatDate(project.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="projects.length === 0" description="暂无项目，点击新建项目开始创作" />

    <!-- 新建项目对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建项目"
      width="500px"
    >
      <el-form :model="newProject" label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="newProject.name" placeholder="输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="newProject.description"
            type="textarea"
            :rows="3"
            placeholder="输入项目描述（可选）"
          />
        </el-form-item>
        <el-form-item label="源语言">
          <LanguageSelect v-model="newProject.source_language" />
        </el-form-item>
        <el-form-item label="目标语言">
          <LanguageSelect
            v-model="newProject.target_language"
            :exclude="[newProject.source_language]"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProjects, createProject as createProjectApi } from '@/api'
import LanguageSelect from '@/components/LanguageSelect.vue'

const router = useRouter()
const projects = ref([])
const dialogVisible = ref(false)
const creating = ref(false)

const newProject = ref({
  name: '',
  description: '',
  source_language: 'zh',
  target_language: 'en'
})

const loadProjects = async () => {
  try {
    projects.value = await getProjects()
  } catch (error) {
    ElMessage.error('加载项目失败：' + error.message)
  }
}

const createProject = () => {
  newProject.value = {
    name: '',
    description: '',
    source_language: 'zh',
    target_language: 'en'
  }
  dialogVisible.value = true
}

const submitCreate = async () => {
  if (!newProject.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }

  creating.value = true
  try {
    const project = await createProjectApi(newProject.value)
    ElMessage.success('项目创建成功')
    dialogVisible.value = false
    openProject(project.id)
  } catch (error) {
    ElMessage.error('创建失败：' + error.message)
  } finally {
    creating.value = false
  }
}

const openProject = (id) => {
  router.push(`/project/${id}`)
}

const statusType = (status) => {
  const map = {
    'draft': 'info',
    'uploaded': '',
    'asr_done': 'warning',
    'translated': 'success',
    'dubbed': 'success',
    'exported': 'success'
  }
  return map[status] || 'info'
}

const statusText = (status) => {
  const map = {
    'draft': '草稿',
    'uploaded': '已上传',
    'asr_done': '已识别',
    'translated': '已翻译',
    'dubbed': '已配音',
    'exported': '已完成'
  }
  return map[status] || status
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

onMounted(loadProjects)
</script>

<style scoped>
.workspace {
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h1 {
  font-size: 24px;
  color: #303133;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.project-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.project-thumbnail {
  height: 160px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.project-thumbnail .el-icon {
  font-size: 48px;
  color: rgba(255, 255, 255, 0.8);
}

.project-thumbnail video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.project-info {
  padding: 16px;
}

.project-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-desc {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-date {
  font-size: 12px;
  color: #c0c4cc;
}
</style>
