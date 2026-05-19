# 江西师范大学(瑶湖校区)空教室

> 江西师范大学(瑶湖校区)空闲教室查询 — 纯静态 Web 应用,数据来自教务在线公开页面。
> 覆盖瑶湖校区惟义楼(W1–W7)共 200+ 间公共教室。
>
> 🤖 **本项目由 [Claude Code](https://claude.com/claude-code) 100% 生成**(从需求分析、爬虫、前端到部署脚本)。

## ✨ 功能

- **教室列表**:选时段 + 教学楼 + 类型,列出此刻空闲的教室;移动端默认折叠筛选,首屏直达
- **课表查询**:查某间教室一周的完整课表,点击单元格查看课程/班级/教师详情
- **占用热力图**:全校教室一整周的占用密度可视化,带图例与节次基线对齐
- **暗色主题**:明亮 / 暗黑 / 跟随系统三档切换,偏好保存到本地
- **首次使用须知**:进入站点首次弹出数据时效性提示,点击"已知晓"后不再打扰
- **轻量增强**:收藏教室、当前节次高亮、"现在"快捷按钮 — 都存浏览器本地,无后端

## 🏗️ 架构

```
┌────────────────────────────────────────────────┐
│  GitHub Actions(每日 06:17 CST)                │
│    └─ scraper/ Python 包                        │
│         GET jwc.jxnu.edu.cn/MyControl/          │
│         Public_ClassRoom.aspx?t=1|2             │
│         → 解析 → data/classrooms.json           │
│         → git commit & push                     │
└────────────────────────────────────────────────┘
                  │ push to main
                  ▼
┌────────────────────────────────────────────────┐
│  GitHub Pages(自动构建)                         │
│    └─ web/  Vue 3 + Vite + Tailwind            │
│         读 data/classrooms.json 做查询          │
└────────────────────────────────────────────────┘
```

- 🆓 **零成本**:GitHub Actions(2000 分钟/月免费)+ GitHub Pages(免费托管)
- ⚡ **极致轻量**:gzip 后 JS ≈ 55 KB + CSS ≈ 8 KB + 数据 ≈ 80 KB
- 🔓 **无需登录**:数据源 `Public_ClassRoom.aspx` 公开可访问,**完全不存任何用户凭证**
- 🌐 **手机优先**:Tailwind 响应式,主要面向手机查询场景

## 📁 目录

```
classroom/
├── scraper/                     # Python 爬虫(同步数据)
│   ├── jxnu_classroom/
│   │   ├── cas.py              # CAS 登录(预留,主路径用不到)
│   │   ├── jwc.py              # HTTP 抓取
│   │   ├── parser.py           # HTML → 数据结构
│   │   ├── builder.py          # 结构 → JSON
│   │   └── cli.py              # 命令行入口
│   └── tests/                  # 离线 smoke 测试
├── data/
│   └── classrooms.json         # 爬虫产物,前端 fetch 之
├── web/                         # Vue 3 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── RangeFree.vue       # 教室列表(空闲查询)
│   │   │   ├── RoomTimeline.vue    # 课表查询
│   │   │   └── Heatmap.vue         # 占用热力图
│   │   ├── components/
│   │   │   ├── BrandMark.vue       # 品牌色块图标
│   │   │   └── WelcomeModal.vue    # 首次使用须知弹窗
│   │   ├── composables/
│   │   │   ├── usePlan.ts          # 数据加载 + 查询
│   │   │   └── useTheme.ts         # 明/暗/跟随系统 主题切换
│   │   └── App.vue
│   └── package.json
└── .github/workflows/
    ├── sync.yml                # 每日抓数据
    └── deploy.yml              # 推 main 自动部署
```

## 🚀 本地开发

### 1. 同步数据(可选,repo 已带最新一份)

```powershell
cd scraper
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python -m jxnu_classroom.cli sync -v
# → 生成 ../data/classrooms.json
```

### 2. 跑前端

```powershell
cd web
npm install
npm run dev
# → http://localhost:5173/
```

Vite 配置了热重载 watcher:每次 scraper 重新生成 `data/classrooms.json`,前端自动刷新。

### 3. 构建生产版本

```powershell
cd web
npm run build
# → web/dist/  (可以直接静态托管)
```

## 🌍 部署

### GitHub Pages(推荐,零配置)

1. Fork 或 push 这个 repo 到 GitHub
2. Settings → Pages → Source 选 **GitHub Actions**
3. 推一次 main,`.github/workflows/deploy.yml` 自动构建并发布
4. 访问 `https://<用户名>.github.io/<仓库名>/`(用了 hash 路由,刷新不会 404)

### Cloudflare Pages

1. 在 Cloudflare Pages 新建项目,连接 GitHub repo
2. 配置:
   - Build command: `cd web && npm install && npm run build`
   - Build output: `web/dist`
3. 推 main 自动部署,带自定义域名

### 自动同步(GitHub Actions)

`.github/workflows/sync.yml` 每天北京时间 06:17 自动跑爬虫并 commit 数据。
也可以在 GitHub UI **Actions → Sync classroom data → Run workflow** 手动触发。

无需任何 secret —— 数据源是公开页面。

## ⚠️ 数据说明

- 数据反映**本学期常规课表**,即教务系统"教室教学安排简明查询"的内容
- 临时调课、补课、考试、会议等占用 **不在此列**
- 学期中途临调教室或时间的情况较为常见,且教务系统未必及时反映,**请以现场实际情况为准**
- 实际去教室前建议口头确认,工具用于初筛
- 如果同步爬虫遇到页面结构变化,会在 GitHub Actions 报错通知

## 🤝 贡献

PR / Issue 都欢迎。改 UI 直接动 `web/src/pages/`,改数据结构联动改 `scraper/jxnu_classroom/builder.py` 和 `web/src/types.ts`。
