export interface Course {
  /** 课程名称 */
  c: string
  /** 班级名称 */
  l: string
  /** 任课教师 */
  t: string
}

export interface Slot {
  /** "12" | "3" | "4" | "5" | "67" | "89" | "ev" */
  key: string
  /** 显示名,例如 "1-2节" */
  label: string
  /** "上午" | "下午" | "晚上" */
  period: string
}

export interface Room {
  /** 教室号,例如 "W1101" */
  id: string
  /** "多媒体" | "普通" */
  type: string
  /** 7 行(周一..周日) × 7 列(时段),null = 空闲 */
  schedule: (Course | null)[][]
}

export interface PlanMeta {
  semester: string
  synced_at: string
  source: string[]
  weekdays: string[]
  slots: Slot[]
  caveat: string
  room_count: number
}

export interface Plan {
  meta: PlanMeta
  rooms: Room[]
}
