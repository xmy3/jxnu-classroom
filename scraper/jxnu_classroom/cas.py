"""江西师范大学统一身份认证 (CAS) 登录。

技术细节(2026-05 调研):
  - CAS 服务端: https://uis.jxnu.edu.cn/cas (Apereo CAS + 自定义主题)
  - 公钥端点:  GET  /cas/jwt/publicKey  (匿名,返回 PEM)
  - 密码加密:  RSA-PKCS1v1.5,密文 = "__RSA__" + base64(...)
  - 验证码:    失败次数 >= 5 才触发(captchaSkipN=5),前 5 次免验证码
  - 完整流程:  JWC SSO 入口 -> CAS 登录页 -> POST -> ticket 回调 -> JWC portal
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from lxml import html as lxml_html

from .config import JxnuConfig


logger = logging.getLogger(__name__)


class CasLoginError(RuntimeError):
    """CAS 登录失败。"""


@dataclass
class CasLoginResult:
    session: requests.Session
    portal_url: str
    portal_html: str

    @property
    def session_cookies(self) -> dict[str, str]:
        return {c.name: c.value for c in self.session.cookies}


def fetch_public_key(session: requests.Session, cas_base: str) -> bytes:
    url = f"{cas_base}/jwt/publicKey"
    logger.debug("GET %s", url)
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    pem = resp.text.strip().encode("ascii")
    serialization.load_pem_public_key(pem)
    return pem


def encrypt_password(plain: str, public_key_pem: bytes) -> str:
    public_key = serialization.load_pem_public_key(public_key_pem)
    cipher = public_key.encrypt(plain.encode("utf-8"), padding.PKCS1v15())
    return "__RSA__" + base64.b64encode(cipher).decode("ascii")


def _extract_password_form_fields(login_html: str) -> dict[str, str]:
    """从密码登录表单 fm1 抽 hidden 字段。"""
    tree = lxml_html.fromstring(login_html)
    forms = tree.xpath('//form[@id="fm1"]')
    if not forms:
        raise CasLoginError("CAS 登录页结构变化:找不到 form#fm1")

    out: dict[str, str] = {}
    for inp in forms[0].xpath('.//input'):
        name = inp.get("name")
        if not name or inp.get("type") == "submit":
            continue
        # checkbox 默认不勾选 -> 不发送
        if inp.get("type") == "checkbox":
            continue
        out[name] = inp.get("value") or ""
    return out


def _build_jwc_sso_url(jwc_base: str, target_url: str) -> str:
    """江西师范大学私有的 SSO 入口 URL 格式。

    样例: <jwc>/SSO/login.aspx?targetUrl={base64}<base64(target)>
    其中 "{base64}" 是字面 7 字符,不是 URL 模板。
    """
    b64 = base64.b64encode(target_url.encode("utf-8")).decode("ascii")
    return f"{jwc_base}/SSO/login.aspx?targetUrl=" + "{base64}" + b64


def _extract_error_message(html_text: str) -> Optional[str]:
    try:
        tree = lxml_html.fromstring(html_text)
    except Exception:
        return None
    for xp in (
        '//*[@id="errorMsg"]//text()',
        '//*[contains(@class, "errors")]//text()',
        '//*[contains(@class, "alert-danger")]//text()',
        '//*[contains(@class, "error")]//text()',
    ):
        text = " ".join(s.strip() for s in tree.xpath(xp) if s.strip())
        if text:
            return text[:200]
    return None


def login(
    config: JxnuConfig,
    target_path: str = "/Portal/Index.aspx",
    session: Optional[requests.Session] = None,
) -> CasLoginResult:
    """走完整 CAS 登录流程,返回带身份的 requests.Session。"""
    if session is None:
        session = requests.Session()
        # 默认忽略 HTTP_PROXY / HTTPS_PROXY 环境变量:校内教务系统访问
        # 通常不应走系统代理。要走代理请显式传入已配置 proxies 的 Session。
        session.trust_env = False
    session.headers.update({
        "User-Agent": config.user_agent,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    target_url = f"{config.jwc_base}{target_path}"

    logger.info("[1/5] 获取 CAS RSA 公钥")
    public_key_pem = fetch_public_key(session, config.cas_base)
    encrypted_password = encrypt_password(config.password, public_key_pem)

    sso_url = _build_jwc_sso_url(config.jwc_base, target_url)
    logger.info("[2/5] GET %s", sso_url)
    resp = session.get(sso_url, allow_redirects=True, timeout=15)
    logger.debug("    -> %s (%d, %d bytes)", resp.url, resp.status_code, len(resp.text))
    if "/cas/login" not in resp.url:
        raise CasLoginError(f"未跳转到 CAS 登录页,当前 URL: {resp.url}")
    cas_login_url = resp.url
    login_page_html = resp.text

    logger.info("[3/5] 解析登录页表单字段")
    fields = _extract_password_form_fields(login_page_html)
    if "execution" not in fields:
        raise CasLoginError("登录页结构变化:fm1 中找不到 execution 字段")
    logger.debug("    fields: %s", sorted(fields.keys()))

    fields["username"] = config.username
    fields["password"] = encrypted_password
    fields.setdefault("_eventId", "submit")
    # geolocation / fpVisitorId 留空即可

    post_url = urljoin(cas_login_url, "login")
    logger.info("[4/5] POST %s", post_url)
    resp = session.post(post_url, data=fields, allow_redirects=False, timeout=15)
    logger.debug("    -> HTTP %d, Location=%s", resp.status_code, resp.headers.get("Location"))

    if resp.status_code != 302:
        msg = _extract_error_message(resp.text) or "(无错误提示)"
        raise CasLoginError(
            f"CAS 登录未跳转 (HTTP {resp.status_code}): {msg}\n"
            "常见原因: 账号/密码错误、需要验证码(失败累计 >=5 次后触发)、"
            "账号被锁定。可在浏览器登录一次确认状态。"
        )

    ticket_url = resp.headers.get("Location", "")
    if "ticket=" not in ticket_url:
        raise CasLoginError(
            f"CAS 未返回 ticket(可能账号密码错误): Location={ticket_url}"
        )

    logger.info("[5/5] 携带 ticket 回调 JWC")
    resp = session.get(ticket_url, allow_redirects=True, timeout=15)
    resp.raise_for_status()
    logger.debug("    -> %s (%d bytes)", resp.url, len(resp.text))

    if ('../SSO/login.aspx' in resp.text
            and '请选择以下方法登录' in resp.text):
        raise CasLoginError(
            "ticket 已发放但 JWC 仍显示登录页,可能 ASP.NET_SessionId "
            "未正确建立或 ticket 校验失败"
        )

    logger.info("✓ 登录成功 -> %s", resp.url)
    return CasLoginResult(
        session=session,
        portal_url=resp.url,
        portal_html=resp.text,
    )
