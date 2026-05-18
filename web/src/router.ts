import { createRouter, createWebHashHistory } from 'vue-router'
import RangeFree from '@/pages/RangeFree.vue'
import RoomTimeline from '@/pages/RoomTimeline.vue'
import Heatmap from '@/pages/Heatmap.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'range', component: RangeFree, meta: { title: '教室列表' } },
    { path: '/room', name: 'room', component: RoomTimeline, meta: { title: '课表查询' } },
    { path: '/heatmap', name: 'heatmap', component: Heatmap, meta: { title: '占用热力图' } },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.afterEach(to => {
  const t = to.meta?.title as string | undefined
  document.title = t ? `${t} · 江西师范大学(瑶湖校区)空教室` : '江西师范大学(瑶湖校区)空教室'
})

export default router
