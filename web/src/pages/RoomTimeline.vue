<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import type { Plan, Room } from '@/types'

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
        <div>
          <span class="text-xl font-bold">{{ selectedRoom.id }}</span>
          <span class="text-sm text-slate-500 ml-2">{{ selectedRoom.type }}</span>
        </div>
        <RouterLink to="/" class="text-xs text-slate-500 hover:text-slate-900">
          ← 返回找空教室
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
            >
              <td class="px-2 py-1.5 text-slate-500 whitespace-nowrap">
                {{ s.label }}
              </td>
              <td
                v-for="(_, wi) in plan.meta.weekdays"
                :key="wi"
                class="px-0.5 py-0.5 align-middle"
              >
                <div
                  v-if="selectedRoom.schedule[wi][si]"
                  class="bg-rose-50 border border-rose-100 rounded p-1 text-rose-900 text-[10px] leading-snug min-h-[2rem]"
                  :title="`${selectedRoom.schedule[wi][si]!.c}\n${selectedRoom.schedule[wi][si]!.l}\n${selectedRoom.schedule[wi][si]!.t}`"
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
        <span class="text-slate-400">hover 单元格看完整信息</span>
      </div>
    </section>
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
