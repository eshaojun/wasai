import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// ===== 项目 API =====

export const getProjects = () => api.get('/projects/')

export const getProject = (id) => api.get(`/projects/${id}`)

export const createProject = (data) => api.post('/projects/', data)

export const updateProject = (id, data) => api.put(`/projects/${id}`, data)

export const deleteProject = (id) => api.delete(`/projects/${id}`)

// ===== 字幕 API =====

export const getSubtitles = (projectId) => api.get(`/projects/${projectId}/subtitles`)

export const createSubtitle = (projectId, data) => api.post(`/projects/${projectId}/subtitles`, data)

export const updateSubtitle = (projectId, subtitleId, data) =>
  api.put(`/projects/${projectId}/subtitles/${subtitleId}`, data)

export const deleteSubtitle = (projectId, subtitleId) =>
  api.delete(`/projects/${projectId}/subtitles/${subtitleId}`)

export const batchUpdateSubtitles = (projectId, subtitles) =>
  api.post(`/projects/${projectId}/batch-update-subtitles`, subtitles)

// ===== 设置 API =====

export const getSettings = () => api.get('/settings/')

export const updateSettings = (data) => api.put('/settings/', data)

// ===== AI 服务 API =====

export const executeASR = (projectId, params) =>
  api.post(`/projects/${projectId}/asr`, params)

export const executeTTS = (projectId, params) =>
  api.post(`/projects/${projectId}/tts`, params)

export const translateSubtitles = (projectId, data) =>
  api.post(`/projects/${projectId}/translate`, data)

export const exportVideo = (projectId, params) =>
  api.post(`/projects/${projectId}/export`, params)

// ===== 字幕导入导出 API =====

export const previewImportSubtitles = (projectId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/projects/${projectId}/subtitles/preview-import`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const importSubtitles = (projectId, subtitles, mode = 'replace') =>
  api.post(`/projects/${projectId}/subtitles/import?mode=${mode}`, subtitles)

export const exportSubtitles = (projectId, format = 'srt') => {
  return api.get(`/projects/${projectId}/subtitles/export?format=${format}`, {
    responseType: 'blob'
  })
}

export default api
