"""教务系统 (jwc.jxnu.edu.cn) HTTP 层。

意外发现(2026-05):
  https://jwc.jxnu.edu.cn/MyControl/Public_ClassRoom.aspx?t={1|2}
  这个"教室教学安排简明查询"页面 **无需登录** 即可访问,
  且一次 GET 就拿到本学期全部教室的整周课表 HTML 表格。
  所以爬虫不需要走 CAS 登录(cas.py 保留作为以后高级查询的能力)。

  - t=1: 普通教室
  - t=2: 多媒体教室
  - 编码: gb2312(实际用 gb18030 解码以兼容生僻字)
"""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


PUBLIC_CLASSROOM_URL = "https://jwc.jxnu.edu.cn/MyControl/Public_ClassRoom.aspx"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def make_session() -> requests.Session:
    """构造一个不依赖系统代理、带浏览器 UA 的 Session。"""
    s = requests.Session()
    s.trust_env = False
    s.headers["User-Agent"] = DEFAULT_USER_AGENT
    s.headers["Accept-Language"] = "zh-CN,zh;q=0.9"
    return s


def fetch_public_classroom(
    t: int,
    session: requests.Session | None = None,
    timeout: float = 30.0,
) -> str:
    """GET 一次教室教学安排页,返回已用 gb18030 解码的 HTML 文本。

    Args:
        t: 1 = 普通教室,2 = 多媒体教室
        session: 复用的 requests.Session(可选)
    """
    if t not in (1, 2):
        raise ValueError(f"t 只能是 1 或 2,得到 {t}")

    session = session or make_session()
    url = PUBLIC_CLASSROOM_URL
    params = {"t": t}
    logger.info("GET %s?t=%d", url, t)
    resp = session.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    # 服务器实际用 UTF-8 传输(虽然 HTML meta 写的是 gb2312)
    # 以 Content-Type 头里 charset 为准,否则 fallback 到 utf-8
    encoding = resp.encoding or "utf-8"
    if encoding.lower() in ("iso-8859-1", "ascii"):
        encoding = "utf-8"
    html_text = resp.content.decode(encoding, errors="replace")
    logger.debug("  -> %d bytes / %d chars (decoded as %s)",
                 len(resp.content), len(html_text), encoding)
    return html_text
