<template>
  <div class="drafts">
    <div class="header">
      <h1>草稿箱</h1>
    </div>

    <el-table :data="draftProjects" style="width: 100%">
      <el-table-column prop="name" label="项目名称" min-width="200">
        <template #default="{ row }">
          <div class="project-name-cell">
            <el-icon><VideoCamera /></el-icon>
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="source_language" label="源语言" width="100">
        <template #default="{ row }">
          <span class="language-tag">{{ getLanguageName(row.source_language) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="target_language" label="目标语言" width="100">
        <template #default="{ row }">
          <span class="language-tag">{{ getLanguageName(row.target_language) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="openProject(row.id)">
            编辑
          </el-button>
          <el-button type="danger" size="small" @click="deleteProject(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="draftProjects.length === 0" description="暂无草稿项目" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProjects, deleteProject as deleteProjectApi } from '@/api'

const router = useRouter()
const projects = ref([])

const draftProjects = computed(() => {
  return projects.value.filter(p => p.status !== 'exported')
})

const loadProjects = async () => {
  try {
    projects.value = await getProjects()
  } catch (error) {
    ElMessage.error('加载项目失败：' + error.message)
  }
}

const openProject = (id) => {
  router.push(`/project/${id}`)
}

const deleteProject = async (project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？此操作不可恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteProjectApi(project.id)
    ElMessage.success('项目已删除')
    loadProjects()
  } catch {
    // 取消删除
  }
}

const statusType = (status) => {
  const map = {
    'draft': 'info',
    'uploaded': '',
    'asr_done': 'warning',
    'translated': 'success',
    'dubbed': 'success'
  }
  return map[status] || 'info'
}

const statusText = (status) => {
  const map = {
    'draft': '草稿',
    'uploaded': '已上传',
    'asr_done': '已识别',
    'translated': '已翻译',
    'dubbed': '已配音'
  }
  return map[status] || status
}

const getLanguageName = (code) => {
  const map = {
    'zh': '中文', 'en': '英语', 'ja': '日语', 'ko': '韩语',
    'es': '西班牙语', 'fr': '法语', 'de': '德语', 'ru': '俄语',
    'ar': '阿拉伯语', 'pt': '葡萄牙语', 'th': '泰语',
    'vi': '越南语', 'id': '印尼语'
  }
  return map[code] || code
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(loadProjects)
</script>

<style scoped>
.drafts {
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 24px;
}

.header h1 {
  font-size: 24px;
  color: #303133;
}

.project-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-name-cell .el-icon {
  color: #667eea;
}

.language-tag {
  padding: 2px 8px;
  background: #f0f2ff;
  border-radius: 4px;
  font-size: 12px;
  color: #667eea;
}
</style>
