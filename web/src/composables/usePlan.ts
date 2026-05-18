import { ref, computed, shallowRef, onMounted, onUnmounted } from 'vue'
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

// 节次 -> 上课时间(江西师范大学瑶湖校区作息),用于在节次旁附时间。
// 合并规则:连堂取首节开始 + 末节结束;晚上覆盖 10-12 节。
const SLOT_TIME_RANGES: Record<string, [string, string]> = {
  '12': ['08:00', '09:30'],
  '3':  ['09:40', '10:20'],
  '4':  ['10:30', '11:10'],
  '5':  ['11:20', '12:00'],
  '67': ['14:00', '15:30'],
  '89': ['15:40', '17:10'],
  'ev': ['19:00', '21:20'],
}

export function slotTime(key: string): string {
  const r = SLOT_TIME_RANGES[key]
  return r ? `${r[0]}-${r[1]}` : ''
}

function toMin(hhmm: string): number {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

/** 当前 weekday 索引(周一=0...周日=6) */
export function currentWeekdayIndex(now: Date = new Date()): number {
  const d = now.getDay()
  return d === 0 ? 6 : d - 1
}

/**
 * 现在落在 plan.meta.slots 的哪一节?
 * - 落在某 slot 时间段内 → 返回该 slot 的索引
 * - 早于第 1 节 → 返回 0(默认引导到上午第一节)
 * - 在两节之间 → 返回下一节的索引(更贴近“接下来去上课”的语义)
 * - 晚于最后一节 → 返回最后一节索引
 */
export function currentSlotIndex(plan: Plan, now: Date = new Date()): number {
  const mins = now.getHours() * 60 + now.getMinutes()
  const slots = plan.meta.slots
  for (let i = 0; i < slots.length; i++) {
    const r = SLOT_TIME_RANGES[slots[i].key]
    if (!r) continue
    const start = toMin(r[0]), end = toMin(r[1])
    if (mins < start) return i // 早于该节开始 → 选该节
    if (mins <= end) return i  // 正在上课
  }
  return slots.length - 1
}

/** 收藏教室(localStorage) */
const FAV_KEY = 'jxnu-fav-rooms'
const _favs = ref<string[]>(readFavs())

function readFavs(): string[] {
  try {
    const raw = localStorage.getItem(FAV_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr.filter(x => typeof x === 'string') : []
  } catch {
    return []
  }
}

function writeFavs(list: string[]): void {
  try { localStorage.setItem(FAV_KEY, JSON.stringify(list)) } catch {}
}

// 跨 tab/窗口同步
function onStorage(e: StorageEvent) {
  if (e.key === FAV_KEY) _favs.value = readFavs()
}

export function useFavorites() {
  onMounted(() => window.addEventListener('storage', onStorage))
  onUnmounted(() => window.removeEventListener('storage', onStorage))
  return {
    favs: computed(() => _favs.value),
    isFav: (id: string) => _favs.value.includes(id),
    toggle(id: string) {
      const i = _favs.value.indexOf(id)
      const next = i >= 0
        ? _favs.value.filter(x => x !== id)
        : [..._favs.value, id]
      _favs.value = next
      writeFavs(next)
    },
    remove(id: string) {
      _favs.value = _favs.value.filter(x => x !== id)
      writeFavs(_favs.value)
    },
  }
}

// 从教室 id 推断建筑编号(W1101 -> "W1",W2201 -> "W2"),
// 在江西师范大学命名里,W 后第 1 位数字代表教学楼组。
export function buildingOf(id: string): string {
  const m = id.match(/^([A-Z]\d)/)
  return m ? m[1] : id.slice(0, 2)
}

export function listBuildings(plan: Plan): string[] {
  const set = new Set<string>()
  for (const r of plan.rooms) set.add(buildingOf(r.id))
  return [...set].sort()
}

export interface RoomFilter {
  building?: string
}

function matchFilter(r: Room, f: RoomFilter): boolean {
  if (f.building && buildingOf(r.id) !== f.building) return false
  return true
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

/** 给定 (weekday, slots[]),返回在所有给定 slots 都空闲的教室 */
export function findFreeRoomsInRange(
  plan: Plan, weekday: number, slots: number[], f: RoomFilter = {}
): Room[] {
  if (slots.length === 0) return []
  return plan.rooms.filter(
    r => matchFilter(r, f) && slots.every(si => r.schedule[weekday][si] === null)
  )
}

export interface RoomStatus {
  room: Room
  /** 选中节次中被占用的节次数 */
  occupiedCount: number
  /** 选中节次总数 */
  totalCount: number
  /** 整段都空闲 */
  free: boolean
  /** 第一节被占用的课程,用作卡片预览 */
  firstCourse: Course | null
}

/** 给定 (weekday, slots[]),返回所有教室及其在该范围内的占用状态 */
export function findRoomsInRangeWithStatus(
  plan: Plan, weekday: number, slots: number[], f: RoomFilter = {}
): RoomStatus[] {
  if (slots.length === 0) return []
  const out: RoomStatus[] = []
  for (const room of plan.rooms) {
    if (!matchFilter(room, f)) continue
    let occupiedCount = 0
    let firstCourse: Course | null = null
    for (const si of slots) {
      const c = room.schedule[weekday][si]
      if (c) {
        occupiedCount++
        if (!firstCourse) firstCourse = c
      }
    }
    out.push({
      room,
      occupiedCount,
      totalCount: slots.length,
      free: occupiedCount === 0,
      firstCourse,
    })
  }
  return out
}

/** 把一组节次索引格式化为"14:00-21:20"形式的总时间区间 */
export function slotRangeTime(plan: Plan, slots: number[]): string {
  if (slots.length === 0) return ''
  const sorted = [...slots].sort((a, b) => a - b)
  const first = SLOT_TIME_RANGES[plan.meta.slots[sorted[0]].key]
  const last = SLOT_TIME_RANGES[plan.meta.slots[sorted[sorted.length - 1]].key]
  if (!first || !last) return ''
  return `${first[0]}-${last[1]}`
}
