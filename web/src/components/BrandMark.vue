<script setup lang="ts">
defineProps<{
  size?: number
  loading?: boolean
}>()
</script>

<template>
  <span
    class="brand-mark inline-block align-middle"
    :class="loading ? 'is-loading' : 'is-static'"
    :style="{ width: (size ?? 20) + 'px', height: (size ?? 20) + 'px' }"
    aria-hidden="true"
  >
    <svg viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
      <!-- 左上、右上、左下、右下 -->
      <rect class="cell cell-0" x="1"  y="1"  width="8" height="8" rx="1.5" />
      <rect class="cell cell-1" x="11" y="1"  width="8" height="8" rx="1.5" />
      <rect class="cell cell-2" x="1"  y="11" width="8" height="8" rx="1.5" />
      <rect class="cell cell-3" x="11" y="11" width="8" height="8" rx="1.5" />
    </svg>
  </span>
</template>

<style scoped>
.brand-mark svg { width: 100%; height: 100%; display: block; }

/* 静态态: 右上格子(cell-1)是品牌绿色,其余灰色 */
.is-static .cell        { fill: rgb(203 213 225); } /* slate-300 */
.is-static .cell-1      { fill: rgb(16 185 129); }  /* emerald-500 */
:global(.dark) .is-static .cell   { fill: rgb(63 63 70); }   /* zinc-700 */
:global(.dark) .is-static .cell-1 { fill: rgb(52 211 153); } /* emerald-400 */

/* 加载态: 四格依次亮起 (1.6s 一轮) */
.is-loading .cell {
  fill: rgb(203 213 225);
  animation: brand-pulse 1.6s ease-in-out infinite;
}
:global(.dark) .is-loading .cell { fill: rgb(63 63 70); }

.is-loading .cell-0 { animation-delay: 0s; }
.is-loading .cell-1 { animation-delay: .2s; }
.is-loading .cell-3 { animation-delay: .4s; }
.is-loading .cell-2 { animation-delay: .6s; }

@keyframes brand-pulse {
  0%, 70%, 100% { fill: rgb(203 213 225); }
  25%, 45%      { fill: rgb(16 185 129); }
}
:global(.dark) .is-loading .cell {
  animation-name: brand-pulse-dark;
}
@keyframes brand-pulse-dark {
  0%, 70%, 100% { fill: rgb(63 63 70); }
  25%, 45%      { fill: rgb(52 211 153); }
}

@media (prefers-reduced-motion: reduce) {
  .is-loading .cell { animation: none; }
}
</style>
