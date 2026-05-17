<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Plan } from '@/types'
import {
  findFreeRoomsInRange, listBuildings, listTypes,
  slotTime, slotRangeTime,
  currentSlotIndex, currentWeekdayIndex, useFavorites,
} from '@/composables/usePlan'

const props = defineProps<{ plan: Plan }>()

type Mode = 'range' | 'multi'

const weekday = ref<number>(currentWeekdayIndex())
const mode = ref<Mode>('range')

// 范围模式
const startSlot = ref<number>(currentSlotIndex(props.plan))
const endSlot = ref<number>(currentSlotIndex(props.plan))

// 多选模式 (用 Set 存索引)
const multiSlots = ref<Set<number>>(new Set([currentSlotIndex(props.plan)]))

// 筛选
const typeFilter = ref<string>('')
const buildingFilter = ref<string>('')
const showFilters = ref(false)

const { isFav } = useFavorites()

const todayWi = computed(() => currentWeekdayIndex())

// 当前选中的 slot 索引列表 (排序去重)
const selectedSlots = computed<number[]>(() => {
  if (mode.value === 'range') {
    const a = Math.min(startSlot.value, endSlot.value)
    const b = Math.max(startSlot.value, endSlot.value)
    const out: number[] = []
    for (let i = a; i <= b; i++) out.push(i)
    return out
  }
  return [...multiSlots.value].sort((a, b) => a - b)
})

// 模式切换时,把当前选择带过去
watch(mode, (m, prev) => {
  if (m === prev) return
  if (m === 'multi') {
    // 从 range 切到 multi: 把 [start..end] 平铺成集合
    const a = Math.min(startSlot.value, endSlot.value)
    const b = Math.max(startSlot.value, endSlot.value)
    const out = new Set<number>()
    for (let i = a; i <= b; i++) out.add(i)
    multiSlots.value = out
  } else {
    // 从 multi 切到 range: 取 min/max
    const arr = [...multiSlots.value]
    if (arr.length === 0) {
      const now = currentSlotIndex(props.plan)
      startSlot.value = now
      endSlot.value = now
    } else {
      startSlot.value = Math.min(...arr)
      endSlot.value = Math.max(...arr)
    }
  }
})

function pickStart(i: number) {
  startSlot.value = i
  if (endSlot.value < i) endSlot.value = i
}
function pickEnd(i: number) {
  endSlot.value = i
  if (startSlot.value > i) startSlot.value = i
}

function toggleMulti(i: number) {
  const s = new Set(multiSlots.value)
  if (s.has(i)) s.delete(i)
  else s.add(i)
  multiSlots.value = s
}

function presetMorning() {
  const ids: number[] = []
  props.plan.meta.slots.forEach((s, i) => { if (s.period === '上午') ids.push(i) })
  multiSlots.value = new Set(ids)
}
function presetAfternoon() {
  const ids: number[] = []
  props.plan.meta.slots.forEach((s, i) => { if (s.period === '下午') ids.push(i) })
  multiSlots.value = new Set(ids)
}
function presetEvening() {
  const ids: number[] = []
  props.plan.meta.slots.forEach((s, i) => { if (s.period === '晚上') ids.push(i) })
  multiSlots.value = new Set(ids)
}
function presetAllDay() {
  multiSlots.value = new Set(props.plan.meta.slots.map((_, i) => i))
}
function presetClear() {
  multiSlots.value = new Set()
}

const buildings = computed(() => listBuildings(props.plan))
const types = computed(() => listTypes(props.plan))

const freeRooms = computed(() => findFreeRoomsInRange(
  props.plan, weekday.value, selectedSlots.value,
  {
    type: typeFilter.value || undefined,
    building: buildingFilter.value || undefined,
  },
))

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

const timeRangeLabel = computed(() => slotRangeTime(props.plan, selectedSlots.value))

const selectedLabels = computed(() =>
  selectedSlots.value.map(i => props.plan.meta.slots[i].label).join(' · ')
)
</script>

<template>
  <div class="space-y-4">
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

    <!-- 模式切换 -->
    <section class="card p-4 space-y-3">
      <div>
        <h2 class="text-xs font-medium text-slate-500 mb-2">选择方式</h2>
        <div class="flex gap-1.5">
          <button
            @click="mode = 'range'"
            class="pill flex-1"
            :class="mode === 'range' ? 'pill-active' : 'pill-idle bg-slate-100'"
          >范围 (X→Y 节)</button>
          <button
            @click="mode = 'multi'"
            class="pill flex-1"
            :class="mode === 'multi' ? 'pill-active' : 'pill-idle bg-slate-100'"
          >多选 (任意组合)</button>
        </div>
      </div>

      <!-- 范围模式 -->
      <template v-if="mode === 'range'">
        <div>
          <h3 class="text-xs font-medium text-slate-500 mb-2">起始节次</h3>
          <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
            <button
              v-for="(s, i) in plan.meta.slots"
              :key="s.key"
              @click="pickStart(i)"
              class="pill text-center leading-tight"
              :class="startSlot === i ? 'pill-active' : 'pill-idle bg-slate-100'"
            >
              <div>{{ s.label }}</div>
              <div class="text-[9px] opacity-75 tabular-nums">{{ slotTime(s.key) }}</div>
            </button>
          </div>
        </div>
        <div>
          <h3 class="text-xs font-medium text-slate-500 mb-2">结束节次</h3>
          <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
            <button
              v-for="(s, i) in plan.meta.slots"
              :key="s.key"
              @click="pickEnd(i)"
              :disabled="i < startSlot"
              class="pill text-center leading-tight"
              :class="[
                endSlot === i ? 'pill-active' : 'pill-idle bg-slate-100',
                i < startSlot ? 'opacity-30 cursor-not-allowed' : '',
                i >= startSlot && i <= endSlot && endSlot !== i ? 'ring-1 ring-slate-300' : '',
              ]"
            >
              <div>{{ s.label }}</div>
              <div class="text-[9px] opacity-75 tabular-nums">{{ slotTime(s.key) }}</div>
            </button>
          </div>
        </div>
      </template>

      <!-- 多选模式 -->
      <template v-else>
        <div>
          <h3 class="text-xs font-medium text-slate-500 mb-2">勾选节次</h3>
          <div class="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
            <button
              v-for="(s, i) in plan.meta.slots"
              :key="s.key"
              @click="toggleMulti(i)"
              class="pill text-center leading-tight"
              :class="multiSlots.has(i) ? 'pill-active' : 'pill-idle bg-slate-100'"
            >
              <div>{{ s.label }}</div>
              <div class="text-[9px] opacity-75 tabular-nums">{{ slotTime(s.key) }}</div>
            </button>
          </div>
        </div>
        <div>
          <h3 class="text-xs font-medium text-slate-500 mb-2">快捷</h3>
          <div class="flex flex-wrap gap-1.5">
            <button @click="presetMorning" class="pill pill-idle bg-slate-100">整个上午</button>
            <button @click="presetAfternoon" class="pill pill-idle bg-slate-100">整个下午</button>
            <button @click="presetEvening" class="pill pill-idle bg-slate-100">晚上</button>
            <button @click="presetAllDay" class="pill pill-idle bg-slate-100">全天</button>
            <button
              @click="presetClear"
              class="pill pill-idle bg-rose-50 text-rose-700 hover:bg-rose-100"
            >清空</button>
          </div>
        </div>
      </template>
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

    <!-- 已选时段提示 -->
    <div
      v-if="selectedSlots.length > 0"
      class="text-xs text-slate-500 px-1 flex items-center gap-2 flex-wrap"
    >
      <span class="font-medium text-slate-700">已选 {{ selectedSlots.length }} 节</span>
      <span class="opacity-70">{{ selectedLabels }}</span>
      <span v-if="timeRangeLabel" class="tabular-nums text-slate-400">{{ timeRangeLabel }}</span>
    </div>

    <!-- 结果统计 -->
    <div v-if="selectedSlots.length > 0" class="flex items-center justify-between px-1 pt-1">
      <div class="text-sm">
        <span class="text-2xl font-bold text-emerald-600">{{ freeRooms.length }}</span>
        <span class="text-slate-500 ml-1">/ {{ totalRoomsInScope }} 间全程空闲</span>
      </div>
      <div class="text-xs text-slate-500">{{ (freeRatio * 100).toFixed(0) }}% 空闲率</div>
    </div>

    <!-- 教室列表 -->
    <section
      v-if="selectedSlots.length === 0"
      class="card p-8 text-center text-slate-500"
    >
      请先选择至少一节
    </section>
    <section
      v-else-if="freeRooms.length === 0"
      class="card p-8 text-center text-slate-500"
    >
      🚫 没有在所选时段全部空闲的教室
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
