<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Plan } from '@/types'
import {
  findFreeRooms, listBuildings, listTypes,
  slotTime, currentSlotIndex, currentWeekdayIndex, useFavorites
} from '@/composables/usePlan'

const props = defineProps<{ plan: Plan }>()

const weekday = ref<number>(currentWeekdayIndex())
const slot = ref<number>(currentSlotIndex(props.plan))
const typeFilter = ref<string>('')
const buildingFilter = ref<string>('')
const showFilters = ref(false)

const { favs, isFav } = useFavorites()

const todayWi = computed(() => currentWeekdayIndex())
const nowSi = computed(() => currentSlotIndex(props.plan))
const isNow = computed(() => weekday.value === todayWi.value && slot.value === nowSi.value)

function snapNow() {
  weekday.value = todayWi.value
  slot.value = nowSi.value
}

const buildings = computed(() => listBuildings(props.plan))
const types = computed(() => listTypes(props.plan))

const freeRooms = computed(() =>
  findFreeRooms(props.plan, weekday.value, slot.value, {
    type: typeFilter.value || undefined,
    building: buildingFilter.value || undefined,
  })
)

const totalRoomsInScope = computed(() =>
  props.plan.rooms.filter(r =>
    (!typeFilter.value || r.type === typeFilter.value) &&
    (!buildingFilter.value || r.id.startsWith(buildingFilter.value))
  ).length
)

const freeRatio = computed(() =>
  totalRoomsInScope.value > 0
    ? freeRooms.value.length / totalRoomsInScope.value
    : 0
)

function favIsFree(roomId: string): boolean {
  const r = props.plan.rooms.find(x => x.id === roomId)
  if (!r) return false
  return r.schedule[weekday.value][slot.value] === null
}
</script>

<template>
  <div class="space-y-4">
    <!-- 速选: 现在 + 我的常用教室 -->
    <section v-if="favs.length > 0 || !isNow" class="card p-3">
      <div class="flex items-center gap-2 flex-wrap">
        <button
          @click="snapNow"
          class="pill"
          :class="isNow ? 'pill-active' : 'pill-idle bg-amber-50 text-amber-800 border border-amber-200'"
        >
          🕐 现在
        </button>
        <span v-if="favs.length > 0" class="text-xs text-slate-500 ml-1">我的常用</span>
        <RouterLink
          v-for="id in favs"
          :key="id"
          :to="{ name: 'room', query: { id } }"
          class="pill pill-idle border"
          :class="favIsFree(id)
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
            : 'bg-rose-50 text-rose-700 border-rose-200'"
          :title="favIsFree(id) ? '当前空闲' : '当前占用'"
        >
          <span class="mr-0.5">{{ favIsFree(id) ? '🟢' : '🔴' }}</span>{{ id }}
        </RouterLink>
      </div>
    </section>

    <!-- 周几 -->
    <section class="card p-4">
      <h2 class="text-xs font-medium text-slate-500 mb-2">周几</h2>
      <div class="flex gap-1 overflow-x-auto pb-1 -mx-1 px-1">
        <button
          v-for="(name, i) in plan.meta.weekdays"
          :key="i"
          @click="weekday = i"
          class="pill flex-1 min-w-[2.75rem]"
          :class="[
            weekday === i ? 'pill-active' : 'pill-idle',
            i === todayWi && weekday !== i ? 'ring-1 ring-amber-300' : '',
          ]"
        >
          {{ name.replace('周', '') }}
        </button>
      </div>
    </section>

    <!-- 时段 -->
    <section class="card p-4">
      <h2 class="text-xs font-medium text-slate-500 mb-2">时段</h2>
      <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
        <button
          v-for="(s, i) in plan.meta.slots"
          :key="s.key"
          @click="slot = i"
          class="pill text-center leading-tight"
          :class="[
            slot === i ? 'pill-active' : 'pill-idle bg-slate-100',
            i === nowSi && slot !== i && weekday === todayWi ? 'ring-1 ring-amber-300' : '',
          ]"
        >
          <div>{{ s.label }}<span v-if="i === nowSi && weekday === todayWi" class="ml-0.5">🕐</span></div>
          <div class="text-[9px] opacity-75 tabular-nums">{{ slotTime(s.key) }}</div>
        </button>
      </div>
    </section>

    <!-- 筛选(可折叠) -->
    <section class="card overflow-hidden">
      <button
        @click="showFilters = !showFilters"
        class="w-full px-4 py-3 flex items-center justify-between text-sm text-slate-600 hover:bg-slate-50"
      >
        <span>
          筛选
          <span v-if="typeFilter || buildingFilter" class="ml-2 text-slate-900 font-medium">
            {{ [buildingFilter, typeFilter].filter(Boolean).join(' · ') }}
          </span>
        </span>
        <span class="text-slate-400">{{ showFilters ? '收起' : '展开' }}</span>
      </button>
      <div v-if="showFilters" class="px-4 pb-4 space-y-3 border-t border-slate-100 pt-3">
        <div>
          <h3 class="text-xs font-medium text-slate-500 mb-2">教学楼</h3>
          <div class="flex flex-wrap gap-1.5">
            <button
              @click="buildingFilter = ''"
              class="pill"
              :class="!buildingFilter ? 'pill-active' : 'pill-idle bg-slate-100'"
            >全部</button>
            <button
              v-for="b in buildings"
              :key="b"
              @click="buildingFilter = b"
              class="pill"
              :class="buildingFilter === b ? 'pill-active' : 'pill-idle bg-slate-100'"
            >{{ b }}</button>
          </div>
        </div>
        <div>
          <h3 class="text-xs font-medium text-slate-500 mb-2">类型</h3>
          <div class="flex flex-wrap gap-1.5">
            <button
              @click="typeFilter = ''"
              class="pill"
              :class="!typeFilter ? 'pill-active' : 'pill-idle bg-slate-100'"
            >全部</button>
            <button
              v-for="t in types"
              :key="t"
              @click="typeFilter = t"
              class="pill"
              :class="typeFilter === t ? 'pill-active' : 'pill-idle bg-slate-100'"
            >{{ t }}</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 结果统计 -->
    <div class="flex items-center justify-between px-1 pt-1">
      <div class="text-sm">
        <span class="text-2xl font-bold text-emerald-600">{{ freeRooms.length }}</span>
        <span class="text-slate-500 ml-1">/ {{ totalRoomsInScope }} 间空闲</span>
      </div>
      <div class="text-xs text-slate-500">{{ (freeRatio * 100).toFixed(0) }}% 空闲率</div>
    </div>

    <!-- 教室列表 -->
    <section
      v-if="freeRooms.length === 0"
      class="card p-8 text-center text-slate-500"
    >
      🚫 当前时段没有匹配的空教室
    </section>
    <section v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
      <RouterLink
        v-for="room in freeRooms"
        :key="room.id"
        :to="{ name: 'room', query: { id: room.id } }"
        class="card p-3 hover:shadow-md transition-shadow active:scale-95 relative"
      >
        <span v-if="isFav(room.id)" class="absolute top-1 right-1.5 text-amber-400 text-xs">★</span>
        <div class="font-semibold text-slate-900">{{ room.id }}</div>
        <div class="text-xs text-slate-500 mt-0.5">{{ room.type }}</div>
      </RouterLink>
    </section>
  </div>
</template>
