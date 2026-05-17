<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { computed } from 'vue'
import { usePlan } from '@/composables/usePlan'

const route = useRoute()
const { plan, loading, error, reload } = usePlan()

const nav = [
  { to: '/', label: '时段空闲', name: 'range' },
  { to: '/room', label: '教室时段', name: 'room' },
  { to: '/heatmap', label: '热力图', name: 'heatmap' }
] as const

const synced = computed(() => {
  if (!plan.value) return ''
  return new Date(plan.value.meta.synced_at).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="bg-white border-b border-slate-200 sticky top-0 z-10">
      <div class="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
        <h1 class="font-bold text-base sm:text-lg whitespace-nowrap text-slate-900">
          <span class="text-slate-400 mr-1">📚</span><span class="hidden sm:inline">江西师范大学</span><span class="sm:hidden">江师大</span>(瑶湖)空教室
        </h1>
        <nav class="flex gap-1 ml-auto overflow-x-auto">
          <RouterLink
            v-for="item in nav"
            :key="item.name"
            :to="item.to"
            class="pill"
            :class="route.name === item.name ? 'pill-active' : 'pill-idle'"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="max-w-3xl mx-auto w-full px-4 py-4 flex-1">
      <div v-if="error" class="card p-6 text-center">
        <p class="text-rose-600 font-medium mb-2">加载失败</p>
        <p class="text-sm text-slate-600 mb-4">{{ error }}</p>
        <button
          @click="reload()"
          class="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-700"
        >重试</button>
      </div>
      <div v-else-if="loading && !plan" class="card p-12 text-center text-slate-500">
        <div class="animate-pulse">数据加载中…</div>
      </div>
      <RouterView v-else-if="plan" :plan="plan" />
    </main>

    <footer class="text-xs text-slate-500 text-center py-6 px-4 max-w-3xl mx-auto">
      <p v-if="plan">
        {{ plan.meta.semester }} · {{ plan.meta.room_count }} 间教室 · 同步于 {{ synced }}
      </p>
      <p class="mt-1 opacity-70">
        数据来源:江西师范大学教务在线 · 仅供参考,临时调课/补课不在此列
      </p>
      <p class="mt-2 opacity-60">
        🤖 本项目由
        <a
          href="https://claude.com/claude-code"
          target="_blank"
          rel="noopener"
          class="underline hover:text-slate-700"
        >Claude Code</a>
        100% 生成 ·
        <a
          href="https://github.com/xmy3/jxnu-classroom"
          target="_blank"
          rel="noopener"
          class="underline hover:text-slate-700"
        >GitHub</a>
      </p>
    </footer>
  </div>
</template>
