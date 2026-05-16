import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { copyFileSync, mkdirSync, existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))

function copyClassroomData(): Plugin {
  const src = resolve(__dirname, '../data/classrooms.json')
  const destDir = resolve(__dirname, 'public/data')
  const dest = resolve(destDir, 'classrooms.json')

  function copy() {
    if (!existsSync(src)) {
      console.warn(
        `[copy-data] 源文件不存在: ${src}\n` +
        `  请先在 scraper/ 目录跑: python -m jxnu_classroom.cli sync`
      )
      return
    }
    mkdirSync(destDir, { recursive: true })
    copyFileSync(src, dest)
    console.log(`[copy-data] ${src} -> public/data/classrooms.json`)
  }

  return {
    name: 'copy-classroom-data',
    buildStart() {
      copy()
    },
    configureServer(server) {
      copy()
      server.watcher.add(src)
      server.watcher.on('change', file => {
        if (resolve(file) === src) {
          copy()
          server.ws.send({ type: 'full-reload' })
        }
      })
    }
  }
}

export default defineConfig({
  base: './',
  plugins: [vue(), copyClassroomData()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
