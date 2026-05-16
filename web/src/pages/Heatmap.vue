<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Plan } from '@/types'
import { buildingOf, listBuildings } from '@/composables/usePlan'

const props = defineProps<{ plan: Plan }>()

function todayIndex(): number {
  const d = new Date().getDay()
  return d === 0 ? 6 : d - 1
}

const mode = ref<'day' | 'week'>('day')
const weekday = ref<number>(todayIndex())
const buildingFilter = ref<string>('')

const buildings = computed(() => listBuildings(props.plan))

const visibleRooms = computed(() =>
  props.plan.rooms.filter(r =>
    !buildingFilter.value || buildingOf(r.id) === buildingFilter.value
  )
)

// 单元格 → 颜色
function cellClass(occupied: boolean): string {
  return occupied ? 'bg-rose-400' : 'bg-emerald-200/60'
}

// 周视图:每个 cell 是 (room × weekday) 在某 slot 的占用率 0..1
// 实现:对每个 (room, weekday),统计该天 7 时段中占用的数量
function dayBusyness(roomIdx: number, wi: number): number {
  const room = visibleRooms.value[roomIdx]
  let n = 0
  for (let s = 0; s < 7; s++) if (room.schedule[wi][s]) n++
  return n / 7
}

function dayBusynessColor(b: number): string {
  if (b === 0) return 'bg-emerald-200/60'
  if (b < 0.3) return 'bg-amber-200'
  if (b < 0.6) return 'bg-orange-400'
  return 'bg-rose-500'
}
</script>

<template>
  <div class="space-y-4">
    <!-- 模式切换 -->
    <section class="card p-4 space-y-3">
      <div>
        <h2 class="text-xs font-medium text-slate-500 mb-2">视图</h2>
        <div class="flex gap-1.5">
          <button @click="mode = 'day'" class="pill flex-1"
            :class="mode === 'day' ? 'pill-active' : 'pill-idle bg-slate-100'">
            单日:教室 × 时段
          </button>
          <button @click="mode = 'week'" class="pill flex-1"
            :class="mode === 'week' ? 'pill-active' : 'pill-idle bg-slate-100'">
            全周:教室 × 星期
          </button>
        </div>
      </div>
      <div v-if="mode === 'day'">
        <h2 class="text-xs font-medium text-slate-500 mb-2">周几</h2>
        <div class="flex gap-1 overflow-x-auto pb-1">
          <button
            v-for="(name, i) in plan.meta.weekdays"
            :key="i"
            @click="weekday = i"
            class="pill flex-1 min-w-[2.75rem]"
            :class="weekday === i ? 'pill-active' : 'pill-idle bg-slate-100'"
          >{{ name.replace('周', '') }}</button>
        </div>
      </div>
      <div>
        <h2 class="text-xs font-medium text-slate-500 mb-2">教学楼</h2>
        <div class="flex flex-wrap gap-1.5">
          <button @click="buildingFilter = ''" class="pill"
            :class="!buildingFilter ? 'pill-active' : 'pill-idle bg-slate-100'">全部</button>
          <button v-for="b in buildings" :key="b" @click="buildingFilter = b" class="pill"
            :class="buildingFilter === b ? 'pill-active' : 'pill-idle bg-slate-100'">{{ b }}</button>
        </div>
      </div>
    </section>

    <!-- 图例 -->
    <div class="flex items-center gap-3 text-xs text-slate-500 px-1">
      <span class="inline-flex items-center gap-1">
        <span class="w-3 h-3 rounded-sm bg-emerald-200/60"></span> 空闲
      </span>
      <span v-if="mode === 'day'" class="inline-flex items-center gap-1">
        <span class="w-3 h-3 rounded-sm bg-rose-400"></span> 占用
      </span>
      <template v-else>
        <span class="inline-flex items-center gap-1">
          <span class="w-3 h-3 rounded-sm bg-amber-200"></span> &lt;30%
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="w-3 h-3 rounded-sm bg-orange-400"></span> &lt;60%
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="w-3 h-3 rounded-sm bg-rose-500"></span> ≥60%
        </span>
      </template>
      <span class="ml-auto">{{ visibleRooms.length }} 个教室</span>
    </div>

    <!-- 热力网格 -->
    <section class="card p-2 overflow-x-auto">
      <table class="w-full text-[10px]" style="border-collapse: separate; border-spacing: 1px;">
        <thead>
          <tr>
            <th class="sticky left-0 bg-white z-10 px-1 py-0.5 text-slate-500 text-left"></th>
            <template v-if="mode === 'day'">
              <th v-for="(s, i) in plan.meta.slots" :key="i" class="text-slate-500 px-0.5 py-0.5">
                {{ s.label }}
              </th>
            </template>
            <template v-else>
              <th v-for="(w, i) in plan.meta.weekdays" :key="i" class="text-slate-500 px-0.5 py-0.5">
                {{ w.replace('周', '') }}
              </th>
            </template>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(room, ri) in visibleRooms" :key="room.id">
            <td class="sticky left-0 bg-white z-10 pr-1 text-slate-700 whitespace-nowrap text-[10px]">
              {{ room.id }}
            </td>
            <template v-if="mode === 'day'">
              <td
                v-for="(_, si) in plan.meta.slots"
                :key="si"
                class="w-5 h-5 rounded-sm"
                :class="cellClass(room.schedule[weekday][si] !== null)"
                :title="
                  room.schedule[weekday][si]
                    ? `${room.id} ${plan.meta.weekdays[weekday]} ${plan.meta.slots[si].label}\n${room.schedule[weekday][si]!.c} | ${room.schedule[weekday][si]!.t}`
                    : `${room.id} ${plan.meta.weekdays[weekday]} ${plan.meta.slots[si].label} 空闲`
                "
              ></td>
            </template>
            <template v-else>
              <td
                v-for="(_, wi) in plan.meta.weekdays"
                :key="wi"
                class="w-5 h-5 rounded-sm"
                :class="dayBusynessColor(dayBusyness(ri, wi))"
                :title="`${room.id} ${plan.meta.weekdays[wi]} 占用 ${(dayBusyness(ri, wi) * 100).toFixed(0)}%`"
              ></td>
            </template>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
