import { ref, computed, shallowRef } from 'vue'
import type { Plan, Room, Course } from '@/types'

const _plan = shallowRef<Plan | null>(null)
const _loading = ref(false)
const _error = ref<string | null>(null)
let _loadPromise: Promise<Plan> | null = null

const DATA_URL = `${import.meta.env.BASE_URL}data/classrooms.json`

function startLoad(): Promise<Plan> {
  if (_loadPromise) return _loadPromise
  _loading.value = true
  _error.value = null
  _loadPromise = fetch(DATA_URL)
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status} 从 ${DATA_URL} 加载数据失败`)
      return r.json() as Promise<Plan>
    })
    .then(data => {
      _plan.value = data
      return data
    })
    .catch(err => {
      _error.value = String(err.message ?? err)
      _plan.value = null
      _loadPromise = null
      throw err
    })
    .finally(() => {
      _loading.value = false
    })
  return _loadPromise
}

export function usePlan() {
  if (!_plan.value && !_loadPromise) startLoad()
  return {
    plan: _plan,
    loading: _loading,
    error: _error,
    ready: computed(() => _plan.value !== null),
    reload() {
      _loadPromise = null
      _plan.value = null
      return startLoad()
    }
  }
}

// 从教室 id 推断建筑编号(W1101 -> "W1",W2201 -> "W2"),
// 在江西师大命名里,W 后第 1 位数字代表教学楼组。
export function buildingOf(id: string): string {
  const m = id.match(/^([A-Z]\d)/)
  return m ? m[1] : id.slice(0, 2)
}

export function listBuildings(plan: Plan): string[] {
  const set = new Set<string>()
  for (const r of plan.rooms) set.add(buildingOf(r.id))
  return [...set].sort()
}

export function listTypes(plan: Plan): string[] {
  const set = new Set<string>()
  for (const r of plan.rooms) set.add(r.type)
  return [...set].sort()
}

export interface RoomFilter {
  type?: string
  building?: string
}

function matchFilter(r: Room, f: RoomFilter): boolean {
  if (f.type && r.type !== f.type) return false
  if (f.building && buildingOf(r.id) !== f.building) return false
  return true
}

/** 给定 (weekday, slot),返回当前空闲教室 */
export function findFreeRooms(
  plan: Plan, weekday: number, slot: number, f: RoomFilter = {}
): Room[] {
  return plan.rooms.filter(
    r => matchFilter(r, f) && r.schedule[weekday][slot] === null
  )
}

/** 给定 (weekday, slot),返回当前被占用的教室 + 占用信息 */
export function findOccupiedRooms(
  plan: Plan, weekday: number, slot: number, f: RoomFilter = {}
): Array<{ room: Room; course: Course }> {
  const out: Array<{ room: Room; course: Course }> = []
  for (const room of plan.rooms) {
    if (!matchFilter(room, f)) continue
    const c = room.schedule[weekday][slot]
    if (c) out.push({ room, course: c })
  }
  return out
}
