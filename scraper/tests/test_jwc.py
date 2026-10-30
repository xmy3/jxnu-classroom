import pytest

from jxnu_classroom.jwc import make_session


def test_session_ignores_implicit_system_proxy(monkeypatch):
    monkeypatch.delenv("JWC_HTTPS_PROXY", raising=False)
    monkeypatch.setenv("HTTPS_PROXY", "http://unrelated.invalid:8080")
    with make_session() as session:
        assert session.trust_env is False
        assert session.proxies == {}
        assert session.verify is True


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_session_uses_explicit_proxy_without_disabling_tls(monkeypatch, scheme):
    proxy = f"{scheme}://proxy.example.com:8080"
    monkeypatch.setenv("JWC_HTTPS_PROXY", proxy)
    with make_session() as session:
        assert session.proxies == {"https": proxy}
        assert session.verify is True


@pytest.mark.parametrize("proxy", ["socks5://proxy.example.com:1080", "http://", "invalid"])
def test_session_rejects_unsupported_proxy(monkeypatch, proxy):
    monkeypatch.setenv("JWC_HTTPS_PROXY", proxy)
    with pytest.raises(ValueError, match="must be an HTTP or HTTPS proxy URL"):
        make_session()
