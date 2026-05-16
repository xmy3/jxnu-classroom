/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system', 'BlinkMacSystemFont',
          '"Segoe UI"', '"PingFang SC"', '"Microsoft YaHei"',
          'system-ui', 'sans-serif'
        ]
      }
    }
  },
  plugins: []
}
