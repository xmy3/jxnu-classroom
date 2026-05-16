<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Plan } from '@/types'
import { findFreeRooms, listBuildings, listTypes } from '@/composables/usePlan'

const props = defineProps<{ plan: Plan }>()

// 默认今天(JS getDay 周日=0,周一=1...;我们的 weekdays 周一=0)
function todayIndex(): number {
  const d = new Date().getDay()
  return d === 0 ? 6 : d - 1
}

const weekday = ref<number>(todayIndex())
const slot = ref<number>(0)
const typeFilter = ref<string>('')
const buildingFilter = ref<string>('')
const showFilters = ref(false)

const buildings = computed(() => listBuildings(props.plan))
const types = computed(() => listTypes(props.plan))

const freeRooms = computed(() =>
  findFreeRooms(props.plan, weekday.value, slot.value, {
    type: typeFilter.value || undefined,
    building: buildingFilter.value || undefined
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
          :class="weekday === i ? 'pill-active' : 'pill-idle'"
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
          class="pill text-center"
          :class="slot === i ? 'pill-active' : 'pill-idle bg-slate-100'"
        >
          {{ s.label }}
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
        class="card p-3 hover:shadow-md transition-shadow active:scale-95"
      >
        <div class="font-semibold text-slate-900">{{ room.id }}</div>
        <div class="text-xs text-slate-500 mt-0.5">{{ room.type }}</div>
      </RouterLink>
    </section>
  </div>
</template>
