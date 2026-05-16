"""离线 smoke test:不需要账号,只验证可以独立测的环节。

跑法: python tests/smoke_offline.py
"""
import sys
from pathlib import Path

import requests

from jxnu_classroom.cas import (
    encrypt_password,
    fetch_public_key,
    _extract_password_form_fields,
    _build_jwc_sso_url,
)
from jxnu_classroom.config import JxnuConfig


def main() -> int:
    print("== Smoke 1: import & __version__ ==")
    import jxnu_classroom
    print(f"  jxnu_classroom v{jxnu_classroom.__version__}")

    print("\n== Smoke 2: fetch_public_key (live) ==")
    s = requests.Session()
    s.trust_env = False  # 忽略系统代理
    s.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    pem = fetch_public_key(s, "https://uis.jxnu.edu.cn/cas")
    assert pem.startswith(b"-----BEGIN PUBLIC KEY-----"), "PEM 头不对"
    assert pem.endswith(b"-----END PUBLIC KEY-----"), "PEM 尾不对"
    print(f"  公钥长度 {len(pem)} bytes,前 40 字节: {pem[:40].decode()}...")

    print("\n== Smoke 3: encrypt_password ==")
    ciphertext = encrypt_password("hello-world-123", pem)
    assert ciphertext.startswith("__RSA__"), "缺少 __RSA__ 前缀"
    # base64 部分长度应该是 ceil(256/3)*4 = 344 字符(2048-bit 公钥 → 256 字节密文)
    b64 = ciphertext[len("__RSA__"):]
    print(f"  密文格式 OK,base64 长度 {len(b64)}")

    print("\n== Smoke 4: _extract_password_form_fields ==")
    fixture = Path(__file__).resolve().parent.parent.parent / ".research" / "cas_login.html"
    if not fixture.exists():
        print(f"  跳过(未找到 fixture {fixture})")
    else:
        html_text = fixture.read_text(encoding="utf-8")
        fields = _extract_password_form_fields(html_text)
        expected = {"username", "password", "execution", "_eventId", "currentMenu"}
        missing = expected - fields.keys()
        assert not missing, f"缺字段: {missing}"
        print(f"  抽到字段: {sorted(fields.keys())}")
        print(f"  execution={fields['execution']!r}  _eventId={fields['_eventId']!r}")

    print("\n== Smoke 5: _build_jwc_sso_url 格式 ==")
    url = _build_jwc_sso_url("https://jwc.jxnu.edu.cn", "https://jwc.jxnu.edu.cn/Portal/Index.aspx")
    assert "{base64}" in url, "缺少 {base64} 字面前缀"
    print(f"  {url}")

    print("\n== Smoke 6: JxnuConfig 默认值 ==")
    cfg = JxnuConfig(username="x", password="y")
    print(f"  cas_base={cfg.cas_base}")
    print(f"  jwc_base={cfg.jwc_base}")

    print("\n[OK] 所有离线 smoke 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
