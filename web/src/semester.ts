// 已核实的新学期下限；每学期开学时按教务通知更新。
// https://jwc.jxnu.edu.cn/Portal/ArticlesView.aspx?ID=13714
export const REQUIRED_SEMESTER = '26-27第1学期'

function semesterOrder(value: string): number | null {
  const match = value.match(/^(\d{2}|\d{4})-(\d{2}|\d{4})第([12])学期$/)
  if (!match) return null
  const year = Number(match[1]) + (match[1].length === 2 ? 2000 : 0)
  const end = Number(match[2]) + (match[2].length === 2 ? 2000 : 0)
  return end === year + 1 ? year * 2 + Number(match[3]) : null
}

export function isOutdatedSemester(semester: string): boolean {
  const order = semesterOrder(semester)
  return order === null || order < semesterOrder(REQUIRED_SEMESTER)!
}
