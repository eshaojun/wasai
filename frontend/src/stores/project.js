import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getProjects,
  getProject,
  createProject,
  updateProject,
  deleteProject,
  getSubtitles
} from '@/api'

export const useProjectStore = defineStore('project', () => {
  // State
  const projects = ref([])
  const currentProject = ref(null)
  const currentSubtitles = ref([])
  const loading = ref(false)

  // Getters
  const projectCount = computed(() => projects.value.length)

  const projectsByStatus = computed(() => {
    return (status) => projects.value.filter(p => p.status === status)
  })

  // Actions
  const fetchProjects = async () => {
    loading.value = true
    try {
      projects.value = await getProjects()
      return projects.value
    } finally {
      loading.value = false
    }
  }

  const fetchProject = async (id) => {
    loading.value = true
    try {
      currentProject.value = await getProject(id)
      currentSubtitles.value = currentProject.value.subtitles || []
      return currentProject.value
    } finally {
      loading.value = false
    }
  }

  const addProject = async (data) => {
    const project = await createProject(data)
    projects.value.unshift(project)
    return project
  }

  const editProject = async (id, data) => {
    const project = await updateProject(id, data)
    const index = projects.value.findIndex(p => p.id === id)
    if (index !== -1) {
      projects.value[index] = { ...projects.value[index], ...project }
    }
    if (currentProject.value?.id === id) {
      currentProject.value = { ...currentProject.value, ...project }
    }
    return project
  }

  const removeProject = async (id) => {
    await deleteProject(id)
    projects.value = projects.value.filter(p => p.id !== id)
    if (currentProject.value?.id === id) {
      currentProject.value = null
      currentSubtitles.value = []
    }
  }

  const fetchSubtitles = async (projectId) => {
    const subtitles = await getSubtitles(projectId)
    currentSubtitles.value = subtitles
    return subtitles
  }

  const updateSubtitles = (subtitles) => {
    currentSubtitles.value = subtitles
  }

  const clearCurrentProject = () => {
    currentProject.value = null
    currentSubtitles.value = []
  }

  return {
    // State
    projects,
    currentProject,
    currentSubtitles,
    loading,
    // Getters
    projectCount,
    projectsByStatus,
    // Actions
    fetchProjects,
    fetchProject,
    addProject,
    editProject,
    removeProject,
    fetchSubtitles,
    updateSubtitles,
    clearCurrentProject
  }
})
