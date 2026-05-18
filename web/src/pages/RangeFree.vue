<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Plan } from '@/types'
import {
  findRoomsInRangeWithStatus, listBuildings,
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
const buildingFilter = ref<string>('')
const showFilters = ref(false)
// 是否只看空闲教室;关闭时显示全部教室,用颜色区分
const onlyFree = ref<boolean>(false)

// 手机端默认折叠左侧筛选,避免首屏被筛选框塞满
const mobileFiltersOpen = ref(false)

const { isFav } = useFavorites()

const todayWi = computed(() => currentWeekdayIndex())
const isToday = computed(() => weekday.value === todayWi.value)

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
    const a = Math.min(startSlot.value, endSlot.value)
    const b = Math.max(startSlot.value, endSlot.value)
    const out = new Set<number>()
    for (let i = a; i <= b; i++) out.add(i)
    multiSlots.value = out
  } else {
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

const allRooms = computed(() => findRoomsInRangeWithStatus(
  props.plan, weekday.value, selectedSlots.value,
  { building: buildingFilter.value || undefined },
))

const freeRooms = computed(() => allRooms.value.filter(r => r.free))

const displayRooms = computed(() =>
  onlyFree.value ? freeRooms.value : allRooms.value
)

const totalRoomsInScope = computed(() => allRooms.value.length)

const freeRatio = computed(() =>
  totalRoomsInScope.value > 0
    ? freeRooms.value.length / totalRoomsInScope.value
    : 0
)

const timeRangeLabel = computed(() => slotRangeTime(props.plan, selectedSlots.value))

const selectedLabels = computed(() =>
  selectedSlots.value.map(i => props.plan.meta.slots[i].label).join(' · ')
)

const weekdayLabel = computed(() => props.plan.meta.weekdays[weekday.value])
</script>

<template>
  <!-- 主问句区:让人第一眼明白这页是干嘛的 -->
  <section class="mb-5 sm:mb-6">
    <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-zinc-100 tracking-tight">
      {{ isToday ? '今天' : weekdayLabel }}哪些教室是空的?
    </h1>
    <p class="text-sm text-slate-500 dark:text-zinc-400 mt-1.5 flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
      <span v-if="isToday" class="inline-flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
        <span class="text-amber-700 dark:text-amber-300">实时</span>
      </span>
      <span v-if="isToday" class="text-slate-300 dark:text-zinc-700">·</span>
      <template v-if="selectedSlots.length">
        <span>{{ selectedLabels }}</span>
        <span v-if="timeRangeLabel" class="text-slate-400 dark:text-zinc-500 tabular-nums">({{ timeRangeLabel }})</span>
      </template>
      <span v-else>请展开下方筛选选择节次</span>
    </p>
  </section>

  <!-- 手机端:折叠筛选触发按钮(lg 以下显示) -->
  <button
    @click="mobileFiltersOpen = !mobileFiltersOpen"
    class="lg:hidden w-full mb-3 flex items-center justify-between gap-3 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm hover:bg-slate-50 dark:hover:bg-zinc-800/50 transition-colors"
  >
    <span class="flex items-center gap-2 text-sm font-medium text-slate-900 dark:text-zinc-100 shrink-0">
      <svg viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 text-slate-400 dark:text-zinc-500">
        <path d="M2.628 1.601C5.028 1.206 7.49 1 10 1s4.973.206 7.372.601a.75.75 0 01.628.74v2.288a2.25 2.25 0 01-.659 1.59l-4.682 4.683a2.25 2.25 0 00-.659 1.59v3.037c0 .684-.31 1.33-.844 1.757l-1.937 1.55A.75.75 0 018 18.25v-5.757a2.25 2.25 0 00-.659-1.591L2.659 6.22A2.25 2.25 0 012 4.629V2.34a.75.75 0 01.628-.74z" />
      </svg>
      <span>{{ mobileFiltersOpen ? '收起筛选' : '调整筛选' }}</span>
    </span>
    <span class="flex items-center gap-2 text-xs text-slate-500 dark:text-zinc-400 min-w-0">
      <span class="truncate">
        {{ weekdayLabel }} · {{ selectedSlots.length ? selectedLabels : '未选' }}
      </span>
      <svg
        viewBox="0 0 20 20" fill="currentColor"
        class="w-4 h-4 shrink-0 text-slate-400 dark:text-zinc-500 transition-transform"
        :class="mobileFiltersOpen ? 'rotate-180' : ''"
      >
        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.06l3.71-3.83a.75.75 0 011.08 1.04l-4.25 4.39a.75.75 0 01-1.08 0L5.21 8.27a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
      </svg>
    </span>
  </button>

  <!-- 双栏:lg+ 左 320 控制 / 右 结果 -->
  <div class="lg:grid lg:grid-cols-[20rem_minmax(0,1fr)] lg:gap-6 space-y-4 lg:space-y-0">
    <!-- 左:控制面板 (手机端默认折叠) -->
    <aside
      class="space-y-3 lg:sticky lg:top-16 lg:self-start lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto lg:pr-1"
      :class="mobileFiltersOpen ? 'block' : 'hidden lg:block'"
    >
      <!-- 周几 -->
      <section class="card p-3 sm:p-4">
        <h2 class="text-xs font-medium text-slate-500 dark:text-zinc-400 mb-2">周几</h2>
        <div class="grid grid-cols-7 gap-1">
          <button
            v-for="(name, i) in plan.meta.weekdays"
            :key="i"
            @click="weekday = i"
            class="py-1.5 rounded-md text-xs transition-colors"
            :class="[
              weekday === i
                ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-medium'
                : i === todayWi
                  ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-200 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-300 dark:ring-amber-700/50 dark:hover:bg-amber-900/50'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-800',
            ]"
          >
            {{ name.replace('周', '') }}
          </button>
        </div>
      </section>

      <!-- 模式 + 节次 -->
      <section class="card p-3 sm:p-4 space-y-3">
        <div>
          <h2 class="text-xs font-medium text-slate-500 dark:text-zinc-400 mb-2">选择方式</h2>
          <div class="flex gap-1 bg-slate-100 dark:bg-zinc-800 rounded-lg p-0.5">
            <button
              @click="mode = 'range'"
              class="flex-1 py-1.5 rounded-md text-xs transition-colors"
              :class="mode === 'range' ? 'bg-white text-slate-900 dark:bg-zinc-700 dark:text-zinc-100 font-medium shadow-sm' : 'text-slate-600 dark:text-zinc-400'"
            >范围 X→Y</button>
            <button
              @click="mode = 'multi'"
              class="flex-1 py-1.5 rounded-md text-xs transition-colors"
              :class="mode === 'multi' ? 'bg-white text-slate-900 dark:bg-zinc-700 dark:text-zinc-100 font-medium shadow-sm' : 'text-slate-600 dark:text-zinc-400'"
            >多选</button>
          </div>
        </div>

        <!-- 范围模式 -->
        <template v-if="mode === 'range'">
          <div>
            <h3 class="text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1.5">起始节次</h3>
            <div class="grid grid-cols-4 gap-1">
              <button
                v-for="(s, i) in plan.meta.slots"
                :key="s.key"
                @click="pickStart(i)"
                class="py-1 rounded-md text-xs leading-tight transition-colors"
                :class="startSlot === i
                  ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-medium'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'"
              >
                <div>{{ s.label }}</div>
                <div class="text-[9px] opacity-70 tabular-nums">{{ slotTime(s.key) }}</div>
              </button>
            </div>
          </div>
          <div>
            <h3 class="text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1.5">结束节次</h3>
            <div class="grid grid-cols-4 gap-1">
              <button
                v-for="(s, i) in plan.meta.slots"
                :key="s.key"
                @click="pickEnd(i)"
                :disabled="i < startSlot"
                class="py-1 rounded-md text-xs leading-tight transition-colors"
                :class="[
                  endSlot === i
                    ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-medium'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700',
                  i < startSlot ? 'opacity-30 cursor-not-allowed' : '',
                  i > startSlot && i < endSlot ? 'ring-1 ring-slate-300 dark:ring-zinc-600' : '',
                ]"
              >
                <div>{{ s.label }}</div>
                <div class="text-[9px] opacity-70 tabular-nums">{{ slotTime(s.key) }}</div>
              </button>
            </div>
          </div>
        </template>

        <!-- 多选模式 -->
        <template v-else>
          <div>
            <h3 class="text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1.5">勾选节次</h3>
            <div class="grid grid-cols-4 gap-1">
              <button
                v-for="(s, i) in plan.meta.slots"
                :key="s.key"
                @click="toggleMulti(i)"
                class="py-1 rounded-md text-xs leading-tight transition-colors"
                :class="multiSlots.has(i)
                  ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-medium'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'"
              >
                <div>{{ s.label }}</div>
                <div class="text-[9px] opacity-70 tabular-nums">{{ slotTime(s.key) }}</div>
              </button>
            </div>
          </div>
          <div class="flex flex-wrap gap-1">
            <button @click="presetMorning" class="text-[11px] px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-zinc-800 dark:hover:bg-zinc-700 dark:text-zinc-300">整个上午</button>
            <button @click="presetAfternoon" class="text-[11px] px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-zinc-800 dark:hover:bg-zinc-700 dark:text-zinc-300">整个下午</button>
            <button @click="presetEvening" class="text-[11px] px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-zinc-800 dark:hover:bg-zinc-700 dark:text-zinc-300">晚上</button>
            <button @click="presetAllDay" class="text-[11px] px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-zinc-800 dark:hover:bg-zinc-700 dark:text-zinc-300">全天</button>
            <button @click="presetClear" class="text-[11px] px-2 py-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:hover:bg-rose-900/50 dark:text-rose-300">清空</button>
          </div>
        </template>
      </section>

      <!-- 筛选(可折叠) -->
      <section class="card overflow-hidden">
        <button
          @click="showFilters = !showFilters"
          class="w-full px-3 sm:px-4 py-2.5 flex items-center justify-between text-xs text-slate-600 dark:text-zinc-400 hover:bg-slate-50 dark:hover:bg-zinc-800/50"
        >
          <span class="font-medium text-slate-500 dark:text-zinc-400">
            筛选
            <span v-if="buildingFilter" class="ml-1 text-slate-900 dark:text-zinc-100 font-medium">
              · {{ buildingFilter }}
            </span>
          </span>
          <span class="text-slate-400 dark:text-zinc-500">{{ showFilters ? '收起' : '展开' }}</span>
        </button>
        <div v-if="showFilters" class="px-3 sm:px-4 pb-3 sm:pb-4 space-y-3 border-t border-slate-100 dark:border-zinc-800 pt-3">
          <div>
            <h3 class="text-xs font-medium text-slate-500 dark:text-zinc-400 mb-1.5">教学楼</h3>
            <div class="flex flex-wrap gap-1">
              <button
                @click="buildingFilter = ''"
                class="text-[11px] px-2 py-1 rounded transition-colors"
                :class="!buildingFilter ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'"
              >全部</button>
              <button
                v-for="b in buildings"
                :key="b"
                @click="buildingFilter = b"
                class="text-[11px] px-2 py-1 rounded transition-colors"
                :class="buildingFilter === b ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'"
              >{{ b }}</button>
            </div>
          </div>
        </div>
      </section>
    </aside>

    <!-- 右:结果 -->
    <div>
      <!-- 空状态 -->
      <section
        v-if="selectedSlots.length === 0"
        class="card p-10 text-center text-slate-500 dark:text-zinc-400"
      >
        <div class="text-3xl mb-2 opacity-40">👈</div>
        <p>请在左侧勾选你想查的节次</p>
      </section>

      <template v-else>
        <!-- 大号空闲数 banner -->
        <div class="mb-3 flex items-baseline gap-2.5 px-0.5">
          <span class="text-4xl sm:text-5xl font-bold text-emerald-600 dark:text-emerald-400 tabular-nums leading-none">
            {{ freeRooms.length }}
          </span>
          <div class="text-sm text-slate-500 dark:text-zinc-400 leading-tight">
            <div class="font-medium text-slate-700 dark:text-zinc-300">间空闲</div>
            <div class="text-xs tabular-nums">/ {{ totalRoomsInScope }} 间 · {{ (freeRatio * 100).toFixed(0) }}%</div>
          </div>
        </div>

        <!-- 全部 / 只看空闲 切换 -->
        <div class="flex items-center justify-between mb-3 px-0.5">
          <div class="flex gap-1 bg-slate-100 dark:bg-zinc-800 rounded-lg p-0.5">
            <button
              @click="onlyFree = false"
              class="px-3 py-1.5 rounded-md text-xs transition-colors"
              :class="!onlyFree ? 'bg-white text-slate-900 dark:bg-zinc-700 dark:text-zinc-100 font-medium shadow-sm' : 'text-slate-600 dark:text-zinc-400'"
            >全部 {{ totalRoomsInScope }}</button>
            <button
              @click="onlyFree = true"
              class="px-3 py-1.5 rounded-md text-xs transition-colors"
              :class="onlyFree ? 'bg-white text-slate-900 dark:bg-zinc-700 dark:text-zinc-100 font-medium shadow-sm' : 'text-slate-600 dark:text-zinc-400'"
            >只看空闲 {{ freeRooms.length }}</button>
          </div>
          <!-- 图例 -->
          <div v-if="!onlyFree" class="flex items-center gap-3 text-[11px] text-slate-500 dark:text-zinc-400">
            <span class="inline-flex items-center gap-1">
              <span class="w-2.5 h-2.5 rounded-sm bg-emerald-200 dark:bg-emerald-700/60"></span>空闲
            </span>
            <span class="inline-flex items-center gap-1">
              <span class="w-2.5 h-2.5 rounded-sm bg-rose-200 dark:bg-rose-700/60"></span>占用
            </span>
          </div>
        </div>

        <section
          v-if="displayRooms.length === 0"
          class="card p-10 text-center"
        >
          <p class="text-slate-700 dark:text-zinc-200 font-medium">
            {{ onlyFree ? '该时段所有教室都在上课' : '该范围内没有教室' }}
          </p>
          <p class="text-sm text-slate-500 dark:text-zinc-400 mt-1">
            {{ onlyFree ? '试试切到"全部"或换个时段、教学楼' : '试试放宽教学楼筛选' }}
          </p>
        </section>

        <!-- 教室方块:绿色=空闲,红色=占用 -->
        <section v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-2.5">
          <RouterLink
            v-for="item in displayRooms"
            :key="item.room.id"
            :to="{ name: 'room', query: { id: item.room.id } }"
            :title="item.free
              ? `${item.room.id} · 空闲`
              : `${item.room.id} · ${item.occupiedCount}/${item.totalCount} 节有课${item.firstCourse ? '\n' + item.firstCourse.c : ''}`"
            class="relative rounded-lg p-3 transition-all active:scale-95 border hover:shadow-sm"
            :class="item.free
              ? 'bg-emerald-50 border-emerald-200 hover:bg-emerald-100 hover:border-emerald-300 dark:bg-emerald-950/60 dark:border-emerald-800/60 dark:hover:bg-emerald-900/70 dark:hover:border-emerald-700'
              : 'bg-rose-50 border-rose-200 hover:bg-rose-100 hover:border-rose-300 dark:bg-rose-950/60 dark:border-rose-800/60 dark:hover:bg-rose-900/70 dark:hover:border-rose-700'"
          >
            <span
              v-if="isFav(item.room.id)"
              class="absolute top-1 right-1.5 text-amber-400 text-xs"
            >★</span>
            <div
              class="font-semibold"
              :class="item.free
                ? 'text-emerald-900 dark:text-emerald-100'
                : 'text-rose-900 dark:text-rose-100'"
            >{{ item.room.id }}</div>
            <div
              v-if="item.free"
              class="text-[11px] mt-0.5 text-emerald-700/70 dark:text-emerald-400/80"
            >空闲</div>
            <div
              v-else
              class="text-[11px] mt-0.5 text-rose-700/80 dark:text-rose-300/80 truncate"
            >
              <template v-if="item.totalCount > 1">{{ item.occupiedCount }}/{{ item.totalCount }} 节 ·</template>
              <span v-if="item.firstCourse">{{ item.firstCourse.c }}</span>
              <span v-else>有课</span>
            </div>
          </RouterLink>
        </section>
      </template>
    </div>
  </div>
</template>
