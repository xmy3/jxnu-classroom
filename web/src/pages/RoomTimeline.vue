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

const { favs, isFav, toggle: toggleFav } = useFavorites()
const todayWi = computed(() => currentWeekdayIndex())
const nowSi = computed(() => currentSlotIndex(props.plan))

const freeCount = computed(() =>
  selectedRoom.value ? selectedRoom.value.schedule.flat().filter(s => s === null).length : 0
)
const busyCount = computed(() =>
  selectedRoom.value ? selectedRoom.value.schedule.flat().filter(s => s !== null).length : 0
)
</script>

<template>
  <!-- 主问句区 -->
  <section class="mb-5 sm:mb-6">
    <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-zinc-100 tracking-tight">
      <span v-if="selectedRoom">{{ selectedRoom.id }} 这周的课表</span>
      <span v-else>查一间教室的整周课表</span>
    </h1>
    <p class="text-sm text-slate-500 dark:text-zinc-400 mt-1.5">
      <span v-if="selectedRoom">
        <span class="text-emerald-600 dark:text-emerald-400 font-medium">{{ freeCount }} 格空</span> ·
        <span class="text-rose-600 dark:text-rose-400 font-medium">{{ busyCount }} 格占</span>
      </span>
      <span v-else>输入教室号(如 W1101),查这周一到周日每节课的占用情况</span>
    </p>
  </section>

  <div class="space-y-4">
    <!-- 教室选择 -->
    <section class="card p-3 sm:p-4">
      <div class="relative max-w-md">
        <input
          v-model="search"
          type="text"
          autocomplete="off"
          spellcheck="false"
          placeholder="输入教室号,例如 W1101"
          class="w-full px-4 py-2.5 text-base rounded-lg
                 border border-slate-300 dark:border-zinc-700
                 bg-white dark:bg-zinc-900
                 text-slate-900 dark:text-zinc-100
                 placeholder:text-slate-400 dark:placeholder:text-zinc-500
                 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        />
        <button
          v-if="search"
          @click="clearSelection"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600
                 dark:text-zinc-500 dark:hover:text-zinc-300 text-xl leading-none px-1"
        >×</button>
      </div>

      <!-- 候选 -->
      <div
        v-if="!selectedRoom && matchingRooms.length > 0"
        class="mt-3 flex flex-wrap gap-1"
      >
        <button
          v-for="r in matchingRooms"
          :key="r.id"
          @click="pickRoom(r)"
          class="text-xs px-2.5 py-1 rounded-md
                 bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 text-slate-700
                 dark:bg-zinc-800 dark:hover:bg-emerald-900/40 dark:hover:text-emerald-300 dark:text-zinc-300
                 transition-colors"
        >
          {{ r.id }}
        </button>
      </div>
      <p v-else-if="!selectedRoom && search" class="text-sm text-slate-500 dark:text-zinc-400 mt-3">
        没有匹配的教室
      </p>

      <!-- 收藏快捷入口 -->
      <div
        v-if="!selectedRoom && favs.length > 0"
        class="mt-4 pt-3 border-t border-slate-100 dark:border-zinc-800"
      >
        <div class="text-xs text-slate-500 dark:text-zinc-400 mb-1.5">
          <span class="text-amber-400">★</span> 我的常用
        </div>
        <div class="flex flex-wrap gap-1">
          <button
            v-for="id in favs"
            :key="id"
            @click="pickRoom({ id } as Room)"
            class="text-xs px-2.5 py-1 rounded-md
                   bg-amber-50 text-amber-800 hover:bg-amber-100
                   dark:bg-amber-900/30 dark:text-amber-200 dark:hover:bg-amber-900/50
                   transition-colors"
          >{{ id }}</button>
        </div>
      </div>
    </section>

    <!-- 课表 -->
    <section v-if="selectedRoom" class="card overflow-hidden">
      <div class="px-4 py-3 border-b border-slate-100 dark:border-zinc-800 flex items-baseline justify-between">
        <div class="flex items-baseline gap-2">
          <span class="text-xl font-bold text-slate-900 dark:text-zinc-100">{{ selectedRoom.id }}</span>
          <button
            @click="toggleFav(selectedRoom.id)"
            class="text-lg leading-none px-1 transition-colors"
            :class="isFav(selectedRoom.id)
              ? 'text-amber-400 hover:text-amber-500'
              : 'text-slate-300 hover:text-amber-400 dark:text-zinc-600 dark:hover:text-amber-400'"
            :title="isFav(selectedRoom.id) ? '取消收藏' : '加入我的常用'"
          >{{ isFav(selectedRoom.id) ? '★' : '☆' }}</button>
        </div>
        <RouterLink to="/" class="text-xs text-slate-500 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-zinc-100">
          ← 回教室列表
        </RouterLink>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="bg-slate-50 dark:bg-zinc-900/70 text-slate-600 dark:text-zinc-400">
              <th class="px-2 py-2 font-medium text-left">时段</th>
              <th
                v-for="(name, i) in plan.meta.weekdays"
                :key="i"
                class="px-1 py-2 font-medium"
                :class="i === todayWi ? 'text-amber-700 dark:text-amber-300' : ''"
              >{{ name.replace('周', '') }}<span v-if="i === todayWi" class="text-amber-500 dark:text-amber-400 ml-0.5">·今</span></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(s, si) in plan.meta.slots"
              :key="s.key"
              class="border-t border-slate-100 dark:border-zinc-800"
              :class="si === nowSi ? 'bg-amber-50/60 dark:bg-amber-900/20' : ''"
            >
              <td class="px-2 py-1.5 text-slate-500 dark:text-zinc-400 whitespace-nowrap leading-tight">
                <div>
                  {{ s.label }}<span v-if="si === nowSi" class="ml-0.5 text-amber-500 dark:text-amber-400" title="当前节次">🕐</span>
                </div>
                <div class="text-[10px] text-slate-400 dark:text-zinc-500 tabular-nums">{{ slotTime(s.key) }}</div>
              </td>
              <td
                v-for="(_, wi) in plan.meta.weekdays"
                :key="wi"
                class="px-0.5 py-0.5 align-middle"
                :class="wi === todayWi && si === nowSi ? 'ring-1 ring-amber-300 dark:ring-amber-600 ring-inset' : ''"
              >
                <div
                  v-if="selectedRoom.schedule[wi][si]"
                  @click="openDetail(wi, si)"
                  class="rounded p-1 text-[10px] leading-snug min-h-[2rem] cursor-pointer transition-colors
                         bg-rose-50 border border-rose-200/60 text-rose-900 hover:bg-rose-100 hover:border-rose-300
                         dark:bg-rose-950/40 dark:border-rose-900/60 dark:text-rose-100
                         dark:hover:bg-rose-900/40 dark:hover:border-rose-800"
                >
                  <div class="font-medium line-clamp-2">{{ selectedRoom.schedule[wi][si]!.c }}</div>
                  <div class="opacity-70 line-clamp-1">{{ selectedRoom.schedule[wi][si]!.t }}</div>
                </div>
                <div
                  v-else
                  class="rounded min-h-[2rem] flex items-center justify-center text-[10px]
                         bg-emerald-50 border border-emerald-200/60 text-emerald-600
                         dark:bg-emerald-950/30 dark:border-emerald-900/60 dark:text-emerald-400/80"
                >空</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 py-2 text-xs text-slate-500 dark:text-zinc-400 border-t border-slate-100 dark:border-zinc-800 flex justify-between">
        <span>
          <span class="text-emerald-600 dark:text-emerald-400 font-medium">{{ freeCount }}</span> 空 ·
          <span class="text-rose-600 dark:text-rose-400 font-medium">{{ busyCount }}</span> 占
        </span>
        <span class="text-slate-400 dark:text-zinc-500">点红色格看课程详情</span>
      </div>
    </section>

    <!-- 课程详情弹窗 -->
    <Teleport to="body">
      <div
        v-if="detail"
        @click.self="closeDetail"
        class="fixed inset-0 z-50 bg-black/50 dark:bg-black/70 flex items-center justify-center p-4"
      >
        <div class="bg-white dark:bg-zinc-900 dark:border dark:border-zinc-800 rounded-xl shadow-xl max-w-sm w-full overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-100 dark:border-zinc-800 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="text-lg font-bold text-slate-900 dark:text-zinc-100 break-words">{{ detail.course.c }}</div>
              <div class="text-xs text-slate-500 dark:text-zinc-400 mt-1">
                {{ selectedRoom?.id }} · {{ detail.weekday }} · {{ detail.slot }}<span v-if="detail.time" class="text-slate-400 dark:text-zinc-500"> ({{ detail.time }})</span>
              </div>
            </div>
            <button
              @click="closeDetail"
              class="text-slate-400 hover:text-slate-700 dark:text-zinc-500 dark:hover:text-zinc-200 text-2xl leading-none shrink-0"
              aria-label="关闭"
            >×</button>
          </div>
          <dl class="px-5 py-4 text-sm space-y-3">
            <div v-if="detail.course.l">
              <dt class="text-xs text-slate-500 dark:text-zinc-400 mb-0.5">班级</dt>
              <dd class="text-slate-800 dark:text-zinc-200 break-words">{{ detail.course.l }}</dd>
            </div>
            <div v-if="detail.course.t">
              <dt class="text-xs text-slate-500 dark:text-zinc-400 mb-0.5">教师</dt>
              <dd class="text-slate-800 dark:text-zinc-200 break-words">{{ detail.course.t }}</dd>
            </div>
            <div v-if="!detail.course.l && !detail.course.t" class="text-slate-400 dark:text-zinc-500">
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
