<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { computed } from 'vue'
import { usePlan } from '@/composables/usePlan'
import { useTheme } from '@/composables/useTheme'
import BrandMark from '@/components/BrandMark.vue'

const route = useRoute()
const { plan, loading, error, reload } = usePlan()
const { mode, cycle } = useTheme()

const nav = [
  { to: '/', label: '教室列表', name: 'range' },
  { to: '/room', label: '课表查询', name: 'room' },
  { to: '/heatmap', label: '热力图', name: 'heatmap' }
] as const

const synced = computed(() => {
  if (!plan.value) return ''
  return new Date(plan.value.meta.synced_at).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
})

const themeLabel = computed(() =>
  mode.value === 'light' ? '当前: 明亮 · 点击切到暗色'
  : mode.value === 'dark' ? '当前: 暗黑 · 点击跟随系统'
  : '当前: 跟随系统 · 点击切到明亮'
)
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="bg-white/95 dark:bg-zinc-950/90 backdrop-blur
                   border-b border-slate-200 dark:border-zinc-800 sticky top-0 z-50">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 h-12 flex items-center gap-3">
        <RouterLink to="/"
          class="font-semibold text-sm sm:text-base text-slate-900 dark:text-zinc-100
                 flex items-center gap-2 shrink-0">
          <BrandMark :size="20" :loading="loading && !plan" />
          <span class="hidden sm:inline">江师大瑶湖 · 空教室</span>
          <span class="sm:hidden">空教室</span>
        </RouterLink>
        <nav class="flex gap-0.5 ml-auto overflow-x-auto">
          <RouterLink
            v-for="item in nav"
            :key="item.name"
            :to="item.to"
            class="px-3 py-1.5 rounded-md text-sm whitespace-nowrap transition-colors"
            :class="route.name === item.name
              ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
              : 'text-slate-600 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-800'"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <button
          type="button"
          @click="cycle()"
          :title="themeLabel"
          :aria-label="themeLabel"
          class="shrink-0 w-8 h-8 -mr-1 inline-flex items-center justify-center rounded-md
                 text-slate-500 hover:bg-slate-100 hover:text-slate-900
                 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100
                 transition-colors"
        >
          <!-- 明亮: 太阳 -->
          <svg v-if="mode === 'light'" width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
          </svg>
          <!-- 暗黑: 月亮 -->
          <svg v-else-if="mode === 'dark'" width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
          <!-- 跟随系统: 显示器 -->
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="4" width="20" height="14" rx="2" />
            <path d="M8 22h8M12 18v4" />
          </svg>
        </button>
      </div>
    </header>

    <main class="max-w-6xl mx-auto w-full px-4 sm:px-6 py-4 sm:py-6 flex-1">
      <div v-if="error" class="card p-6 text-center">
        <p class="text-rose-600 dark:text-rose-400 font-medium mb-2">加载失败</p>
        <p class="text-sm text-slate-600 dark:text-zinc-400 mb-4">{{ error }}</p>
        <button
          @click="reload()"
          class="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-700
                 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >重试</button>
      </div>
      <div v-else-if="loading && !plan" class="card p-12 text-center text-slate-500 dark:text-zinc-400">
        <div class="flex flex-col items-center gap-3">
          <BrandMark :size="32" :loading="true" />
          <span class="text-sm">数据加载中…</span>
        </div>
      </div>
      <RouterView v-else-if="plan" :plan="plan" />
    </main>

    <footer class="text-xs text-slate-500 dark:text-zinc-500 text-center py-6 px-4 max-w-6xl mx-auto w-full">
      <p v-if="plan">
        {{ plan.meta.semester }} · 共 {{ plan.meta.room_count }} 间公共教室 · 数据更新于 {{ synced }}
      </p>
      <p class="mt-1 opacity-70">
        以教务在线公共教室查询为准 · 临时调/补课请以辅导员通知为准
      </p>
      <p class="mt-2 opacity-60">
        由
        <a
          href="https://claude.com/claude-code"
          target="_blank"
          rel="noopener"
          class="underline hover:text-slate-700 dark:hover:text-zinc-300"
        >Claude Code</a>
        生成 ·
        <a
          href="https://github.com/xmy3/jxnu-classroom"
          target="_blank"
          rel="noopener"
          class="underline hover:text-slate-700 dark:hover:text-zinc-300"
        >GitHub</a>
      </p>
    </footer>
  </div>
</template>
