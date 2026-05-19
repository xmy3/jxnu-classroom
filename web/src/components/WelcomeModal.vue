<script setup lang="ts">
import { onMounted, ref } from 'vue'

const STORAGE_KEY = 'welcome-notice-read-v1'

const visible = ref(false)

onMounted(() => {
  try {
    if (localStorage.getItem(STORAGE_KEY) !== '1') visible.value = true
  } catch {
    visible.value = true
  }
})

function dismiss() {
  visible.value = false
  try { localStorage.setItem(STORAGE_KEY, '1') } catch {}
}

function onBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    // 仅允许通过按钮关闭,避免误触
  }
}
</script>

<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="visible"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4
             bg-slate-900/50 dark:bg-black/70 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-title"
      @click="onBackdropClick"
    >
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 scale-95 translate-y-2"
        enter-to-class="opacity-100 scale-100 translate-y-0"
        appear
      >
        <div
          v-if="visible"
          class="card w-full max-w-md p-6 sm:p-7 shadow-xl"
          @click.stop
        >
          <h2
            id="welcome-title"
            class="text-base sm:text-lg font-semibold text-slate-900 dark:text-zinc-100
                   flex items-center gap-2"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round"
                 class="text-amber-500 dark:text-amber-400 shrink-0">
              <path d="M12 9v4M12 17h.01" />
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            </svg>
            使用须知
          </h2>

          <div class="mt-4 space-y-3 text-sm leading-relaxed
                      text-slate-700 dark:text-zinc-300">
            <p>
              本站数据来源于
              <span class="font-medium text-slate-900 dark:text-zinc-100">江西师范大学教务在线</span>
              公共教室查询系统,并按计划定期同步。
            </p>
            <p>
              实际教学过程中, 学期中途<span class="font-medium">临时调换教室或调整上课时间</span>
              的情况较为常见, 而教务系统的公开数据未必能够及时反映这些变更。
            </p>
            <p>
              因此, 本站显示为"空闲"的教室仍可能正在被使用。
              <span class="font-medium text-slate-900 dark:text-zinc-100">请以现场实际情况为准</span>,
              并留意辅导员或任课教师发布的最新通知。
            </p>
          </div>

          <div class="mt-6 flex justify-end">
            <button
              type="button"
              @click="dismiss"
              class="px-4 py-2 rounded-lg text-sm font-medium
                     bg-slate-900 text-white hover:bg-slate-700
                     dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300
                     focus:outline-none focus:ring-2 focus:ring-offset-2
                     focus:ring-slate-500 dark:focus:ring-zinc-400
                     dark:focus:ring-offset-zinc-900
                     transition-colors"
            >
              我已知晓, 不再提示
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>
