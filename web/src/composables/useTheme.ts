import { computed, ref } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'theme'

function readSavedMode(): ThemeMode {
  if (typeof window === 'undefined') return 'system'
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw === 'light' || raw === 'dark' || raw === 'system') return raw
  return 'system'
}

function systemPrefersDark(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyDark(dark: boolean) {
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle('dark', dark)
}

const mode = ref<ThemeMode>(readSavedMode())
const systemDark = ref<boolean>(systemPrefersDark())

const isDark = computed(() =>
  mode.value === 'dark' || (mode.value === 'system' && systemDark.value)
)

// 切换主题: 同步写 html.dark + localStorage. 不依赖 watch, 避免模块顶层 watch 的 scope 问题
function commit(m: ThemeMode) {
  mode.value = m
  applyDark(m === 'dark' || (m === 'system' && systemDark.value))
  try { localStorage.setItem(STORAGE_KEY, m) } catch {}
}

// 系统主题变化监听 (只在 system 档时影响显示). 模块加载时注册一次, 不依赖组件生命周期
if (typeof window !== 'undefined') {
  const mql = window.matchMedia('(prefers-color-scheme: dark)')
  const fire = (e: MediaQueryListEvent) => {
    systemDark.value = e.matches
    if (mode.value === 'system') applyDark(e.matches)
  }
  mql.addEventListener('change', fire)
  // index.html 内联脚本已经先一步同步过 html.dark, 这里再保险一次
  applyDark(isDark.value)
}

export function useTheme() {
  return {
    mode,
    isDark,
    setMode: commit,
    cycle() {
      commit(
        mode.value === 'light' ? 'dark'
      : mode.value === 'dark'  ? 'system'
                               : 'light'
      )
    },
  }
}
