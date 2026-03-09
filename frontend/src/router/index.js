import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        name: 'Workspace',
        component: () => import('@/views/Workspace.vue'),
        meta: { title: '工作台' }
      },
      {
        path: 'drafts',
        name: 'Drafts',
        component: () => import('@/views/Drafts.vue'),
        meta: { title: '草稿箱' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '设置' }
      },
    ]
  },
  {
    path: '/project/:id',
    name: 'ProjectDetail',
    component: () => import('@/views/ProjectDetail.vue'),
    meta: { title: '项目详情' }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
