/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts,js}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'Inter',
          '"Noto Sans SC"',
          '-apple-system', 'BlinkMacSystemFont',
          '"Segoe UI"', '"PingFang SC"', '"Microsoft YaHei"',
          'system-ui', 'sans-serif'
        ],
        num: [
          'Inter',
          '-apple-system', 'BlinkMacSystemFont',
          'system-ui', 'sans-serif'
        ]
      }
    }
  },
  plugins: []
}
