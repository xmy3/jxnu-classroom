<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import type { Course, Plan, Room } from '@/types'
import { slotTime, useFavorites, currentSlotIndex, currentWeekdayIndex } from '@/composables/usePlan'

const props = defineProps<{ plan: Plan }>()
const route = useRoute()
const router = useRouter()

const queryRoomId = computed(() => (route.query.id as string) || '')
const search = ref(queryRoomId.value)

watch(queryRoomId, v => { if (v) search.value = v })

const matchingRooms = computed<Room[]>(() => {
  const q = search.value.trim().toUpperCase()
  if (!q) return []
  return props.plan.rooms
    .filter(r => r.id.toUpperCase().includes(q))
    .slice(0, 24)
})

const selectedRoom = computed<Room | null>(() => {
  if (!queryRoomId.value) return null
  return props.plan.rooms.find(r => r.id === queryRoomId.value) ?? null
})

function pickRoom(r: Room) {
  search.value = r.id
  router.replace({ name: 'room', query: { id: r.id } })
}

function clearSelection() {
  search.value = ''
  router.replace({ name: 'room' })
}

const detail = ref<{ course: Course; weekday: string; slot: string; time: string } | null>(null)

function openDetail(wi: number, si: number) {
  const room = selectedRoom.value
  if (!room) return
  const c = room.schedule[wi][si]
  if (!c) return
  const s = props.plan.meta.slots[si]
  detail.value = {
    course: c,
    weekday: props.plan.meta.weekdays[wi],
    slot: s.label,
    time: slotTime(s.key),
  }
}

function closeDetail() {
  detail.value = null
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') closeDetail()
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

const { isFav, toggle: toggleFav } = useFavorites()
const todayWi = computed(() => currentWeekdayIndex())
const nowSi = computed(() => currentSlotIndex(props.plan))
</script>

<template>
  <div class="space-y-4">
    <!-- 教室选择 -->
    <section class="card p-4">
      <label class="block text-xs font-medium text-slate-500 mb-2">教室号</label>
      <div class="relative">
        <input
          v-model="search"
          type="text"
          autocomplete="off"
          spellcheck="false"
          placeholder="例如:W1101"
          class="w-full px-3 py-2.5 text-base rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
        />
        <button
          v-if="search"
          @click="clearSelection"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xl leading-none px-1"
        >×</button>
      </div>

      <div
        v-if="!selectedRoom && matchingRooms.length > 0"
        class="mt-3 flex flex-wrap gap-1.5"
      >
        <button
          v-for="r in matchingRooms"
          :key="r.id"
          @click="pickRoom(r)"
          class="pill pill-idle bg-slate-100 text-slate-700"
        >
          {{ r.id }} <span class="opacity-60 text-xs">{{ r.type }}</span>
        </button>
      </div>
      <p v-else-if="!selectedRoom && !search" class="text-sm text-slate-500 mt-3">
        输入教室号查询本周课表
      </p>
      <p v-else-if="!selectedRoom" class="text-sm text-slate-500 mt-3">
        没有匹配的教室
      </p>
    </section>

    <!-- 课表 -->
    <section v-if="selectedRoom" class="card overflow-hidden">
      <div class="px-4 py-3 border-b border-slate-100 flex items-baseline justify-between">
        <div class="flex items-baseline gap-2">
          <span class="text-xl font-bold">{{ selectedRoom.id }}</span>
          <span class="text-sm text-slate-500">{{ selectedRoom.type }}</span>
          <button
            @click="toggleFav(selectedRoom.id)"
            class="text-lg leading-none px-1 transition-colors"
            :class="isFav(selectedRoom.id) ? 'text-amber-400 hover:text-amber-500' : 'text-slate-300 hover:text-amber-400'"
            :title="isFav(selectedRoom.id) ? '取消收藏' : '加入我的常用'"
          >{{ isFav(selectedRoom.id) ? '★' : '☆' }}</button>
        </div>
        <RouterLink to="/" class="text-xs text-slate-500 hover:text-slate-900">
          ← 返回时段空闲
        </RouterLink>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="bg-slate-50 text-slate-600">
              <th class="px-2 py-2 font-medium text-left">时段</th>
              <th
                v-for="(name, i) in plan.meta.weekdays"
                :key="i"
                class="px-1 py-2 font-medium"
              >{{ name.replace('周', '') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(s, si) in plan.meta.slots"
              :key="s.key"
              class="border-t border-slate-100"
              :class="si === nowSi ? 'bg-amber-50/60' : ''"
            >
              <td class="px-2 py-1.5 text-slate-500 whitespace-nowrap leading-tight">
                <div>
                  {{ s.label }}<span v-if="si === nowSi" class="ml-0.5 text-amber-500" title="当前节次">🕐</span>
                </div>
                <div class="text-[10px] text-slate-400 tabular-nums">{{ slotTime(s.key) }}</div>
              </td>
              <td
                v-for="(_, wi) in plan.meta.weekdays"
                :key="wi"
                class="px-0.5 py-0.5 align-middle"
                :class="wi === todayWi && si === nowSi ? 'ring-1 ring-amber-300 ring-inset' : ''"
              >
                <div
                  v-if="selectedRoom.schedule[wi][si]"
                  @click="openDetail(wi, si)"
                  class="bg-rose-50 border border-rose-100 rounded p-1 text-rose-900 text-[10px] leading-snug min-h-[2rem] cursor-pointer hover:bg-rose-100 hover:border-rose-200 transition-colors"
                >
                  <div class="font-medium line-clamp-2">{{ selectedRoom.schedule[wi][si]!.c }}</div>
                  <div class="opacity-70 line-clamp-1">{{ selectedRoom.schedule[wi][si]!.t }}</div>
                </div>
                <div v-else class="text-center text-emerald-500/70 text-xs">·</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 py-2 text-xs text-slate-500 border-t border-slate-100 flex justify-between">
        <span>
          空闲 {{ selectedRoom.schedule.flat().filter(s => s === null).length }} /
          占用 {{ selectedRoom.schedule.flat().filter(s => s !== null).length }} 格
        </span>
        <span class="text-slate-400">点击课程看完整信息</span>
      </div>
    </section>

    <!-- 课程详情弹窗 -->
    <Teleport to="body">
      <div
        v-if="detail"
        @click.self="closeDetail"
        class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      >
        <div class="bg-white rounded-xl shadow-xl max-w-sm w-full overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-100 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="text-lg font-bold text-slate-900 break-words">{{ detail.course.c }}</div>
              <div class="text-xs text-slate-500 mt-1">
                {{ selectedRoom?.id }} · {{ detail.weekday }} · {{ detail.slot }}<span v-if="detail.time" class="text-slate-400"> ({{ detail.time }})</span>
              </div>
            </div>
            <button
              @click="closeDetail"
              class="text-slate-400 hover:text-slate-700 text-2xl leading-none shrink-0"
              aria-label="关闭"
            >×</button>
          </div>
          <dl class="px-5 py-4 text-sm space-y-3">
            <div v-if="detail.course.l">
              <dt class="text-xs text-slate-500 mb-0.5">班级</dt>
              <dd class="text-slate-800 break-words">{{ detail.course.l }}</dd>
            </div>
            <div v-if="detail.course.t">
              <dt class="text-xs text-slate-500 mb-0.5">教师</dt>
              <dd class="text-slate-800 break-words">{{ detail.course.t }}</dd>
            </div>
            <div v-if="!detail.course.l && !detail.course.t" class="text-slate-400">
              该课程未提供更多信息
            </div>
          </dl>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
