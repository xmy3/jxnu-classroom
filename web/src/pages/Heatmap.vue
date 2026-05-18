<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import type { Plan, Room } from '@/types'
import {
  buildingOf, listBuildings, slotTime,
  currentSlotIndex, currentWeekdayIndex,
} from '@/composables/usePlan'

const props = defineProps<{ plan: Plan }>()

const mode = ref<'day' | 'week'>('day')
const weekday = ref<number>(currentWeekdayIndex())
const buildingFilter = ref<string>('')

const todayWi = computed(() => currentWeekdayIndex())
const isToday = computed(() => weekday.value === todayWi.value)
const nowSi = computed(() => currentSlotIndex(props.plan))

const buildings = computed(() => listBuildings(props.plan))

const visibleRooms = computed(() =>
  props.plan.rooms.filter(r =>
    !buildingFilter.value || buildingOf(r.id) === buildingFilter.value
  )
)

const groups = computed<{ b: string; rooms: Room[] }[]>(() => {
  const map = new Map<string, Room[]>()
  for (const r of visibleRooms.value) {
    const b = buildingOf(r.id)
    if (!map.has(b)) map.set(b, [])
    map.get(b)!.push(r)
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([b, rooms]) => ({ b, rooms }))
})

const colCount = computed(() =>
  mode.value === 'day' ? props.plan.meta.slots.length : 7
)

// 一个 cell 的占用强度 [0, 1]
//   单日:占=1 / 空=0(二态)
//   全周:看该教室在 ci=星期 一整天的占用比例
function cellBusy(room: Room, ci: number): number {
  if (mode.value === 'day') {
    return room.schedule[weekday.value][ci] === null ? 0 : 1
  }
  let n = 0
  for (let s = 0; s < 7; s++) if (room.schedule[ci][s]) n++
  return n / 7
}

// 单元格背景色:统一 indigo 系
//   单日 0/1 二态;全周 0..1 五档
function cellBg(room: Room, ci: number): string {
  const b = cellBusy(room, ci)
  if (mode.value === 'day') {
    return b > 0
      ? 'bg-indigo-500 dark:bg-indigo-400'
      : 'bg-slate-200/70 dark:bg-zinc-700/50'
  }
  if (b === 0)   return 'bg-slate-200/70 dark:bg-zinc-700/50'
  if (b <= 0.2)  return 'bg-indigo-200 dark:bg-indigo-900'
  if (b <= 0.4)  return 'bg-indigo-300 dark:bg-indigo-700'
  if (b <= 0.6)  return 'bg-indigo-400 dark:bg-indigo-500'
  if (b <= 0.8)  return 'bg-indigo-600 dark:bg-indigo-400'
  return              'bg-indigo-800 dark:bg-indigo-200'
}

// 一间教室在当前视图下的占用格数
function busyCount(room: Room): number {
  if (mode.value === 'day') {
    let n = 0
    for (let s = 0; s < 7; s++) if (room.schedule[weekday.value][s]) n++
    return n
  }
  let n = 0
  for (let w = 0; w < 7; w++) for (let s = 0; s < 7; s++) if (room.schedule[w][s]) n++
  return n
}

function totalSlotCount(): number {
  return mode.value === 'day' ? 7 : 49
}

function freeCountOfRoom(room: Room): number {
  return totalSlotCount() - busyCount(room)
}

// 一个 "全天空" 的教室
function isAllFree(room: Room): boolean {
  return busyCount(room) === 0
}

// 卡片色系:全天空 → 翠绿;否则跟随占用程度
function cardTone(room: Room): string {
  if (isAllFree(room)) {
    return 'bg-emerald-50/80 border-emerald-200 hover:border-emerald-400 dark:bg-emerald-950/40 dark:border-emerald-800/70 dark:hover:border-emerald-600'
  }
  return 'bg-white border-slate-200 hover:border-indigo-400 dark:bg-zinc-900 dark:border-zinc-800 dark:hover:border-indigo-500'
}

// 顶部 KPI
const totalRooms = computed(() => visibleRooms.value.length)
const totalCells = computed(() => totalRooms.value * 7)
const totalBusy = computed(() => {
  if (totalRooms.value === 0) return 0
  let n = 0
  for (const r of visibleRooms.value) {
    if (mode.value === 'day') {
      for (let s = 0; s < 7; s++) if (r.schedule[weekday.value][s]) n++
    } else {
      for (let w = 0; w < 7; w++) for (let s = 0; s < 7; s++) if (r.schedule[w][s]) n++
    }
  }
  return n
})
const totalAll = computed(() => mode.value === 'day' ? totalCells.value : totalCells.value * 7)
const totalFree = computed(() => totalAll.value - totalBusy.value)
const occupancyRate = computed(() =>
  totalAll.value === 0 ? 0 : totalBusy.value / totalAll.value
)
const allFreeRooms = computed(() => visibleRooms.value.filter(isAllFree).length)

// 顶部 pulse:每列(单日=节次,全周=星期)的总占用率
const pulse = computed<number[]>(() => {
  const arr = new Array(colCount.value).fill(0)
  if (totalRooms.value === 0) return arr
  for (let c = 0; c < colCount.value; c++) {
    let n = 0
    for (const r of visibleRooms.value) {
      if (mode.value === 'day') {
        if (r.schedule[weekday.value][c]) n++
      } else {
        for (let s = 0; s < 7; s++) if (r.schedule[c][s]) n++
      }
    }
    arr[c] = mode.value === 'day' ? n / totalRooms.value : n / (totalRooms.value * 7)
  }
  return arr
})

const peakColIndex = computed(() => {
  if (pulse.value.length === 0) return -1
  let max = -1, idx = -1
  pulse.value.forEach((v, i) => { if (v > max) { max = v; idx = i } })
  return max > 0 ? idx : -1
})

const peakLabel = computed(() => {
  const i = peakColIndex.value
  if (i < 0) return ''
  return mode.value === 'day'
    ? props.plan.meta.slots[i].label
    : props.plan.meta.weekdays[i]
})

// 楼栋统计
function groupBusy(rooms: Room[]): number {
  let n = 0
  for (const r of rooms) {
    if (mode.value === 'day') {
      for (let s = 0; s < 7; s++) if (r.schedule[weekday.value][s]) n++
    } else {
      for (let w = 0; w < 7; w++) for (let s = 0; s < 7; s++) if (r.schedule[w][s]) n++
    }
  }
  return n
}
function groupTotal(rooms: Room[]): number {
  return rooms.length * totalSlotCount()
}
function groupFree(rooms: Room[]): number {
  return groupTotal(rooms) - groupBusy(rooms)
}
function groupRate(rooms: Room[]): number {
  const t = groupTotal(rooms)
  return t === 0 ? 0 : groupBusy(rooms) / t
}
function groupAllFree(rooms: Room[]): number {
  return rooms.filter(isAllFree).length
}

// tooltip 文字
function cellTitle(room: Room, ci: number): string {
  if (mode.value === 'day') {
    const s = props.plan.meta.slots[ci]
    const c = room.schedule[weekday.value][ci]
    return c
      ? `${room.id} ${s.label} ${slotTime(s.key)}\n${c.c} | ${c.t}`
      : `${room.id} ${s.label} ${slotTime(s.key)} · 空闲`
  }
  return `${room.id} ${props.plan.meta.weekdays[ci]} · 占 ${(cellBusy(room, ci) * 100).toFixed(0)}%`
}

// 单日:在每节课色带上,上午/下午/晚上之间留视觉间隙
function isPeriodBreakDay(ci: number): boolean {
  if (mode.value !== 'day') return false
  const cur = props.plan.meta.slots[ci]?.period
  const next = props.plan.meta.slots[ci + 1]?.period
  return !!cur && !!next && cur !== next
}

// 楼栋小节奏:7 格 mini 摘要(单日=7 节课总占用率,全周=7 天总占用率)
function groupPulse(rooms: Room[]): number[] {
  const arr = new Array(7).fill(0)
  if (rooms.length === 0) return arr
  for (let c = 0; c < 7; c++) {
    let n = 0
    for (const r of rooms) {
      if (mode.value === 'day') {
        if (r.schedule[weekday.value][c]) n++
      } else {
        for (let s = 0; s < 7; s++) if (r.schedule[c][s]) n++
      }
    }
    arr[c] = mode.value === 'day' ? n / rooms.length : n / (rooms.length * 7)
  }
  return arr
}
function pulseBg(v: number): string {
  if (v === 0)   return 'bg-slate-200/70 dark:bg-zinc-700/50'
  if (v <= 0.2)  return 'bg-indigo-200 dark:bg-indigo-900'
  if (v <= 0.4)  return 'bg-indigo-300 dark:bg-indigo-700'
  if (v <= 0.6)  return 'bg-indigo-400 dark:bg-indigo-500'
  if (v <= 0.8)  return 'bg-indigo-600 dark:bg-indigo-400'
  return              'bg-indigo-800 dark:bg-indigo-200'
}
</script>

<template>
  <!-- ============== Hero ============== -->
  <section class="mb-5 sm:mb-6">
    <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-zinc-100 tracking-tight">
      热力图
    </h1>
    <p class="text-sm text-slate-500 dark:text-zinc-400 mt-1.5">
      <template v-if="mode === 'day'">
        <span v-if="isToday" class="inline-flex items-center gap-1">
          <span class="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
          <span class="text-amber-700 dark:text-amber-300 font-medium">今天</span>
        </span>
        <span v-else>{{ plan.meta.weekdays[weekday] }}</span>
        <span class="mx-1 text-slate-300 dark:text-zinc-700">·</span>
        <span>每间教室一整天的忙闲一眼看完</span>
      </template>
      <template v-else>
        <span>这周全部教室 × 周一到周日 的整体节奏</span>
      </template>
    </p>

    <!-- KPI 大卡片:不对称编辑式排版 -->
    <div
      v-if="totalRooms > 0"
      class="mt-4 sm:mt-6 relative overflow-hidden rounded-2xl border border-slate-200 dark:border-zinc-800
             bg-gradient-to-br from-white via-slate-50 to-emerald-50/40
             dark:from-zinc-900 dark:via-zinc-900 dark:to-emerald-950/30
             px-5 sm:px-8 py-5 sm:py-7"
    >
      <!-- 装饰圆 -->
      <div class="absolute -top-24 -right-24 w-64 h-64 rounded-full bg-emerald-200/30 dark:bg-emerald-500/10 blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-20 -left-20 w-56 h-56 rounded-full bg-indigo-200/20 dark:bg-indigo-500/10 blur-3xl pointer-events-none"></div>

      <div class="relative flex flex-col sm:flex-row sm:items-end gap-5 sm:gap-8">
        <!-- 主数字:全天空闲 -->
        <div class="flex-1 min-w-0">
          <div class="text-[10px] sm:text-[11px] uppercase tracking-[0.2em] font-semibold text-emerald-600/80 dark:text-emerald-400/80 mb-1">
            {{ mode === 'day' ? '此刻全天空' : '本周空闲格' }}
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-6xl sm:text-7xl font-bold text-emerald-600 dark:text-emerald-300 tabular-nums leading-[0.85] tracking-tight">
              {{ mode === 'day' ? allFreeRooms : totalFree }}
            </span>
            <span class="text-base sm:text-lg text-slate-500 dark:text-zinc-400 font-medium pb-1">
              {{ mode === 'day' ? '间' : '格' }}
            </span>
          </div>
          <div class="mt-2 text-xs sm:text-sm text-slate-500 dark:text-zinc-400 tabular-nums">
            <span v-if="mode === 'day'">
              共 {{ totalRooms }} 间 · 占
              <span class="tabular-nums font-semibold text-slate-700 dark:text-zinc-200">{{ Math.round(allFreeRooms / totalRooms * 100) }}%</span>
            </span>
            <span v-else>
              共 {{ totalAll }} 格 · 空
              <span class="tabular-nums font-semibold text-slate-700 dark:text-zinc-200">{{ Math.round((1 - occupancyRate) * 100) }}%</span>
            </span>
          </div>
        </div>

        <!-- 右侧两个小指标 -->
        <div class="grid grid-cols-2 gap-5 sm:gap-7 sm:pl-7 sm:border-l sm:border-slate-200/70 sm:dark:border-zinc-800">
          <!-- 占用率 -->
          <div>
            <div class="text-[10px] sm:text-[11px] uppercase tracking-[0.2em] font-semibold text-slate-400 dark:text-zinc-500 mb-1">
              整体占用
            </div>
            <div class="flex items-baseline gap-1">
              <span class="text-3xl sm:text-4xl font-bold text-indigo-600 dark:text-indigo-300 tabular-nums leading-none">
                {{ Math.round(occupancyRate * 100) }}
              </span>
              <span class="text-sm text-slate-500 dark:text-zinc-400 font-medium">%</span>
            </div>
            <div class="w-full h-1 rounded-full bg-slate-100 dark:bg-zinc-800 overflow-hidden mt-2">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="occupancyRate <= 0.4 ? 'bg-emerald-400 dark:bg-emerald-500'
                  : occupancyRate <= 0.7 ? 'bg-indigo-400 dark:bg-indigo-400'
                  : 'bg-rose-400 dark:bg-rose-400'"
                :style="{ width: `${occupancyRate * 100}%` }"
              ></div>
            </div>
          </div>
          <!-- 最忙 -->
          <div v-if="peakColIndex >= 0">
            <div class="text-[10px] sm:text-[11px] uppercase tracking-[0.2em] font-semibold text-slate-400 dark:text-zinc-500 mb-1">
              最忙{{ mode === 'day' ? '节次' : '一天' }}
            </div>
            <div class="flex items-baseline gap-1.5">
              <span class="text-3xl sm:text-4xl font-bold text-rose-500 dark:text-rose-400 tabular-nums leading-none">
                {{ peakLabel.replace('周', '') }}
              </span>
              <span class="text-xs text-rose-400/80 dark:text-rose-400/70 tabular-nums font-semibold">{{ Math.round(pulse[peakColIndex] * 100) }}%</span>
            </div>
            <div v-if="mode === 'day'" class="text-[11px] text-slate-400 dark:text-zinc-500 tabular-nums mt-2">
              {{ slotTime(plan.meta.slots[peakColIndex].key) }}
            </div>
            <div v-else class="text-[11px] text-slate-400 dark:text-zinc-500 mt-2">
              最高占用日
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ============== 控制条 ============== -->
  <section class="mb-5 flex flex-col sm:flex-row sm:items-center gap-3">
    <!-- 模式切换 -->
    <div class="flex gap-1 bg-slate-100 dark:bg-zinc-800 rounded-lg p-0.5 shrink-0">
      <button
        @click="mode = 'day'"
        class="px-3 py-1.5 rounded-md text-xs transition-colors"
        :class="mode === 'day'
          ? 'bg-white text-slate-900 dark:bg-zinc-700 dark:text-zinc-100 font-medium shadow-sm'
          : 'text-slate-600 dark:text-zinc-400'"
      >单日</button>
      <button
        @click="mode = 'week'"
        class="px-3 py-1.5 rounded-md text-xs transition-colors"
        :class="mode === 'week'
          ? 'bg-white text-slate-900 dark:bg-zinc-700 dark:text-zinc-100 font-medium shadow-sm'
          : 'text-slate-600 dark:text-zinc-400'"
      >全周</button>
    </div>
    <!-- 周几切换 -->
    <div v-if="mode === 'day'" class="flex gap-0.5 -mx-1 px-1 overflow-x-auto sm:mx-0 sm:px-0 shrink-0">
      <button
        v-for="(name, i) in plan.meta.weekdays"
        :key="i"
        @click="weekday = i"
        class="px-2.5 py-1.5 rounded-md text-xs whitespace-nowrap transition-colors"
        :class="[
          weekday === i
            ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900 font-medium'
            : i === todayWi
              ? 'text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-900/20'
              : 'text-slate-600 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-800',
        ]"
      >{{ name.replace('周', '') }}<span v-if="i === todayWi && weekday !== i" class="ml-0.5 text-[10px] opacity-70">·今</span></button>
    </div>
    <!-- 楼栋筛选 -->
    <div class="flex flex-wrap items-center gap-1 sm:ml-auto">
      <button
        @click="buildingFilter = ''"
        class="text-[11px] px-2 py-1 rounded transition-colors"
        :class="!buildingFilter
          ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
          : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'"
      >全部</button>
      <button
        v-for="b in buildings"
        :key="b"
        @click="buildingFilter = b"
        class="text-[11px] px-2 py-1 rounded transition-colors"
        :class="buildingFilter === b
          ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
          : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700'"
      >{{ b }}</button>
    </div>
  </section>

  <!-- ============== Pulse 节奏条 ============== -->
  <section v-if="visibleRooms.length > 0" class="mb-6 sm:mb-7">
    <div class="flex items-baseline justify-between mb-3">
      <h2 class="text-[11px] uppercase tracking-widest font-medium text-slate-400 dark:text-zinc-500">
        {{ mode === 'day' ? '今日节奏' : '本周节奏' }}
      </h2>
      <span class="text-[10px] text-slate-400 dark:text-zinc-500">
        颜色越深越忙 · 数字 = 占用率%
      </span>
    </div>
    <div class="flex items-end gap-1.5 sm:gap-2 h-20">
      <template v-for="(v, ci) in pulse" :key="ci">
        <div
          class="flex-1 flex flex-col items-center gap-1.5 min-w-0"
          :class="isPeriodBreakDay(ci) ? 'mr-1.5 sm:mr-3' : ''"
        >
          <span
            class="text-[11px] tabular-nums leading-none font-medium"
            :class="ci === peakColIndex
              ? 'text-rose-500 dark:text-rose-400'
              : v > 0
                ? 'text-slate-500 dark:text-zinc-400'
                : 'text-slate-300 dark:text-zinc-600'"
          >{{ Math.round(v * 100) }}</span>
          <div class="w-full flex flex-col justify-end" style="height: 44px;">
            <div
              class="w-full rounded-md transition-all"
              :class="[
                pulseBg(v),
                mode === 'day' && isToday && ci === nowSi
                  ? 'ring-2 ring-amber-400 dark:ring-amber-300 ring-offset-1 ring-offset-white dark:ring-offset-zinc-950'
                  : '',
              ]"
              :style="{ height: `${Math.max(6, v * 44)}px` }"
              :title="(mode === 'day'
                ? plan.meta.slots[ci].label + ' ' + slotTime(plan.meta.slots[ci].key)
                : plan.meta.weekdays[ci]) + ' · ' + (v*100).toFixed(0) + '%'"
            ></div>
          </div>
          <span
            class="text-[10px] leading-none truncate w-full text-center"
            :class="mode === 'day' && isToday && ci === nowSi
              ? 'text-amber-700 dark:text-amber-300 font-semibold'
              : 'text-slate-500 dark:text-zinc-400'"
          >
            {{ mode === 'day' ? plan.meta.slots[ci].label : plan.meta.weekdays[ci].replace('周', '') }}
          </span>
        </div>
      </template>
    </div>
  </section>

  <!-- ============== 楼栋分组 ============== -->
  <section v-if="visibleRooms.length === 0" class="card p-10 text-center text-slate-500 dark:text-zinc-400">
    <p>没有匹配的教室</p>
  </section>

  <div v-else class="space-y-8 sm:space-y-10">
    <section v-for="g in groups" :key="g.b">
      <!-- 楼栋 header -->
      <header class="flex items-center justify-between mb-4 sm:mb-5 gap-3">
        <div class="flex items-center gap-3 sm:gap-4 min-w-0">
          <!-- 楼栋徽章 -->
          <div
            class="flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 rounded-2xl shrink-0
                   text-base sm:text-lg font-bold tabular-nums tracking-wider
                   bg-gradient-to-br shadow-sm"
            :class="groupAllFree(g.rooms) === g.rooms.length
              ? 'from-emerald-500 to-emerald-600 text-white dark:from-emerald-500 dark:to-emerald-600'
              : groupRate(g.rooms) > 0.7
                ? 'from-rose-500 to-rose-600 text-white dark:from-rose-500 dark:to-rose-600'
                : 'from-slate-800 to-slate-900 text-white dark:from-zinc-100 dark:to-zinc-300 dark:text-zinc-900'"
          >
            {{ g.b }}
          </div>
          <div class="min-w-0">
            <div class="flex items-baseline gap-1.5 text-sm sm:text-base">
              <span class="tabular-nums font-bold text-slate-900 dark:text-zinc-100">{{ g.rooms.length }}</span>
              <span class="text-slate-500 dark:text-zinc-400">间教室</span>
            </div>
            <div class="text-[11px] sm:text-xs text-slate-500 dark:text-zinc-400 tabular-nums mt-0.5">
              <span class="font-semibold text-emerald-600 dark:text-emerald-400">{{ groupAllFree(g.rooms) }}</span>
              <span class="mx-0.5">全空</span>
              <span class="mx-1.5 text-slate-300 dark:text-zinc-700">·</span>
              <span class="font-semibold"
                :class="groupRate(g.rooms) > 0.7
                  ? 'text-rose-500 dark:text-rose-400'
                  : 'text-indigo-600 dark:text-indigo-300'"
              >{{ Math.round(groupRate(g.rooms) * 100) }}%</span>
              <span class="ml-0.5">占用</span>
            </div>
          </div>
        </div>
        <!-- 楼栋 mini 节奏 -->
        <div class="hidden md:flex items-center gap-2 shrink-0">
          <span class="text-[10px] uppercase tracking-[0.18em] text-slate-400 dark:text-zinc-500">
            {{ mode === 'day' ? '本日节奏' : '本周节奏' }}
          </span>
          <div class="flex items-end gap-[3px]">
            <template v-for="(v, i) in groupPulse(g.rooms)" :key="i">
              <div
                class="w-2.5 rounded-sm transition-colors"
                :class="pulseBg(v)"
                :style="{ height: `${Math.max(6, v * 24)}px` }"
                :title="(mode === 'day'
                  ? plan.meta.slots[i]?.label
                  : plan.meta.weekdays[i]) + ' · ' + (v*100).toFixed(0) + '%'"
              ></div>
              <span
                v-if="isPeriodBreakDay(i)"
                class="w-1 shrink-0"
                aria-hidden="true"
              ></span>
            </template>
          </div>
        </div>
      </header>

      <!-- 教室卡片网格 -->
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5 sm:gap-3">
        <RouterLink
          v-for="room in g.rooms"
          :key="room.id"
          :to="{ name: 'room', query: { id: room.id } }"
          class="group relative rounded-xl border p-3 sm:p-3.5 transition-all hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0"
          :class="cardTone(room)"
          :title="isAllFree(room) ? `${room.id} · 全天空` : `${room.id} · ${busyCount(room)}/${totalSlotCount()} 占用`"
        >
          <!-- 教室号 + 占用比 -->
          <div class="flex items-baseline justify-between mb-2.5">
            <span
              class="font-bold text-base sm:text-lg tabular-nums tracking-tight leading-none"
              :class="isAllFree(room)
                ? 'text-emerald-700 dark:text-emerald-300'
                : 'text-slate-900 dark:text-zinc-100'"
            >{{ room.id }}</span>
            <span
              v-if="isAllFree(room)"
              class="text-[10px] font-bold uppercase tracking-wider text-emerald-600/90 dark:text-emerald-400/90
                     bg-emerald-100/80 dark:bg-emerald-900/50 px-1.5 py-0.5 rounded"
            >全空</span>
            <span
              v-else
              class="text-[11px] tabular-nums text-slate-400 dark:text-zinc-500 leading-none"
            >
              <span class="text-slate-700 dark:text-zinc-200 font-semibold">{{ freeCountOfRoom(room) }}</span>
              <span class="opacity-60">/{{ totalSlotCount() }}</span>
            </span>
          </div>
          <!-- 节次/星期 色带 -->
          <div class="flex items-center gap-[3px]">
            <template v-for="ci in colCount" :key="ci - 1">
              <div
                class="flex-1 h-4 sm:h-5 rounded-sm transition-colors"
                :class="[
                  cellBg(room, ci - 1),
                  mode === 'day' && isToday && (ci - 1) === nowSi
                    ? 'ring-2 ring-amber-400 dark:ring-amber-300 ring-offset-1 ring-offset-white dark:ring-offset-zinc-900 z-10 relative'
                    : '',
                ]"
                :title="cellTitle(room, ci - 1)"
              ></div>
              <span
                v-if="isPeriodBreakDay(ci - 1)"
                class="w-1 shrink-0"
                aria-hidden="true"
              ></span>
            </template>
          </div>
        </RouterLink>
      </div>
    </section>
  </div>
</template>
