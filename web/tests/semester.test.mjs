import { test } from 'node:test'
import assert from 'node:assert/strict'
import { isOutdatedSemester } from '../src/semester.ts'

test('旧学期不能作为当前空教室依据', () => {
  assert.equal(isOutdatedSemester('25-26第2学期'), true)
  assert.equal(isOutdatedSemester('26-27第1学期'), false)
  assert.equal(isOutdatedSemester('26-27第2学期'), false)
  assert.equal(isOutdatedSemester('27-28第1学期'), false)
})

test('缺失或无效学期不能放行，支持完整年份', () => {
  for (const value of ['', '未知学期', '26-27第3学期', '26-28第1学期']) {
    assert.equal(isOutdatedSemester(value), true)
  }
  assert.equal(isOutdatedSemester('2025-2026第2学期'), true)
  assert.equal(isOutdatedSemester('2026-2027第1学期'), false)
})
