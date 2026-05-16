import { createRouter, createWebHashHistory } from 'vue-router'
import FreeRooms from '@/pages/FreeRooms.vue'
import RoomTimeline from '@/pages/RoomTimeline.vue'
import Heatmap from '@/pages/Heatmap.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'free', component: FreeRooms, meta: { title: '找空教室' } },
    { path: '/room', name: 'room', component: RoomTimeline, meta: { title: '教室时段' } },
    { path: '/heatmap', name: 'heatmap', component: Heatmap, meta: { title: '占用热力图' } }
  ]
})

router.afterEach(to => {
  const t = to.meta?.title as string | undefined
  document.title = t ? `${t} · 江师大空教室` : '江师大空教室'
})

export default router
