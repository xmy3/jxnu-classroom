"""配置加载。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class JxnuConfig:
    username: str
    password: str
    cas_base: str = "https://uis.jxnu.edu.cn/cas"
    jwc_base: str = "https://jwc.jxnu.edu.cn"
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "JxnuConfig":
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
            scraper_env = Path(__file__).resolve().parent.parent / ".env"
            if scraper_env.exists():
                load_dotenv(scraper_env, override=False)

        username = os.environ.get("JXNU_USERNAME", "").strip()
        password = os.environ.get("JXNU_PASSWORD", "")
        if not username or not password:
            raise RuntimeError(
                "缺少 JXNU_USERNAME 或 JXNU_PASSWORD。"
                "请把 scraper/.env.example 复制为 scraper/.env 并填入账号密码。"
            )
        return cls(username=username, password=password)
