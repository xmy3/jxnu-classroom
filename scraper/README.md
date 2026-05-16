# scraper — 江西师范大学教务系统爬虫

Python 包,负责 CAS 单点登录 + 抓取教室课表 + 产出 JSON。

## 安装

需要 Python 3.10+。

```bash
cd scraper
python -m venv .venv
.venv\Scripts\activate         # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .
```

国内网络如果慢,可换镜像:

```bash
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置

```bash
cp .env.example .env
# 编辑 .env 填入 JXNU_USERNAME / JXNU_PASSWORD
```

## 验证登录

```bash
jxnu-classroom login --verbose --dump portal.html
```

成功后:
- 控制台会打印每一步的 URL/状态码
- 把登录后的工作台页面保存到 `portal.html`,用于后续接口分析

## 模块结构

| 文件 | 职责 |
|---|---|
| `config.py` | 加载 .env 配置 |
| `cas.py` | CAS 登录(RSA 加密密码 / execution / ticket 回调) |
| `jwc.py` | 教务系统会话与页面适配(进行中) |
| `cli.py` | 命令行入口 |
